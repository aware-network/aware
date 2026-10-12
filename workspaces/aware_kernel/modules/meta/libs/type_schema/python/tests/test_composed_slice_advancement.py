from __future__ import annotations

import hashlib
import importlib.util
import os
import statistics
import subprocess
import time
from dataclasses import replace
from pathlib import Path

import pytest
from aware_meta_type_schema.composed_slice_advancement import (
    AdmittedTypeSchemaComposedSlice,
    TypeSchemaComposedSliceAdvancementError,
    admit_composed_slice,
    advance_attribution_only_composed_slice,
)
from aware_meta_type_schema.composition import (
    TypeOwnerBinding,
    TypeSchemaPackageRoot,
    resolve_composed_slice,
)
from aware_meta_type_schema.composition_codec import (
    decode_catalog_root,
    decode_composed_slice,
    decode_package_root,
    decode_source_attribution_fragment,
    encode_composition_value,
)
from aware_meta_type_schema.composition_transition import (
    DefinitionFragmentMovement,
    PackageRootMovement,
    SourceAttributionFragmentMovement,
    TypeOwnerBindingMovement,
    create_typed_empty_catalog,
    create_typed_empty_package,
    transition_catalog,
    transition_package,
)
from aware_meta_type_schema.definition_fragment import (
    SourceDefinitionBinding,
    TypeDefinitionFragment,
    TypeSchemaSourceAttributionFragment,
)
from aware_meta_type_schema.model import (
    FieldDefinition,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    ValueShape,
)
from aware_meta_type_schema.persistent_index import (
    PersistentBodyAuthority,
    persistent_body_coordinate_from_wire,
)
from aware_meta_type_schema.positive_reader import (
    PositiveBodyRead,
    TypeSchemaPositiveReaderCapability,
)


class _Store:
    def __init__(self) -> None:
        self.values: dict[str, PersistentBodyAuthority] = {}
        self.calls = 0

    def ingest(self, values: tuple[PersistentBodyAuthority, ...]) -> None:
        self.values.update((value.coordinate.body_ref, value) for value in values)

    def reader(self) -> TypeSchemaPositiveReaderCapability:
        def read(expected):
            self.calls += 1
            body = self.values[expected.body_ref]
            return PositiveBodyRead(
                body.coordinate.body_ref,
                body.coordinate.body_digest,
                body.coordinate.size_bytes,
                body.coordinate.schema,
                body.canonical_bytes,
            )

        return TypeSchemaPositiveReaderCapability(
            request_ref="request:advancement",
            read_body=read,
        )


def _fragment(type_ref: str, references: tuple[str, ...]) -> TypeDefinitionFragment:
    if references:
        definition = TypeDefinition(
            type_ref=type_ref,
            name=type_ref.rsplit(".", 1)[-1],
            kind=TypeKind.GRAPH_OBJECT,
            fields=tuple(
                FieldDefinition(
                    field_ref=f"{type_ref}.field{index}",
                    name=f"field{index}",
                    shape=ValueShape.named(reference),
                )
                for index, reference in enumerate(references)
            ),
        )
    else:
        definition = TypeDefinition(
            type_ref=type_ref,
            name=type_ref.rsplit(".", 1)[-1],
            kind=TypeKind.SCALAR_ALIAS,
            scalar_target=ScalarKind.STRING,
        )
    return TypeDefinitionFragment.create(definition)


def _package(
    store: _Store,
    *,
    package_ref: str,
    dependencies: tuple[str, ...],
    fragment: TypeDefinitionFragment,
):
    name = package_ref.split(":", 1)[1].split("@", 1)[0]
    empty, bodies = create_typed_empty_package(
        package_ref=package_ref,
        package_name=name,
        namespace=name,
        semantic_version="1.0.0",
        dependency_package_refs=dependencies,
    )
    store.ingest(bodies)
    attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref=package_ref,
        source_path=f"{name}/{name}.aware",
        document_coordinate_ref=f"coordinate:{name}:v1",
        bindings=(
            SourceDefinitionBinding(fragment.type_ref, fragment.to_body().coordinate),
        ),
    )
    transition = transition_package(
        empty,
        definition_movements=(
            DefinitionFragmentMovement(fragment.type_ref, None, fragment),
        ),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                attribution.source_path,
                None,
                attribution,
            ),
        ),
        reader=store.reader(),
        request_ref="request:advancement",
    )
    store.ingest(transition.emitted_bodies)
    return transition, attribution


def _world():
    store = _Store()
    content_fragment = _fragment("content.Text", ())
    storage_fragment = _fragment("storage.Blob", ())
    issue_fragment = _fragment(
        "workflow.Issue",
        ("content.Text", "storage.Blob"),
    )
    content, _ = _package(
        store,
        package_ref="package:content@1.0.0",
        dependencies=(),
        fragment=content_fragment,
    )
    storage, _ = _package(
        store,
        package_ref="package:storage@1.0.0",
        dependencies=(),
        fragment=storage_fragment,
    )
    workflow, workflow_attribution = _package(
        store,
        package_ref="package:workflow@1.0.0",
        dependencies=(content.successor.package_ref, storage.successor.package_ref),
        fragment=issue_fragment,
    )
    empty, bodies = create_typed_empty_catalog(
        target_package_ref=workflow.successor.package_ref
    )
    store.ingest(bodies)
    transitions = (content, storage, workflow)
    fragments = (content_fragment, storage_fragment, issue_fragment)
    owners = tuple(
        TypeOwnerBinding.create(
            type_ref=fragment.type_ref,
            package_ref=transition.successor.package_ref,
        )
        for transition, fragment in zip(transitions, fragments, strict=True)
    )
    catalog_transition = transition_catalog(
        empty,
        package_movements=tuple(
            sorted(
                (
                    PackageRootMovement(
                        transition.successor.package_ref,
                        None,
                        transition.successor,
                        transition,
                    )
                    for transition in transitions
                ),
                key=lambda value: value.package_ref,
            )
        ),
        owner_movements=tuple(
            TypeOwnerBindingMovement(owner.type_ref, None, owner)
            for owner in sorted(owners, key=lambda value: value.type_ref)
        ),
        reader=store.reader(),
        request_ref="request:advancement",
    )
    store.ingest(catalog_transition.emitted_bodies)
    prior_slice = resolve_composed_slice(
        catalog_transition.successor,
        root_type_refs=("workflow.Issue",),
        reader=store.reader(),
        request_ref="request:advancement",
    ).slice
    return (
        store,
        prior_slice,
        workflow,
        workflow_attribution,
        issue_fragment,
    )


def test_prevalidated_slice_helper_preserves_strict_fallback() -> None:
    import aware_meta_type_schema.composed_slice_advancement as advancement
    from aware_meta_type_schema import positive_reader

    _, value, *_ = _world()
    canonical = encode_composition_value(value)
    for proof_token in (
        None,
        object(),
        positive_reader._PREVALIDATED_PROOF_BUNDLE_ADMISSION_TOKEN,
    ):
        admission = advancement._admit_prevalidated_composed_slice(
            value,
            canonical,
            _token=advancement._PREVALIDATED_SLICE_ADMISSION_TOKEN,
            _proof_bundle_token=proof_token,
        )
        assert advancement._slice_admission_context(admission).canonical_bytes == canonical
    with pytest.raises(TypeSchemaComposedSliceAdvancementError):
        advancement._admit_prevalidated_composed_slice(
            value, canonical, _token=object()
        )


def _successor():
    store, prior_slice, workflow, prior_attribution, issue_fragment = _world()
    next_attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref=workflow.successor.package_ref,
        source_path=prior_attribution.source_path,
        document_coordinate_ref="coordinate:workflow:comments-v2",
        bindings=(
            SourceDefinitionBinding(
                issue_fragment.type_ref,
                issue_fragment.to_body().coordinate,
            ),
        ),
    )
    workflow_transition = transition_package(
        workflow.successor,
        definition_movements=(),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                prior_attribution.source_path,
                prior_attribution.to_body().coordinate,
                next_attribution,
            ),
        ),
        reader=store.reader(),
        request_ref="request:advancement",
    )
    store.ingest(workflow_transition.emitted_bodies)
    movement = PackageRootMovement(
        workflow.successor.package_ref,
        workflow.successor.to_body().coordinate,
        workflow_transition.successor,
        workflow_transition,
    )
    catalog_transition = transition_catalog(
        prior_slice.catalog,
        package_movements=(movement,),
        owner_movements=(),
        reader=store.reader(),
        request_ref="request:advancement",
    )
    store.ingest(catalog_transition.emitted_bodies)
    return (
        store,
        prior_slice,
        catalog_transition,
        movement,
        workflow_transition,
    )


def _advance(values, admission: AdmittedTypeSchemaComposedSlice | None = None):
    store, prior_slice, catalog_transition, movement, workflow_transition = values
    if admission is None:
        admission = admit_composed_slice(encode_composition_value(prior_slice))
    result = advance_attribution_only_composed_slice(
        admission,
        catalog_transition=catalog_transition,
        successor_catalog=catalog_transition.successor,
        package_movements=(movement,),
        package_transitions=(workflow_transition,),
        reader=store.reader(),
        request_ref="request:advancement",
    )
    return result


def test_attribution_only_advancement_matches_full_workflow_resolution() -> None:
    values = _successor()
    store, _, catalog_transition, _, _ = values
    result = _advance(values)
    expected = resolve_composed_slice(
        catalog_transition.successor,
        root_type_refs=("workflow.Issue",),
        reader=store.reader(),
        request_ref="request:advancement",
    ).slice

    assert encode_composition_value(result.slice) == encode_composition_value(expected)
    assert result.slice.slice_ref == expected.slice_ref
    assert decode_composed_slice(encode_composition_value(result.slice)) == expected
    assert result.changed_package_refs == ("package:workflow@1.0.0",)
    assert result.fresh_membership_count == 3
    assert result.retained_membership_count == 6
    assert result.fresh_node_count > 0
    assert result.retained_node_count > 0
    assert result.observation.read_count > 0
    assert result.observation.enumeration_attempts == 0


def test_returned_proofs_are_detached_from_retained_admission() -> None:
    values = _successor()
    admission = admit_composed_slice(encode_composition_value(values[1]))
    first = _advance(values, admission)
    retained_refs = {
        node_ref
        for membership in values[1].membership_proofs.memberships
        for node_ref in membership.node_refs
    }
    returned_retained_node = next(
        node
        for node in first.slice.membership_proofs.nodes
        if node.node_ref in retained_refs and node.depth > 0
    )
    object.__setattr__(
        returned_retained_node, "path", "x" * returned_retained_node.depth
    )

    second = _advance(values, admission)

    assert decode_composed_slice(encode_composition_value(second.slice)) == second.slice
    assert encode_composition_value(second.slice) != encode_composition_value(
        first.slice
    )
    assert second.slice.slice_ref == _advance(values, admission).slice.slice_ref


def test_callback_coordinate_mutation_cannot_poison_retained_admission() -> None:
    values = _successor()
    store, _, catalog_transition, movement, workflow_transition = values
    admission = admit_composed_slice(encode_composition_value(values[1]))
    observed: list = []
    calls: list[str] = []

    class ForeignCoordinateRef(str):
        def __hash__(self) -> int:
            calls.append("foreign_retained_coordinate_hash")
            raise RuntimeError("foreign retained coordinate hash executed")

    def capturing_read(expected):
        observed.append(expected)
        body = store.values[expected.body_ref]
        return PositiveBodyRead(
            body.coordinate.body_ref,
            body.coordinate.body_digest,
            body.coordinate.size_bytes,
            body.coordinate.schema,
            body.canonical_bytes,
        )

    first = advance_attribution_only_composed_slice(
        admission,
        catalog_transition=catalog_transition,
        successor_catalog=catalog_transition.successor,
        package_movements=(movement,),
        package_transitions=(workflow_transition,),
        reader=TypeSchemaPositiveReaderCapability(
            request_ref="request:advancement",
            read_body=capturing_read,
        ),
        request_ref="request:advancement",
    )
    assert observed
    object.__setattr__(
        observed[0],
        "coordinate_ref",
        ForeignCoordinateRef(observed[0].coordinate_ref),
    )

    second = _advance(values, admission)

    assert first.slice.slice_ref == second.slice.slice_ref
    assert decode_composed_slice(encode_composition_value(second.slice)) == second.slice
    assert calls == []


def test_admission_and_foreign_nested_values_fail_before_behavior() -> None:
    values = _successor()
    store, _, catalog_transition, movement, workflow_transition = values
    with pytest.raises(TypeSchemaComposedSliceAdvancementError, match="not active"):
        advance_attribution_only_composed_slice(
            AdmittedTypeSchemaComposedSlice(),
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(movement,),
            package_transitions=(workflow_transition,),
            reader=store.reader(),
            request_ref="request:advancement",
        )

    calls: list[str] = []

    class ForeignPackage(TypeSchemaPackageRoot):
        def to_body(self):
            calls.append("foreign_to_body")
            raise AssertionError("foreign behavior executed")

    foreign = ForeignPackage(
        **{
            field: getattr(workflow_transition.successor, field)
            for field in (
                "package_ref",
                "package_name",
                "namespace",
                "semantic_version",
                "dependency_package_refs",
                "definition_index",
                "source_attribution_index",
                "package_root_ref",
                "contract",
            )
        }
    )
    poisoned = replace(movement)
    object.__setattr__(poisoned, "next", foreign)
    admission = admit_composed_slice(encode_composition_value(values[1]))
    with pytest.raises(TypeSchemaComposedSliceAdvancementError, match="foreign"):
        advance_attribution_only_composed_slice(
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(poisoned,),
            package_transitions=(workflow_transition,),
            reader=store.reader(),
            request_ref="request:advancement",
        )
    assert calls == []

    class ForeignAdmission(AdmittedTypeSchemaComposedSlice):
        pass

    with pytest.raises(TypeSchemaComposedSliceAdvancementError, match="not exact"):
        advance_attribution_only_composed_slice(
            ForeignAdmission(),
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(movement,),
            package_transitions=(workflow_transition,),
            reader=store.reader(),
            request_ref="request:advancement",
        )

    with pytest.raises((TypeError, ValueError)):
        admit_composed_slice(b" " + encode_composition_value(values[1]))

    class ForeignRequestRef(str):
        def __ne__(self, other):
            calls.append("foreign_request_ne")
            raise AssertionError("foreign request behavior executed")

    def exact_read(expected):
        body = store.values[expected.body_ref]
        return PositiveBodyRead(
            body.coordinate.body_ref,
            body.coordinate.body_digest,
            body.coordinate.size_bytes,
            body.coordinate.schema,
            body.canonical_bytes,
        )

    foreign_request_reader = TypeSchemaPositiveReaderCapability(
        request_ref=ForeignRequestRef("request:advancement"),
        read_body=exact_read,
    )
    with pytest.raises(
        TypeSchemaComposedSliceAdvancementError,
        match="request_ref is not exact",
    ):
        advance_attribution_only_composed_slice(
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(movement,),
            package_transitions=(workflow_transition,),
            reader=foreign_request_reader,
            request_ref="request:advancement",
        )
    assert calls == []


def test_metadata_and_catalog_substitutions_require_full_resolution() -> None:
    values = _successor()
    store, prior_slice, catalog_transition, movement, workflow_transition = values
    admission = admit_composed_slice(encode_composition_value(prior_slice))
    metadata = TypeSchemaPackageRoot.create(
        package_ref=workflow_transition.successor.package_ref,
        package_name=workflow_transition.successor.package_name,
        namespace=workflow_transition.successor.namespace,
        semantic_version="1.0.1",
        dependency_package_refs=workflow_transition.successor.dependency_package_refs,
        definition_index=workflow_transition.successor.definition_index,
        source_attribution_index=workflow_transition.successor.source_attribution_index,
    )
    poisoned_transition = replace(workflow_transition)
    object.__setattr__(poisoned_transition, "successor", metadata)
    poisoned_movement = replace(movement)
    object.__setattr__(poisoned_movement, "next", metadata)
    object.__setattr__(poisoned_movement, "transition", poisoned_transition)
    with pytest.raises(TypeSchemaComposedSliceAdvancementError):
        advance_attribution_only_composed_slice(
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(poisoned_movement,),
            package_transitions=(poisoned_transition,),
            reader=store.reader(),
            request_ref="request:advancement",
        )

    substituted_catalog = replace(catalog_transition.successor)
    object.__setattr__(
        substituted_catalog, "owner_index", prior_slice.catalog.package_index
    )
    with pytest.raises(TypeSchemaComposedSliceAdvancementError, match="strict"):
        advance_attribution_only_composed_slice(
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=substituted_catalog,
            package_movements=(movement,),
            package_transitions=(workflow_transition,),
            reader=store.reader(),
            request_ref="request:advancement",
        )

    restamped_transition = replace(workflow_transition)
    object.__setattr__(restamped_transition, "transition_ref", "sha256:" + "9" * 64)
    restamped_movement = replace(movement)
    object.__setattr__(restamped_movement, "transition", restamped_transition)
    with pytest.raises(TypeSchemaComposedSliceAdvancementError, match="strict"):
        advance_attribution_only_composed_slice(
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(restamped_movement,),
            package_transitions=(restamped_transition,),
            reader=store.reader(),
            request_ref="request:advancement",
        )

    with pytest.raises(TypeSchemaComposedSliceAdvancementError, match="closure"):
        advance_attribution_only_composed_slice(
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(movement,),
            package_transitions=(),
            reader=store.reader(),
            request_ref="request:advancement",
        )

    class ForeignReader(TypeSchemaPositiveReaderCapability):
        pass

    def foreign_read(expected):
        body = store.values[expected.body_ref]
        return PositiveBodyRead(
            body.coordinate.body_ref,
            body.coordinate.body_digest,
            body.coordinate.size_bytes,
            body.coordinate.schema,
            body.canonical_bytes,
        )

    with pytest.raises(TypeSchemaComposedSliceAdvancementError, match="exact"):
        advance_attribution_only_composed_slice(
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(movement,),
            package_transitions=(workflow_transition,),
            reader=ForeignReader(
                request_ref="request:advancement",
                read_body=foreign_read,
            ),
            request_ref="request:advancement",
        )


def test_meta_incremental_workflow_gate_is_below_accepted_thresholds() -> None:
    values = _successor()
    admission = admit_composed_slice(encode_composition_value(values[1]))
    durations: list[float] = []
    for _ in range(2):
        _advance(values, admission)
    for _ in range(10):
        started = time.perf_counter()
        _advance(values, admission)
        durations.append(time.perf_counter() - started)
    median = statistics.median(durations)
    p95 = max(durations)
    assert median < 0.500
    assert p95 < 0.750


def test_real_storage_content_workflow_closure_parity_and_performance() -> None:
    """Exercise the authored Workflow closure, not the miniature unit world."""

    if importlib.util.find_spec("aware_meta_type_schema_aware_source") is None:
        repository_root = next(
            value
            for value in Path(__file__).resolve().parents
            if (value / "workspaces").is_dir()
        )
        kernel_python = repository_root / "workspaces/aware_kernel/.venv/bin/python"
        completed = subprocess.run(
            (
                str(kernel_python),
                "-m",
                "pytest",
                "-q",
                f"{Path(__file__).resolve()}::test_real_storage_content_workflow_closure_parity_and_performance",
                "-s",
            ),
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        return

    from aware_language_parsed_document_contract import NEUTRAL_SYNTAX_IR_SCHEMA
    from aware_meta_type_schema_aware_source import project_parsed_type_schema
    from tree_sitter_aware.parsed_document import (
        TREE_SITTER_AWARE_PARSER_PROFILE,
        AwarePortableParseInput,
        AwareSemanticPackageProjectionRequest,
        parse_aware_document_batch,
    )

    repository_root = next(
        value
        for value in Path(__file__).resolve().parents
        if (value / "workspaces").is_dir()
    )
    package_specs = (
        (
            repository_root
            / "workspaces/aware_kernel/modules/storage/ontology/structure",
            "storage-ontology",
            "aware_storage",
            "package:storage-ontology@1.0.0",
            (),
        ),
        (
            repository_root
            / "workspaces/aware_kernel/modules/content/ontology/structure",
            "content-ontology",
            "aware_content",
            "package:content-ontology@1.0.0",
            ("package:storage-ontology@1.0.0",),
        ),
        (
            repository_root
            / "workspaces/aware_coordination/modules/workflow/ontology/structure",
            "workflow-ontology",
            "aware_workflow",
            "package:workflow-ontology@1.0.0",
            (
                "package:content-ontology@1.0.0",
                "package:storage-ontology@1.0.0",
            ),
        ),
    )

    def digest(value: bytes) -> str:
        return "sha256:" + hashlib.sha256(value).hexdigest()

    def projection_for(spec, *, attribution_delta: bool = False):
        root, package_name, prefix, package_ref, dependencies = spec
        sources = []
        for source in sorted((root / "aware").rglob("*.aware")):
            relative = source.relative_to(root / "aware").as_posix()
            source_path = f"{package_name}/aware/{relative}"
            body = source.read_bytes()
            if attribution_delta and relative == "issue/issue.aware":
                body = b"// Gate A attribution-only proof\n" + body
            sources.append((source_path, body))
        parse_inputs = tuple(
            AwarePortableParseInput(
                package_ref,
                package_name,
                source_path,
                f"cas://source/{digest(body)[7:]}",
                digest(body),
                len(body),
                body.decode("utf-8"),
            )
            for source_path, body in sources
        )
        batch = parse_aware_document_batch(parse_inputs).batch
        manifest = (root / "aware.toml").read_bytes()
        request = AwareSemanticPackageProjectionRequest.create(
            composition_authority_digest=digest(b"gate-a-real-workflow-composition"),
            parent_operation_authority_digest=digest(
                b"gate-a-real-workflow-operation"
                + (b"-delta" if attribution_delta else b"-genesis")
            ),
            package_ref=package_ref,
            package_name=package_name,
            package_kind="ontology",
            fqn_prefix=prefix,
            semantic_version="1.0.0",
            package_root=package_name,
            sources_root=f"{package_name}/aware",
            manifest_path=f"{package_name}/aware.toml",
            manifest_ref=f"cas://manifest/{package_name}/{digest(manifest)[7:]}",
            manifest_digest=digest(manifest),
            manifest_size_bytes=len(manifest),
            declared_source_paths=tuple(path for path, _ in sources),
            direct_dependency_package_refs=dependencies,
            dependency_package_refs=dependencies,
            requested_root_refs=(
                "aware_workflow.issue.Issue"
                if package_name == "workflow-ontology"
                else f"{prefix}.__gate_a_package_root__",
            ),
            source_lifecycle="source_delta" if attribution_delta else "genesis",
            parser_contract=NEUTRAL_SYNTAX_IR_SCHEMA,
            parser_profile=TREE_SITTER_AWARE_PARSER_PROFILE,
            parsed_batch_ref=batch.batch_ref,
        )
        return project_parsed_type_schema(request, batch)

    store = _Store()
    transitions = []
    projections = []
    package_transition_spans: list[tuple[str, float]] = []
    for spec in package_specs:
        projection = projection_for(spec)
        projections.append(projection)
        package_ref = spec[3]
        empty, bodies = create_typed_empty_package(
            package_ref=package_ref,
            package_name=spec[1],
            namespace=spec[2],
            semantic_version="1.0.0",
            dependency_package_refs=spec[4],
        )
        store.ingest(bodies)
        package_started = time.perf_counter()
        transition = transition_package(
            empty,
            definition_movements=tuple(
                DefinitionFragmentMovement(value.type_ref, None, value)
                for value in projection.definitions
            ),
            attribution_movements=tuple(
                SourceAttributionFragmentMovement(value.source_path, None, value)
                for value in projection.source_attributions
            ),
            reader=store.reader(),
            request_ref="request:advancement",
        )
        package_transition_spans.append(
            (package_ref, time.perf_counter() - package_started)
        )
        store.ingest(transition.emitted_bodies)
        transitions.append(transition)

    catalog_empty, bodies = create_typed_empty_catalog(
        target_package_ref="package:workflow-ontology@1.0.0"
    )
    store.ingest(bodies)
    owner_bindings = tuple(
        TypeOwnerBinding.create(
            type_ref=definition.type_ref,
            package_ref=transition.successor.package_ref,
        )
        for transition, projection in zip(transitions, projections, strict=True)
        for definition in projection.definitions
    )
    catalog_started = time.perf_counter()
    catalog_genesis = transition_catalog(
        catalog_empty,
        package_movements=tuple(
            sorted(
                (
                    PackageRootMovement(
                        value.successor.package_ref,
                        None,
                        value.successor,
                        value,
                    )
                    for value in transitions
                ),
                key=lambda value: value.package_ref,
            )
        ),
        owner_movements=tuple(
            TypeOwnerBindingMovement(value.type_ref, None, value)
            for value in sorted(owner_bindings, key=lambda value: value.type_ref)
        ),
        reader=store.reader(),
        request_ref="request:advancement",
    )
    catalog_seconds = time.perf_counter() - catalog_started
    store.ingest(catalog_genesis.emitted_bodies)
    composition_started = time.perf_counter()
    prior = resolve_composed_slice(
        catalog_genesis.successor,
        root_type_refs=("aware_workflow.issue.Issue",),
        reader=store.reader(),
        request_ref="request:advancement",
    ).slice
    composition_seconds = time.perf_counter() - composition_started
    print(
        "meta_bootstrap_visibility "
        + " ".join(
            f"{package_ref}={duration:.6f}"
            for package_ref, duration in package_transition_spans
        )
        + f" catalog={catalog_seconds:.6f} composition={composition_seconds:.6f}"
    )

    if os.environ.get("AWARE_RUN_META_TYPE_SCHEMA_RELEASE") == "1":
        package_roots = (
            "aware_storage.bucket.StorageBucket",
            "aware_content.content.Content",
            "aware_workflow.issue.Issue",
        )

        def bootstrap_target(target_index: int):
            sample_store = _Store()
            sample_transitions = []
            target_package_seconds = 0.0
            outer_started = 0.0
            for index, (spec, projection) in enumerate(
                zip(package_specs, projections, strict=True)
            ):
                if index > target_index:
                    break
                package_ref = spec[3]
                empty, empty_bodies = create_typed_empty_package(
                    package_ref=package_ref,
                    package_name=spec[1],
                    namespace=spec[2],
                    semantic_version="1.0.0",
                    dependency_package_refs=spec[4],
                )
                sample_store.ingest(empty_bodies)
                if index == target_index:
                    outer_started = time.perf_counter()
                package_started = time.perf_counter()
                result = transition_package(
                    empty,
                    definition_movements=tuple(
                        DefinitionFragmentMovement(value.type_ref, None, value)
                        for value in projection.definitions
                    ),
                    attribution_movements=tuple(
                        SourceAttributionFragmentMovement(
                            value.source_path, None, value
                        )
                        for value in projection.source_attributions
                    ),
                    reader=sample_store.reader(),
                    request_ref="request:advancement",
                )
                package_elapsed = time.perf_counter() - package_started
                if index == target_index:
                    target_package_seconds = package_elapsed
                sample_store.ingest(result.emitted_bodies)
                sample_transitions.append(result)

            target_ref = sample_transitions[-1].successor.package_ref
            empty_catalog, empty_catalog_bodies = create_typed_empty_catalog(
                target_package_ref=target_ref
            )
            sample_store.ingest(empty_catalog_bodies)
            owners = tuple(
                TypeOwnerBinding.create(
                    type_ref=definition.type_ref,
                    package_ref=transition.successor.package_ref,
                )
                for transition, projection in zip(
                    sample_transitions,
                    projections[: target_index + 1],
                    strict=True,
                )
                for definition in projection.definitions
            )
            catalog_started = time.perf_counter()
            catalog_result = transition_catalog(
                empty_catalog,
                package_movements=tuple(
                    sorted(
                        (
                            PackageRootMovement(
                                value.successor.package_ref,
                                None,
                                value.successor,
                                value,
                            )
                            for value in sample_transitions
                        ),
                        key=lambda value: value.package_ref,
                    )
                ),
                owner_movements=tuple(
                    TypeOwnerBindingMovement(value.type_ref, None, value)
                    for value in sorted(owners, key=lambda value: value.type_ref)
                ),
                reader=sample_store.reader(),
                request_ref="request:advancement",
            )
            catalog_elapsed = time.perf_counter() - catalog_started
            sample_store.ingest(catalog_result.emitted_bodies)
            composition_started = time.perf_counter()
            resolve_composed_slice(
                catalog_result.successor,
                root_type_refs=(package_roots[target_index],),
                reader=sample_store.reader(),
                request_ref="request:advancement",
            )
            composition_elapsed = time.perf_counter() - composition_started
            return (
                time.perf_counter() - outer_started,
                target_package_seconds,
                catalog_elapsed,
                composition_elapsed,
            )

        ceilings = (
            (0.700, 1.000),
            (1.250, 1.600),
            (1.500, 2.000),
        )
        release_failures: list[str] = []
        for target_index, (median_ceiling, p95_ceiling) in enumerate(ceilings):
            for _ in range(2):
                bootstrap_target(target_index)
            samples = tuple(bootstrap_target(target_index) for _ in range(10))
            outer = tuple(value[0] for value in samples)
            median = statistics.median(outer)
            p95 = max(outer)
            print(
                "meta_release_bootstrap "
                f"package={package_specs[target_index][3]} "
                f"samples={samples} median={median:.6f} p95={p95:.6f}"
            )
            if median >= median_ceiling or p95 >= p95_ceiling:
                release_failures.append(
                    f"{package_specs[target_index][3]}: "
                    f"median={median:.6f}/{median_ceiling:.6f}, "
                    f"p95={p95:.6f}/{p95_ceiling:.6f}"
                )

        def current_chain():
            sample_store = _Store()
            sample_store.ingest(tuple(store.values.values()))
            outer_started = time.perf_counter()
            package_spans = []
            for prior_transition in transitions:
                package_started = time.perf_counter()
                current = transition_package(
                    prior_transition.successor,
                    definition_movements=(),
                    attribution_movements=(),
                    reader=sample_store.reader(),
                    request_ref="request:advancement",
                )
                package_spans.append(time.perf_counter() - package_started)
                assert current.successor == prior_transition.successor
                assert not current.emitted_bodies
            catalog_started = time.perf_counter()
            current_catalog = transition_catalog(
                catalog_genesis.successor,
                package_movements=(),
                owner_movements=(),
                reader=sample_store.reader(),
                request_ref="request:advancement",
            )
            catalog_elapsed = time.perf_counter() - catalog_started
            assert current_catalog.successor == catalog_genesis.successor
            assert not current_catalog.emitted_bodies
            return (
                time.perf_counter() - outer_started,
                tuple(package_spans),
                catalog_elapsed,
            )

        for _ in range(2):
            current_chain()
        current_samples = tuple(current_chain() for _ in range(10))
        current_outer = tuple(value[0] for value in current_samples)
        current_median = statistics.median(current_outer)
        current_p95 = max(current_outer)
        print(
            "meta_release_current "
            f"samples={current_samples} median={current_median:.6f} "
            f"p95={current_p95:.6f}"
        )
        if current_median >= 0.250 or current_p95 >= 0.400:
            release_failures.append(
                "CURRENT: "
                f"median={current_median:.6f}/0.250000, "
                f"p95={current_p95:.6f}/0.400000"
            )
        assert not release_failures, "; ".join(release_failures)

    workflow_prior = transitions[-1]
    workflow_projection = projections[-1]
    workflow_next_projection = projection_for(package_specs[-1], attribution_delta=True)
    assert tuple(
        value.fragment_ref for value in workflow_projection.definitions
    ) == tuple(value.fragment_ref for value in workflow_next_projection.definitions)
    prior_attribution = {
        value.source_path: value for value in workflow_projection.source_attributions
    }
    changed_attributions = tuple(
        value
        for value in workflow_next_projection.source_attributions
        if value.to_body().coordinate
        != prior_attribution[value.source_path].to_body().coordinate
    )
    assert len(changed_attributions) == 1
    next_attribution = changed_attributions[0]
    package_transition = transition_package(
        workflow_prior.successor,
        definition_movements=(),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                next_attribution.source_path,
                prior_attribution[next_attribution.source_path].to_body().coordinate,
                next_attribution,
            ),
        ),
        reader=store.reader(),
        request_ref="request:advancement",
    )
    store.ingest(package_transition.emitted_bodies)
    movement = PackageRootMovement(
        package_transition.successor.package_ref,
        workflow_prior.successor.to_body().coordinate,
        package_transition.successor,
        package_transition,
    )
    catalog_transition = transition_catalog(
        catalog_genesis.successor,
        package_movements=(movement,),
        owner_movements=(),
        reader=store.reader(),
        request_ref="request:advancement",
    )
    store.ingest(catalog_transition.emitted_bodies)
    calls_before_full_resolution = store.calls
    expected = resolve_composed_slice(
        catalog_transition.successor,
        root_type_refs=("aware_workflow.issue.Issue",),
        reader=store.reader(),
        request_ref="request:advancement",
    ).slice
    full_resolution_reads = store.calls - calls_before_full_resolution
    admission = admit_composed_slice(encode_composition_value(prior))

    def advance_real():
        return advance_attribution_only_composed_slice(
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=catalog_transition.successor,
            package_movements=(movement,),
            package_transitions=(package_transition,),
            reader=store.reader(),
            request_ref="request:advancement",
        )

    first = advance_real()
    assert encode_composition_value(first.slice) == encode_composition_value(expected)
    for _ in range(2):
        advance_real()
    durations = []
    for _ in range(10):
        started = time.perf_counter()
        result = advance_real()
        durations.append(time.perf_counter() - started)
        assert encode_composition_value(result.slice) == encode_composition_value(
            expected
        )
    median = statistics.median(durations)
    p95 = max(durations)
    print(
        "gate_a_real_workflow "
        f"definitions={len(prior.definitions)} "
        f"memberships={len(prior.membership_proofs.memberships)} "
        f"full_resolution_reads={full_resolution_reads} "
        f"median={median:.6f} p95={p95:.6f}"
    )
    if os.environ.get("AWARE_RUN_META_TYPE_SCHEMA_RELEASE") == "1":
        prior_slice_bytes = encode_composition_value(prior)
        workflow_package_bytes = encode_composition_value(workflow_prior.successor)
        catalog_bytes = encode_composition_value(catalog_genesis.successor)
        next_attribution_bytes = next_attribution.to_body().canonical_bytes
        prior_attribution_coordinate_wire = prior_attribution[
            next_attribution.source_path
        ].to_body().coordinate.to_wire()
        retained_bodies = tuple(store.values.values())
        expected_bytes = encode_composition_value(expected)

        def delta_chain():
            sample_store = _Store()
            sample_store.ingest(
                tuple(
                    PersistentBodyAuthority(
                        persistent_body_coordinate_from_wire(
                            body.coordinate.to_wire()
                        ),
                        bytes(body.canonical_bytes),
                    )
                    for body in retained_bodies
                )
            )
            sample_prior_slice = decode_composed_slice(prior_slice_bytes)
            sample_admission = admit_composed_slice(
                encode_composition_value(sample_prior_slice)
            )
            sample_workflow_package = decode_package_root(workflow_package_bytes)
            sample_catalog = decode_catalog_root(catalog_bytes)
            sample_next_attribution = decode_source_attribution_fragment(
                next_attribution_bytes
            )
            sample_prior_attribution_coordinate = (
                persistent_body_coordinate_from_wire(
                    prior_attribution_coordinate_wire
                )
            )

            outer_started = time.perf_counter()
            package_started = time.perf_counter()
            sample_package_transition = transition_package(
                sample_workflow_package,
                definition_movements=(),
                attribution_movements=(
                    SourceAttributionFragmentMovement(
                        sample_next_attribution.source_path,
                        sample_prior_attribution_coordinate,
                        sample_next_attribution,
                    ),
                ),
                reader=sample_store.reader(),
                request_ref="request:advancement",
            )
            package_elapsed = time.perf_counter() - package_started
            sample_store.ingest(sample_package_transition.emitted_bodies)
            sample_movement = PackageRootMovement(
                sample_package_transition.successor.package_ref,
                sample_workflow_package.to_body().coordinate,
                sample_package_transition.successor,
                sample_package_transition,
            )
            catalog_started = time.perf_counter()
            sample_catalog_transition = transition_catalog(
                sample_catalog,
                package_movements=(sample_movement,),
                owner_movements=(),
                reader=sample_store.reader(),
                request_ref="request:advancement",
            )
            catalog_elapsed = time.perf_counter() - catalog_started
            sample_store.ingest(sample_catalog_transition.emitted_bodies)
            advancement_started = time.perf_counter()
            sample_result = advance_attribution_only_composed_slice(
                sample_admission,
                catalog_transition=sample_catalog_transition,
                successor_catalog=sample_catalog_transition.successor,
                package_movements=(sample_movement,),
                package_transitions=(sample_package_transition,),
                reader=sample_store.reader(),
                request_ref="request:advancement",
            )
            advancement_elapsed = time.perf_counter() - advancement_started
            outer_elapsed = time.perf_counter() - outer_started
            assert encode_composition_value(sample_result.slice) == expected_bytes
            assert outer_elapsed >= (
                package_elapsed + catalog_elapsed + advancement_elapsed
            )
            return (
                outer_elapsed,
                package_elapsed,
                catalog_elapsed,
                advancement_elapsed,
            )

        for _ in range(2):
            delta_chain()
        delta_samples = tuple(delta_chain() for _ in range(10))
        delta_outer = tuple(value[0] for value in delta_samples)
        delta_median = statistics.median(delta_outer)
        delta_p95 = max(delta_outer)
        print(
            "meta_release_attribution_delta "
            f"samples={delta_samples} median={delta_median:.6f} "
            f"p95={delta_p95:.6f}"
        )
        assert delta_median < 0.750
        assert delta_p95 < 1.000
    assert len(prior.definitions) > 3
    assert full_resolution_reads > 0
    assert median < 0.500
    assert p95 < 0.750
