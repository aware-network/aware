from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from aware_workspace_runtime.semantic_package_composition import (
    CONTENT_ADDRESSED_AUTHORITY_REF_SCHEMA,
    WORKSPACE_OPERATION_AUTHORITY_INPUT_ROLE,
    WorkspaceCapturedSemanticInput,
    WorkspaceParentOperationAuthorityRef,
    WorkspaceSemanticPackageCompositionAuthority,
    WorkspaceSemanticPackageCompositionError,
    WorkspaceSemanticPackageInputAuthority,
    WorkspaceSemanticPackageManifestAuthority,
    WorkspaceSemanticPackagePriorAuthority,
    WorkspaceSemanticPriorAuthority,
    WorkspaceSemanticPriorAuthorityRef,
    WorkspaceSemanticProviderSelectionAuthority,
    WorkspaceSemanticRendererInputAuthority,
    WorkspaceSemanticSourceMovement,
)
from aware_workspace_runtime.semantic_package_result_catalog import (
    WorkspaceSemanticResultCatalogRoot,
)

FIXTURE = (
    Path(__file__).parents[1] / "contracts/semantic_package_composition/v2/"
    "storage-content-target-genesis-input-authority.json"
)


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _canonical_digest(value: object) -> str:
    body = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _captured(
    package: str,
    relative_path: str,
    *,
    input_kind: str = "aware_source",
) -> WorkspaceCapturedSemanticInput:
    body = f"{package}:{relative_path}:body"
    return WorkspaceCapturedSemanticInput(
        input_kind=input_kind,
        relative_path=relative_path,
        body_ref=f"cas://workspace-source/{_digest(body)[7:]}.body",
        body_digest=_digest(body),
        size_bytes=len(body.encode()),
    )


def _package(
    name: str,
    *,
    dependencies: tuple[str, ...] = (),
    sources: tuple[str, ...] = ("entity.aware",),
    owned_roots: tuple[str, ...] | None = None,
) -> WorkspaceSemanticPackageInputAuthority:
    package_ref = f"package:{name}@1.0.0"
    root = f"workspaces/{name}/ontology/structure"
    return WorkspaceSemanticPackageInputAuthority(
        package_ref=package_ref,
        package_name=name,
        package_kind="ontology",
        fqn_prefix=f"aware.{name}",
        semantic_version="1.0.0",
        package_root=root,
        sources_root=f"{root}/aware",
        owned_semantic_root_refs=(
            owned_roots if owned_roots is not None else (f"aware.{name}.Root",)
        ),
        manifest=WorkspaceSemanticPackageManifestAuthority(
            relative_path=f"{root}/aware.toml",
            ref=f"cas://workspace-package/{_digest(name + ':manifest')[7:]}.json",
            digest=_digest(name + ":manifest"),
            size_bytes=512,
        ),
        declared_source_relative_paths=tuple(
            f"{root}/aware/{source}" for source in sources
        ),
        direct_dependency_package_refs=dependencies,
    )


def _prior(
    packages: tuple[WorkspaceSemanticPackageInputAuthority, ...],
) -> WorkspaceSemanticPriorAuthority:
    priors: list[WorkspaceSemanticPackagePriorAuthority] = []
    for package in packages:
        priors.append(
            WorkspaceSemanticPackagePriorAuthority(
                package_ref=package.package_ref,
                prior_kind="exact_refs",
                base_authority_ref=_digest(package.package_ref + ":membership"),
                refs=(
                    WorkspaceSemanticPriorAuthorityRef(
                        package_ref=package.package_ref,
                        role="package",
                        ref=package.manifest.ref,
                        digest=package.manifest.digest,
                        size_bytes=package.manifest.size_bytes,
                    ),
                    WorkspaceSemanticPriorAuthorityRef(
                        package_ref=package.package_ref,
                        role="schema",
                        ref=f"cas://meta-type-schema/{package.package_name}.json",
                        digest=_digest(package.package_name + ":schema"),
                        size_bytes=1024,
                    ),
                    WorkspaceSemanticPriorAuthorityRef(
                        package_ref=package.package_ref,
                        role="object_abi",
                        ref=f"cas://ontology-object-abi/{package.package_name}.json",
                        digest=_digest(package.package_name + ":abi"),
                        size_bytes=2048,
                    ),
                ),
            )
        )
    return WorkspaceSemanticPriorAuthority(package_priors=tuple(priors))


def _catalog() -> WorkspaceSemanticResultCatalogRoot:
    return WorkspaceSemanticResultCatalogRoot.typed_empty()[0]


def _movement(
    package: WorkspaceSemanticPackageInputAuthority,
    relative_path: str,
    *,
    change_kind: str = "update",
) -> WorkspaceSemanticSourceMovement:
    full_path = f"{package.sources_root}/{relative_path}"
    if change_kind == "delete":
        return WorkspaceSemanticSourceMovement(
            package_ref=package.package_ref,
            input_kind="aware_source",
            relative_path=full_path,
            change_kind="delete",
            before_digest=_digest("before:" + full_path),
        )
    return WorkspaceSemanticSourceMovement(
        package_ref=package.package_ref,
        input_kind="aware_source",
        relative_path=full_path,
        change_kind=change_kind,
        before_digest=(
            _digest("before:" + full_path) if change_kind == "update" else None
        ),
        after_body=_captured(package.package_name, full_path),
    )


def _parent(marker: str = "1") -> WorkspaceParentOperationAuthorityRef:
    if len(marker) != 1 or marker not in "0123456789abcdef":
        raise ValueError("parent marker must be one lowercase hexadecimal digit")
    identity = {
        "schema": CONTENT_ADDRESSED_AUTHORITY_REF_SCHEMA,
        "input_name": "workspace-operation:operation-fixture-001",
        "input_role": WORKSPACE_OPERATION_AUTHORITY_INPUT_ROLE,
        "ref_kind": "workspace_operation_authority_ref",
        "ref": "cas://workspace-operation-authority/" + marker * 64 + ".json",
        "digest": "sha256:" + marker * 64,
        "size": 4096,
    }
    return WorkspaceParentOperationAuthorityRef(
        **identity,
        authority_digest=_canonical_digest(identity),
    )


def _authority(
    *,
    workflow_roots: tuple[str, ...] = ("aware.workflow.Root",),
    requested_roots: tuple[str, ...] = ("aware.workflow.Root",),
    source_movements: bool = True,
) -> WorkspaceSemanticPackageCompositionAuthority:
    storage = _package("storage", sources=("blob.aware",))
    content = _package(
        "content",
        dependencies=(storage.package_ref,),
        sources=("content.aware",),
    )
    workflow = _package(
        "workflow",
        dependencies=(content.package_ref, storage.package_ref),
        sources=("issue.aware", "workflow.aware"),
        owned_roots=workflow_roots,
    )
    packages = (workflow, storage, content)
    return WorkspaceSemanticPackageCompositionAuthority.create(
        parent_operation=_parent(),
        target_package_ref=workflow.package_ref,
        packages=packages,
        source_movements=(
            (_movement(workflow, "issue.aware"),) if source_movements else ()
        ),
        requested_semantic_root_refs=requested_roots,
        provider=WorkspaceSemanticProviderSelectionAuthority(
            capability_key="ontology.semantic-package-projection",
            semantic_version="1.0.0",
            contract_schema_digest=_digest("provider-contract"),
            selection_binding_ref="local-provider:ontology-runtime",
            selection_binding_fingerprint=_digest("provider-binding"),
        ),
        accepted_result_catalog=_catalog(),
        prior_authority=_prior(packages),
        renderer=WorkspaceSemanticRendererInputAuthority(
            renderer_profile_ref="python:ontology-object-facade:v1",
            renderer_configuration_ref="cas://renderer-config/python-v1.json",
            renderer_configuration_digest=_digest("renderer-config"),
            allowed_output_namespace="aware_workflow_ontology_object",
        ),
    )


def test_fixture_is_exact_and_strictly_round_trips() -> None:
    authority = _authority()

    assert authority.to_json_bytes() == FIXTURE.read_bytes().rstrip(b"\n")
    assert (
        WorkspaceSemanticPackageCompositionAuthority.from_json_bytes(
            authority.to_json_bytes()
        )
        == authority
    )


def test_reordered_equivalent_inputs_normalize_to_one_authority() -> None:
    authority = _authority()

    reordered = WorkspaceSemanticPackageCompositionAuthority.create(
        parent_operation=authority.parent_operation,
        target_package_ref=authority.target_package_ref,
        packages=tuple(reversed(authority.packages)),
        source_movements=tuple(reversed(authority.source_movements)),
        requested_semantic_root_refs=tuple(
            reversed(authority.requested_semantic_root_refs)
        ),
        provider=authority.provider,
        accepted_result_catalog=authority.accepted_result_catalog,
        prior_authority=WorkspaceSemanticPriorAuthority(
            package_priors=tuple(reversed(authority.prior_authority.package_priors)),
        ),
        renderer=authority.renderer,
    )

    assert reordered.to_json_bytes() == authority.to_json_bytes()
    assert reordered.authority_digest == authority.authority_digest


def test_parent_is_the_exact_existing_workspace_operation_ref() -> None:
    parent = _parent()
    assert parent.to_dict() == {
        **parent.identity_payload(),
        "authority_digest": parent.authority_digest,
    }

    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="authority digest mismatched",
    ):
        replace(parent, digest="sha256:" + "2" * 64)
    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="input_role is unsupported",
    ):
        replace(parent, input_role="source")


def test_parse_input_view_contains_each_aware_body_once_and_no_manifest() -> None:
    authority = _authority()
    inputs = authority.aware_parse_inputs()
    expected = tuple(
        (movement.package_ref, movement.relative_path)
        for movement in authority.source_movements
        if movement.change_kind in {"create", "update"}
        and movement.input_kind == "aware_source"
    )

    assert (
        tuple((item.package_ref, item.source.relative_path) for item in inputs)
        == expected
    )
    assert all(item.source.input_kind == "aware_source" for item in inputs)
    assert all(item.source.relative_path.endswith(".aware") for item in inputs)
    assert authority.aware_parse_input_digest.startswith("sha256:")
    assert authority.source_lifecycle == "source_delta"
    assert authority.requires_source_semantic_work


def _recompose(
    authority: WorkspaceSemanticPackageCompositionAuthority,
    *,
    parent_operation: WorkspaceParentOperationAuthorityRef | None = None,
    packages: tuple[WorkspaceSemanticPackageInputAuthority, ...] | None = None,
    requested_roots: tuple[str, ...] | None = None,
    provider: WorkspaceSemanticProviderSelectionAuthority | None = None,
    prior_authority: WorkspaceSemanticPriorAuthority | None = None,
    renderer: WorkspaceSemanticRendererInputAuthority | None = None,
) -> WorkspaceSemanticPackageCompositionAuthority:
    return WorkspaceSemanticPackageCompositionAuthority.create(
        parent_operation=parent_operation or authority.parent_operation,
        target_package_ref=authority.target_package_ref,
        packages=packages or authority.packages,
        source_movements=authority.source_movements,
        requested_semantic_root_refs=(
            requested_roots or authority.requested_semantic_root_refs
        ),
        provider=provider or authority.provider,
        accepted_result_catalog=authority.accepted_result_catalog,
        prior_authority=prior_authority or authority.prior_authority,
        renderer=renderer or authority.renderer,
    )


def test_source_current_never_claims_overall_command_currentness() -> None:
    authority = _authority(source_movements=False)

    assert authority.source_lifecycle == "source_current"
    assert not authority.requires_source_semantic_work
    assert authority.aware_parse_inputs() == ()
    assert not hasattr(authority, "lifecycle")
    assert not hasattr(authority, "requires_semantic_work")


def test_non_source_authority_movements_change_composition_without_source_work() -> (
    None
):
    authority = _authority(source_movements=False)
    artifact = WorkspaceSemanticPriorAuthorityRef(
        package_ref=authority.target_package_ref,
        role="artifact",
        ref="cas://code-package/workflow-python-v1.json",
        digest=_digest("workflow-artifact-v1"),
        size_bytes=4096,
    )
    with_artifact = _recompose(
        authority,
        prior_authority=WorkspaceSemanticPriorAuthority(
            package_priors=tuple(
                replace(item, refs=(*item.refs, artifact))
                if item.package_ref == authority.target_package_ref
                else item
                for item in authority.prior_authority.package_priors
            ),
        ),
    )
    movements = (
        _recompose(
            authority,
            renderer=replace(
                authority.renderer,
                renderer_configuration_digest=_digest("renderer-config-v2"),
            ),
        ),
        _recompose(
            authority,
            provider=replace(
                authority.provider,
                selection_binding_fingerprint=_digest("provider-binding-v2"),
            ),
        ),
        _recompose(authority, parent_operation=_parent("2")),
        with_artifact,
    )

    for moved in movements:
        assert moved.source_lifecycle == "source_current"
        assert not moved.requires_source_semantic_work
        assert moved.aware_parse_inputs() == ()
        assert moved.authority_digest != authority.authority_digest


def test_requested_root_movement_changes_composition_without_source_work() -> None:
    roots = ("aware.workflow.Root", "aware.workflow.Alternate")
    authority = _authority(
        workflow_roots=roots,
        source_movements=False,
    )
    moved = _recompose(
        authority,
        requested_roots=("aware.workflow.Alternate",),
    )

    assert authority.source_lifecycle == moved.source_lifecycle == "source_current"
    assert authority.aware_parse_inputs() == moved.aware_parse_inputs() == ()
    assert authority.authority_digest != moved.authority_digest


def test_dependency_graph_must_be_complete_and_acyclic() -> None:
    authority = _authority()
    workflow = next(
        package
        for package in authority.packages
        if package.package_ref == authority.target_package_ref
    )

    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="absent from composition",
    ):
        WorkspaceSemanticPackageCompositionAuthority.create(
            parent_operation=authority.parent_operation,
            target_package_ref=workflow.package_ref,
            packages=(workflow,),
            source_movements=authority.source_movements,
            requested_semantic_root_refs=authority.requested_semantic_root_refs,
            provider=authority.provider,
            accepted_result_catalog=authority.accepted_result_catalog,
            prior_authority=authority.prior_authority,
            renderer=authority.renderer,
        )

    disconnected = _package("disconnected")
    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="must equal the target dependency closure",
    ):
        WorkspaceSemanticPackageCompositionAuthority.create(
            parent_operation=authority.parent_operation,
            target_package_ref=authority.target_package_ref,
            packages=(*authority.packages, disconnected),
            source_movements=authority.source_movements,
            requested_semantic_root_refs=authority.requested_semantic_root_refs,
            provider=authority.provider,
            accepted_result_catalog=authority.accepted_result_catalog,
            prior_authority=authority.prior_authority,
            renderer=authority.renderer,
        )

    storage = next(
        package for package in authority.packages if package.package_name == "storage"
    )
    cyclic_storage = replace(
        storage,
        direct_dependency_package_refs=(workflow.package_ref,),
    )
    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="contains a cycle",
    ):
        WorkspaceSemanticPackageCompositionAuthority.create(
            parent_operation=authority.parent_operation,
            target_package_ref=workflow.package_ref,
            packages=tuple(
                cyclic_storage if item == storage else item
                for item in authority.packages
            ),
            source_movements=authority.source_movements,
            requested_semantic_root_refs=authority.requested_semantic_root_refs,
            provider=authority.provider,
            accepted_result_catalog=authority.accepted_result_catalog,
            prior_authority=authority.prior_authority,
            renderer=authority.renderer,
        )


def test_prior_authority_is_typed_empty_or_exact_refs() -> None:
    typed_empty = WorkspaceSemanticPackagePriorAuthority(
        package_ref="package:target@1.0.0",
        prior_kind="typed_empty",
        base_authority_ref=_digest("target:nonmembership"),
    )
    assert typed_empty.refs == ()
    with pytest.raises(WorkspaceSemanticPackageCompositionError):
        WorkspaceSemanticPackagePriorAuthority(
            package_ref="package:target@1.0.0",
            prior_kind="typed_empty",
            base_authority_ref=_digest("target:nonmembership"),
            refs=_authority().prior_authority.package_priors[0].refs,
        )
    with pytest.raises(WorkspaceSemanticPackageCompositionError):
        WorkspaceSemanticPackagePriorAuthority(
            package_ref="package:target@1.0.0",
            prior_kind="exact_refs",
            base_authority_ref=_digest("target:membership"),
        )

    authority = _authority()
    package_ref = authority.packages[0].package_ref
    substituted_priors = tuple(
        replace(
            package_prior,
            refs=tuple(
                replace(
                    ref,
                    ref="cas://workspace-package/substituted.json",
                    digest=_digest("substituted-package-authority"),
                )
                if ref.role == "package"
                else ref
                for ref in package_prior.refs
            ),
        )
        if package_prior.package_ref == package_ref
        else package_prior
        for package_prior in authority.prior_authority.package_priors
    )
    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="mismatched prior fragment",
    ):
        replace(
            authority,
            prior_authority=WorkspaceSemanticPriorAuthority(
                package_priors=substituted_priors,
            ),
        )


def test_source_coordinates_and_root_ownership_fail_closed() -> None:
    package = _package("workflow")
    source = _captured(
        "workflow",
        "workspaces/workflow/ontology/structure/aware/entity.aware",
    )
    shared_body = replace(
        source,
        relative_path="workspaces/workflow/ontology/structure/aware/second.aware",
    )
    assert source.body_ref == shared_body.body_ref

    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="must end in .aware",
    ):
        replace(source, relative_path="outside/not-aware.txt")

    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="contained beneath sources_root",
    ):
        replace(
            package,
            declared_source_relative_paths=("outside/source.aware",),
        )

    authority = _authority()
    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="not owned by the target package",
    ):
        WorkspaceSemanticPackageCompositionAuthority.create(
            parent_operation=authority.parent_operation,
            target_package_ref=authority.target_package_ref,
            packages=authority.packages,
            source_movements=authority.source_movements,
            requested_semantic_root_refs=("aware.content.Root",),
            provider=authority.provider,
            accepted_result_catalog=authority.accepted_result_catalog,
            prior_authority=authority.prior_authority,
            renderer=authority.renderer,
        )


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "operation_id",
        "idempotency_key",
        "source_authority",
        "result_schema_digest",
        "resulting_abi_root_ref",
        "renderer_target_impacts",
        "code_package_delta",
    ],
)
def test_strict_decode_rejects_operation_and_derived_result_fields(
    forbidden_field: str,
) -> None:
    payload = _authority().to_dict()
    payload[forbidden_field] = "forbidden"

    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="fields are incomplete or unknown",
    ):
        WorkspaceSemanticPackageCompositionAuthority.from_dict(payload)


def test_strict_decode_rejects_nested_unknown_and_digest_substitution() -> None:
    payload = _authority().to_dict()
    renderer = dict(payload["renderer"])
    renderer["output_ref"] = "forbidden"
    payload["renderer"] = renderer
    with pytest.raises(WorkspaceSemanticPackageCompositionError):
        WorkspaceSemanticPackageCompositionAuthority.from_dict(payload)

    payload = _authority().to_dict()
    payload["authority_digest"] = "sha256:" + "0" * 64
    with pytest.raises(
        WorkspaceSemanticPackageCompositionError,
        match="authority digest mismatched",
    ):
        WorkspaceSemanticPackageCompositionAuthority.from_dict(payload)
