from __future__ import annotations

from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticMaterializationIntent,
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticDependencyTargetConstraint,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from aware_workspace_runtime import (
    AdmittedWorkspaceSemanticMaterializationMembershipCatalog,
    WorkspaceMaterializationRootSelector,
    WorkspaceSemanticAuthoredDependency,
    WorkspaceSemanticMaterializationMembershipCatalog,
    WorkspaceSemanticMaterializationMembershipResolver,
    WorkspaceSemanticMaterializationPackageEntry,
    WorkspaceSemanticMaterializationParticipationPolicy,
)
from aware_workspace_runtime.materialization_membership_catalog import (
    _issue_workspace_semantic_materialization_membership_catalog,
    _revoke_workspace_semantic_materialization_membership_catalog,
)


def _membership_admission(
    catalog: WorkspaceSemanticMaterializationMembershipCatalog,
):
    return _issue_workspace_semantic_materialization_membership_catalog(
        catalog=catalog,
        host_liveness=lambda: True,
    )


def _digest(value: str) -> ContentDigest:
    return ContentDigest.of_bytes(value.encode())


def _constraint(kind: str, value: str) -> SemanticDependencyTargetConstraint:
    return SemanticDependencyTargetConstraint.create(
        constraint_kind=kind, constraint_value=value
    )


def _entry(
    package_ref: str,
    *,
    kind: str,
    family: str,
    module: str,
    root: str,
    dependency: WorkspaceSemanticAuthoredDependency | None = None,
) -> WorkspaceSemanticMaterializationPackageEntry:
    package = SemanticPackageCoordinate(
        package_ref=package_ref,
        package_kind=kind,
        manifest_digest=_digest(f"manifest:{package_ref}"),
    )
    policy = WorkspaceSemanticMaterializationParticipationPolicy.create(
        policy_ref=f"policy:{package_ref}",
        policy_revision=1,
        package_ref=package_ref,
        allowed_operation_kinds=("materialize",),
        allowed_semantic_root_refs=(root,),
        allowed_terminal_output_roles=("python",),
        allow_unconfigured=True,
        allowed_semantic_configuration_coordinates=(),
    )
    return WorkspaceSemanticMaterializationPackageEntry.create(
        repository_ref="aware",
        workspace_ref="aware_kernel",
        module_ref=module,
        package=package,
        package_family=family,
        package_role=kind,
        manifest_contract=SemanticContractRef(
            key=f"aware.{kind}.manifest",
            version="1",
            schema_digest=_digest(f"manifest-contract:{kind}"),
        ),
        manifest_relative_path=f"{module}/{kind}.aware",
        source_authority_ref=f"workspace-source:{package_ref}",
        source_authority_digest=_digest(f"source:{package_ref}"),
        owned_semantic_root_refs=(root,),
        authored_dependencies=() if dependency is None else (dependency,),
        participation_policy=policy,
        allowed_profile_refs=(f"{kind}.materialization",),
    )


def _catalog() -> WorkspaceSemanticMaterializationMembershipCatalog:
    dependency = WorkspaceSemanticAuthoredDependency.create(
        dependency_kind="api_package",
        dependency_ref="sdk.api",
        admitted_target_package_refs=("package:api",),
        allowed_target_constraints=tuple(
            sorted(
                (
                    _constraint("package_kind", "api"),
                    _constraint("semantic_provider_key", "aware.api"),
                ),
                key=lambda item: canonical_json_bytes(item.to_wire()),
            )
        ),
    )
    entries = tuple(
        sorted(
            (
                _entry(
                    "package:api",
                    kind="api",
                    family="public",
                    module="api",
                    root="api.public",
                ),
                _entry(
                    "package:sdk",
                    kind="sdk",
                    family="public",
                    module="sdk",
                    root="sdk.public",
                    dependency=dependency,
                ),
            ),
            key=lambda item: item.package.package_ref.encode(),
        )
    )
    return WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.production", catalog_generation=3, entries=entries
    )


def test_membership_admission_is_private_and_revocation_invalidates_resolver() -> None:
    import aware_workspace_runtime as public_runtime

    assert not hasattr(public_runtime, "WorkspaceSemanticMaterializationMembershipHost")
    assert not hasattr(
        public_runtime, "WorkspaceSemanticMaterializationMembershipSource"
    )
    assert not hasattr(
        public_runtime,
        "admit_workspace_semantic_materialization_membership_catalog",
    )

    admission = _membership_admission(_catalog())
    resolver = WorkspaceSemanticMaterializationMembershipResolver(admission)
    _revoke_workspace_semantic_materialization_membership_catalog(admission)
    with pytest.raises(ContractViolation, match="not live"):
        _ = resolver.catalog
    with pytest.raises(ContractViolation, match="not live"):
        resolver.package_if_present("package:api")


def test_catalog_derives_source_identity_and_selector_indexes() -> None:
    catalog = _catalog()
    resolver = WorkspaceSemanticMaterializationMembershipResolver(
        _membership_admission(catalog)
    )
    api = resolver.package("package:api")
    assert resolver.package_if_present("package:api") is api
    assert resolver.package_if_present("package:declaration-only") is None
    assert api.source_identity_digest != api.source_authority_digest
    assert tuple(
        item.package.package_ref
        for item in resolver.expand_selector(
            WorkspaceMaterializationRootSelector.create(
                selector_kind="workspace", selector_ref="aware_kernel"
            )
        )
    ) == ("package:api", "package:sdk")
    with pytest.raises(ContractViolation, match="07F-F"):
        resolver.expand_selector(
            WorkspaceMaterializationRootSelector.create(
                selector_kind="repository", selector_ref="aware"
            )
        )


def test_workspace_filters_without_interpreting_provider_constraint() -> None:
    resolver = WorkspaceSemanticMaterializationMembershipResolver(
        _membership_admission(_catalog())
    )
    result = resolver.candidates(
        admitted_package_refs=("package:api",),
        constraints=(
            _constraint("package_kind", "api"),
            _constraint("semantic_provider_key", "unknown.to.workspace"),
        ),
    )
    assert tuple(item.package.package_ref for item in result) == ("package:api",)


def test_membership_admission_is_host_issued_and_forgery_fails() -> None:
    forged = object.__new__(AdmittedWorkspaceSemanticMaterializationMembershipCatalog)
    with pytest.raises(ContractViolation, match="not registered"):
        WorkspaceSemanticMaterializationMembershipResolver(forged)


def test_membership_admission_and_resolver_observation_detach_source_graph() -> None:
    source = _catalog()
    resolver = WorkspaceSemanticMaterializationMembershipResolver(
        _membership_admission(source)
    )
    replacement = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref=source.catalog_ref,
        catalog_generation=source.catalog_generation + 1,
        entries=source.entries,
    )

    object.__setattr__(source, "catalog_generation", replacement.catalog_generation)
    object.__setattr__(source, "catalog_root_digest", replacement.catalog_root_digest)
    assert resolver.catalog.catalog_generation == 3

    exposed = resolver.catalog
    object.__setattr__(exposed, "catalog_generation", replacement.catalog_generation)
    object.__setattr__(exposed, "catalog_root_digest", replacement.catalog_root_digest)
    assert resolver.catalog.catalog_generation == 3


def test_entry_rejects_policy_mismatch_and_source_restamp() -> None:
    entry = _catalog().entries[0]
    with pytest.raises(ContractViolation, match="source identity"):
        replace(entry, source_identity_digest=_digest("forged"))

    wrong = WorkspaceSemanticMaterializationParticipationPolicy.create(
        policy_ref="wrong",
        policy_revision=1,
        package_ref="package:wrong",
        allowed_operation_kinds=("materialize",),
        allowed_semantic_root_refs=("api.public",),
        allowed_terminal_output_roles=("python",),
        allow_unconfigured=True,
        allowed_semantic_configuration_coordinates=(),
    )
    values = {
        name: getattr(entry, name)
        for name in entry.__dataclass_fields__
        if name
        not in {"source_identity_digest", "entry_digest", "participation_policy"}
    }
    with pytest.raises(ContractViolation, match="policy package"):
        WorkspaceSemanticMaterializationPackageEntry.create(
            **values, participation_policy=wrong
        )


def test_policy_admits_exact_package_intent() -> None:
    entry = _catalog().entries[0]
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=("api.public",),
        requested_terminal_output_roles=("python",),
        semantic_configuration_coordinate=None,
    )
    assert entry.participation_policy.admits(intent)
