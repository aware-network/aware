from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from aware_meta_type_schema.composition import (
    ComposedPackageEvidence,
    ComposedTypeOwnerEvidence,
    TypeOwnerBinding,
    TypeSchemaCatalogRoot,
    TypeSchemaComposedSlice,
    TypeSchemaCompositionError,
    resolve_composed_slice,
)
from aware_meta_type_schema.composition_transition import (
    DefinitionFragmentMovement,
    PackageRootMovement,
    SourceAttributionFragmentMovement,
    TypeOwnerBindingMovement,
    TypeSchemaTransitionError,
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
from aware_meta_type_schema.encoding import digest_payload
from aware_meta_type_schema.model import (
    FieldDefinition,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    ValueShape,
)
from aware_meta_type_schema.persistent_index import PersistentBodyAuthority
from aware_meta_type_schema.positive_reader import (
    PositiveBodyRead,
    TypeSchemaPositiveReaderCapability,
    lookup_index_value,
)

_FIXTURES = (
    Path(__file__).resolve().parents[2] / "contracts/v2/workflow-content-storage"
)


class _Store:
    def __init__(self) -> None:
        self.values: dict[str, PersistentBodyAuthority] = {}
        self.calls = 0

    def ingest(self, values: tuple[PersistentBodyAuthority, ...]) -> None:
        self.values.update((value.coordinate.body_ref, value) for value in values)

    def reader(
        self,
        *,
        cache_hit: bool = False,
        elapsed_ns: int = 0,
        on_read: Callable[[], None] | None = None,
    ):
        def read(expected):
            self.calls += 1
            if on_read is not None:
                on_read()
            body = self.values[expected.body_ref]
            return PositiveBodyRead(
                body.coordinate.body_ref,
                body.coordinate.body_digest,
                body.coordinate.size_bytes,
                body.coordinate.schema,
                body.canonical_bytes,
                cache_hit=cache_hit,
                elapsed_ns=elapsed_ns,
            )

        return TypeSchemaPositiveReaderCapability(
            request_ref="request:slice",
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
        document_coordinate_ref=f"coordinate:{name}",
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
                attribution.source_path, None, attribution
            ),
        ),
        reader=store.reader(),
        request_ref="request:slice",
    )
    store.ingest(transition.emitted_bodies)
    return transition


def _world():
    store = _Store()
    content_fragment = _fragment("content.Text", ())
    storage_fragment = _fragment("storage.Blob", ())
    issue_fragment = _fragment(
        "workflow.Issue",
        ("content.Text", "storage.Blob"),
    )
    content = _package(
        store,
        package_ref="package:content@1.0.0",
        dependencies=(),
        fragment=content_fragment,
    )
    storage = _package(
        store,
        package_ref="package:storage@1.0.0",
        dependencies=(),
        fragment=storage_fragment,
    )
    workflow = _package(
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
    packages = tuple(item.successor for item in transitions)
    fragments = (content_fragment, storage_fragment, issue_fragment)
    owners = tuple(
        TypeOwnerBinding.create(
            type_ref=fragment.type_ref, package_ref=package.package_ref
        )
        for package, fragment in zip(packages, fragments, strict=True)
    )
    catalog = transition_catalog(
        empty,
        package_movements=tuple(
            PackageRootMovement(
                transition.successor.package_ref,
                None,
                transition.successor,
                transition,
            )
            for transition in reversed(transitions)
        ),
        owner_movements=tuple(
            TypeOwnerBindingMovement(owner.type_ref, None, owner)
            for owner in reversed(owners)
        ),
        reader=store.reader(),
        request_ref="request:slice",
    )
    store.ingest(catalog.emitted_bodies)
    return store, catalog.successor


def test_issue_slice_resolves_exact_positive_cross_package_closure() -> None:
    store, catalog = _world()
    calls_before = store.calls

    result = resolve_composed_slice(
        catalog,
        root_type_refs=("workflow.Issue",),
        reader=store.reader(),
        request_ref="request:slice",
    )

    assert result.slice.target_package_ref == "package:workflow@1.0.0"
    assert result.slice.dependency_package_refs == (
        "package:content@1.0.0",
        "package:storage@1.0.0",
    )
    assert tuple(value.type_ref for value in result.slice.definitions) == (
        "content.Text",
        "storage.Blob",
        "workflow.Issue",
    )
    assert tuple(value.type_ref for value in result.slice.owners) == (
        "content.Text",
        "storage.Blob",
        "workflow.Issue",
    )
    assert result.observation.enumeration_attempts == 0
    assert result.observation.read_count == store.calls - calls_before
    strict = TypeSchemaComposedSlice.create(
        catalog=result.slice.catalog,
        target_package_ref=result.slice.target_package_ref,
        dependency_package_refs=result.slice.dependency_package_refs,
        root_type_refs=result.slice.root_type_refs,
        packages=result.slice.packages,
        definitions=result.slice.definitions,
        owners=result.slice.owners,
        membership_proofs=result.slice.membership_proofs,
    )
    assert strict == result.slice
    assert strict.to_wire() == result.slice.to_wire()

    second = resolve_composed_slice(
        catalog,
        root_type_refs=("workflow.Issue",),
        reader=store.reader(),
        request_ref="request:slice",
    )
    assert result.slice.catalog is not catalog
    assert result.slice.catalog is not second.slice.catalog
    assert result.slice.packages[0] is not second.slice.packages[0]
    assert result.slice.definitions[0] is not second.slice.definitions[0]
    object.__setattr__(result.slice.catalog, "target_package_ref", "package:poison")
    object.__setattr__(result.slice.packages[0].package, "package_name", "poison")
    object.__setattr__(result.slice.definitions[0], "fragment_ref", "poison")
    assert catalog.target_package_ref == "package:workflow@1.0.0"
    assert second.slice.catalog.target_package_ref == "package:workflow@1.0.0"
    assert second.slice.packages[0].package.package_name != "poison"
    assert second.slice.definitions[0].fragment_ref != "poison"
    later = resolve_composed_slice(
        catalog,
        root_type_refs=("workflow.Issue",),
        reader=store.reader(),
        request_ref="request:slice",
    )
    assert later.slice.catalog.target_package_ref == "package:workflow@1.0.0"
    assert later.slice.packages[0].package.package_name != "poison"
    assert later.slice.definitions[0].fragment_ref != "poison"


def test_composition_rejects_callback_mutation_and_terminates_context() -> None:
    for target in ("catalog", "root"):
        store, catalog = _world()
        original_target = catalog.target_package_ref
        original_root_ref = catalog.owner_index.root_ref
        mutated = False

        def mutate(*, target: str = target, catalog=catalog) -> None:
            nonlocal mutated
            if mutated:
                return
            mutated = True
            if target == "catalog":
                object.__setattr__(catalog, "target_package_ref", "poison")
            else:
                object.__setattr__(
                    catalog.owner_index,
                    "root_ref",
                    "sha256:" + "9" * 64,
                )

        with pytest.raises(TypeSchemaCompositionError, match="changed after admission"):
            resolve_composed_slice(
                catalog,
                root_type_refs=("workflow.Issue",),
                reader=store.reader(on_read=mutate),
                request_ref="request:slice",
            )
        if target == "catalog":
            object.__setattr__(
                catalog,
                "target_package_ref",
                original_target,
            )
        else:
            object.__setattr__(
                catalog.owner_index,
                "root_ref",
                original_root_ref,
            )
        assert resolve_composed_slice(
            catalog,
            root_type_refs=("workflow.Issue",),
            reader=store.reader(),
            request_ref="request:slice",
        ).slice.target_package_ref == "package:workflow@1.0.0"


def test_composition_rejects_module_spoof_and_fake_nominal() -> None:
    store, catalog = _world()
    calls: list[str] = []

    class ModuleSpoofedCatalog(TypeSchemaCatalogRoot):
        __module__ = "aware_meta_type_schema.composition"

        @property
        def target_package_ref(  # pyright: ignore[reportIncompatibleVariableOverride]
            self,
        ):
            calls.append("module_spoof_target_package_ref")
            raise AssertionError("foreign behavior executed")

    spoofed = object.__new__(ModuleSpoofedCatalog)
    for field_name in TypeSchemaCatalogRoot.__slots__:
        TypeSchemaCatalogRoot.__dict__[field_name].__set__(
            spoofed,
            object.__getattribute__(catalog, field_name),
        )

    class AdmittedForeignIndex:
        __module__ = "aware_meta_type_schema.composition"

        @property
        def root_ref(self):
            calls.append("fake_nominal_root_ref")
            raise AssertionError("foreign behavior executed")

    fake_nominal_catalog = TypeSchemaCatalogRoot(
        catalog.target_package_ref,
        catalog.package_index,
        catalog.owner_index,
        catalog.package_count,
        catalog.owner_count,
        catalog.catalog_ref,
        catalog.contract,
    )
    object.__setattr__(
        fake_nominal_catalog,
        "owner_index",
        AdmittedForeignIndex(),
    )

    class ForeignHashMeta(type):
        def __hash__(cls) -> int:
            calls.append("foreign_metaclass_hash")
            raise AssertionError("foreign metaclass hash executed")

    class ForeignEqualityMeta(type):
        def __hash__(cls) -> int:
            return type.__hash__(TypeSchemaCatalogRoot)

        def __eq__(cls, other: object) -> bool:
            calls.append("foreign_metaclass_equality")
            raise AssertionError("foreign metaclass equality executed")

    class HashingCatalog(TypeSchemaCatalogRoot, metaclass=ForeignHashMeta):
        __module__ = "aware_meta_type_schema.composition"

    class EqualityCatalog(TypeSchemaCatalogRoot, metaclass=ForeignEqualityMeta):
        __module__ = "aware_meta_type_schema.composition"

    hostile_metaclass_catalogs = []
    for foreign_type in (HashingCatalog, EqualityCatalog):
        foreign = object.__new__(foreign_type)
        for field_name in TypeSchemaCatalogRoot.__slots__:
            TypeSchemaCatalogRoot.__dict__[field_name].__set__(
                foreign,
                object.__getattribute__(catalog, field_name),
            )
        hostile_metaclass_catalogs.append(foreign)

    for candidate in (
        spoofed,
        fake_nominal_catalog,
        *hostile_metaclass_catalogs,
    ):
        with pytest.raises(TypeSchemaCompositionError, match="operand admission"):
            resolve_composed_slice(
                candidate,
                root_type_refs=("workflow.Issue",),
                reader=store.reader(),
                request_ref="request:slice",
            )
    assert calls == []


def test_observation_changes_do_not_change_composed_slice_authority() -> None:
    cold_store, catalog = _world()
    cold = resolve_composed_slice(
        catalog,
        root_type_refs=("workflow.Issue",),
        reader=cold_store.reader(elapsed_ns=100),
        request_ref="request:slice",
    )
    warm_store = _Store()
    warm_store.values.update(cold_store.values)
    warm = resolve_composed_slice(
        catalog,
        root_type_refs=("workflow.Issue",),
        reader=warm_store.reader(cache_hit=True, elapsed_ns=1),
        request_ref="request:slice",
    )

    assert cold.slice == warm.slice
    assert cold.observation != warm.observation
    assert "observation" not in cold.slice.to_wire()


def test_slice_binds_exact_catalog_and_index_membership_proofs() -> None:
    store, catalog = _world()
    value = resolve_composed_slice(
        catalog,
        root_type_refs=("workflow.Issue",),
        reader=store.reader(),
        request_ref="request:slice",
    ).slice
    assert len(value.membership_proofs.nodes) < sum(
        len(proof.node_refs) for proof in value.membership_proofs.memberships
    )

    empty_catalog, _ = create_typed_empty_catalog(
        target_package_ref=value.target_package_ref
    )
    semantic = value.semantic_wire()
    semantic["catalog"] = empty_catalog.catalog.to_wire()
    with pytest.raises(TypeSchemaCompositionError, match="membership proofs"):
        TypeSchemaComposedSlice(
            catalog=empty_catalog.catalog,
            target_package_ref=value.target_package_ref,
            dependency_package_refs=value.dependency_package_refs,
            root_type_refs=value.root_type_refs,
            packages=value.packages,
            definitions=value.definitions,
            owners=value.owners,
            membership_proofs=value.membership_proofs,
            slice_ref=digest_payload(value.contract, semantic),
        )

    empty_package, _ = create_typed_empty_package(
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        namespace="workflow",
        semantic_version="1.0.0",
        dependency_package_refs=value.dependency_package_refs,
    )
    old_package = value.packages[-1]
    substituted_package = ComposedPackageEvidence(
        old_package.package_ref,
        empty_package.package,
        empty_package.package.to_body().coordinate,
    )
    substituted_owners = tuple(
        (
            replace(owner, package=substituted_package.coordinate)
            if owner.package_ref == substituted_package.package_ref
            else owner
        )
        for owner in value.owners
    )
    substituted_packages = (*value.packages[:-1], substituted_package)
    semantic = value.semantic_wire()
    semantic["packages"] = [item.to_wire() for item in substituted_packages]
    semantic["owners"] = [item.to_wire() for item in substituted_owners]
    with pytest.raises(TypeSchemaCompositionError, match="membership proofs"):
        TypeSchemaComposedSlice(
            catalog=value.catalog,
            target_package_ref=value.target_package_ref,
            dependency_package_refs=value.dependency_package_refs,
            root_type_refs=value.root_type_refs,
            packages=substituted_packages,
            definitions=value.definitions,
            owners=substituted_owners,
            membership_proofs=value.membership_proofs,
            slice_ref=digest_payload(value.contract, semantic),
        )


def test_single_root_does_not_pull_unreferenced_definition() -> None:
    store, catalog = _world()
    result = resolve_composed_slice(
        catalog,
        root_type_refs=("content.Text",),
        reader=store.reader(),
        request_ref="request:slice",
    )
    assert tuple(value.type_ref for value in result.slice.definitions) == (
        "content.Text",
    )


def test_owner_outside_target_reachable_packages_fails_closed() -> None:
    store, catalog = _world()
    prior_owner, _ = lookup_index_value(
        catalog.owner_index,
        key="workflow.Issue",
        reader=store.reader(),
        request_ref="request:slice",
    )
    assert prior_owner is not None
    substituted = TypeOwnerBinding.create(
        type_ref="workflow.Issue",
        package_ref="package:external@1.0.0",
    )
    with pytest.raises(TypeSchemaTransitionError, match="lifecycle"):
        transition_catalog(
            catalog,
            package_movements=(),
            owner_movements=(
                TypeOwnerBindingMovement(
                    "workflow.Issue",
                    prior_owner,
                    substituted,
                ),
            ),
            reader=store.reader(),
            request_ref="request:slice",
        )


def test_composed_slice_rejects_coherently_restamped_coordinate_substitution() -> None:
    store, catalog = _world()
    value = resolve_composed_slice(
        catalog,
        root_type_refs=("workflow.Issue",),
        reader=store.reader(),
        request_ref="request:slice",
    ).slice
    owner = value.owners[-1]
    substituted_owner = replace(owner, definition=owner.owner)
    semantic = value.semantic_wire()
    semantic["owners"] = [
        (
            item.to_wire()
            if item.type_ref != owner.type_ref
            else substituted_owner.to_wire()
        )
        for item in value.owners
    ]
    with pytest.raises(TypeSchemaCompositionError, match="definition coordinate"):
        TypeSchemaComposedSlice(
            catalog=value.catalog,
            target_package_ref=value.target_package_ref,
            dependency_package_refs=value.dependency_package_refs,
            root_type_refs=value.root_type_refs,
            packages=value.packages,
            definitions=value.definitions,
            owners=(*value.owners[:-1], substituted_owner),
            membership_proofs=value.membership_proofs,
            slice_ref=digest_payload(value.contract, semantic),
        )

    package = value.packages[-1]
    with pytest.raises(TypeSchemaCompositionError, match="exact package root"):
        ComposedPackageEvidence(
            package.package_ref,
            package.package,
            value.owners[0].owner,
        )

    with pytest.raises(TypeSchemaCompositionError, match="exact type/package"):
        ComposedTypeOwnerEvidence(
            owner.type_ref,
            owner.package_ref,
            owner.definition,
            owner.package,
            owner.definition,
        )

    semantic = value.semantic_wire()
    semantic["packages"] = [item.to_wire() for item in value.packages[:-1]]
    with pytest.raises(TypeSchemaCompositionError, match="package evidence differs"):
        TypeSchemaComposedSlice(
            catalog=value.catalog,
            target_package_ref=value.target_package_ref,
            dependency_package_refs=value.dependency_package_refs,
            root_type_refs=value.root_type_refs,
            packages=value.packages[:-1],
            definitions=value.definitions,
            owners=value.owners,
            membership_proofs=value.membership_proofs,
            slice_ref=digest_payload(value.contract, semantic),
        )


def test_cyclic_package_dependency_authority_fails_before_type_lookup() -> None:
    store = _Store()
    package_a, bodies_a = create_typed_empty_package(
        package_ref="package:a@1.0.0",
        package_name="a",
        namespace="a",
        semantic_version="1.0.0",
        dependency_package_refs=("package:b@1.0.0",),
    )
    package_b, bodies_b = create_typed_empty_package(
        package_ref="package:b@1.0.0",
        package_name="b",
        namespace="b",
        semantic_version="1.0.0",
        dependency_package_refs=("package:a@1.0.0",),
    )
    store.ingest((*bodies_a, *bodies_b))
    transition_a = transition_package(
        package_a,
        definition_movements=(),
        attribution_movements=(),
        reader=store.reader(),
        request_ref="request:slice",
    )
    transition_b = transition_package(
        package_b,
        definition_movements=(),
        attribution_movements=(),
        reader=store.reader(),
        request_ref="request:slice",
    )
    empty, catalog_bodies = create_typed_empty_catalog(
        target_package_ref="package:a@1.0.0"
    )
    store.ingest(catalog_bodies)
    with pytest.raises(TypeSchemaTransitionError, match="cycle"):
        transition_catalog(
            empty,
            package_movements=(
                PackageRootMovement(
                    package_a.package.package_ref,
                    None,
                    package_a.package,
                    transition_a,
                ),
                PackageRootMovement(
                    package_b.package.package_ref,
                    None,
                    package_b.package,
                    transition_b,
                ),
            ),
            owner_movements=(),
            reader=store.reader(),
            request_ref="request:slice",
        )


def test_workflow_content_storage_conformance_fixtures_match_runtime() -> None:
    typed = json.loads((_FIXTURES / "typed-empty-roots.json").read_text())
    expected_packages = []
    for package_ref, name, dependencies in (
        ("package:content@1.0.0", "content", ()),
        ("package:storage@1.0.0", "storage", ()),
        (
            "package:workflow@1.0.0",
            "workflow",
            ("package:content@1.0.0", "package:storage@1.0.0"),
        ),
    ):
        empty, _ = create_typed_empty_package(
            package_ref=package_ref,
            package_name=name,
            namespace=name,
            semantic_version="1.0.0",
            dependency_package_refs=dependencies,
        )
        expected_packages.append(
            {
                "package_ref": package_ref,
                "empty_ref": empty.empty_ref,
                "package_root_ref": empty.package.package_root_ref,
                "definition_root_ref": empty.package.definition_index.root_ref,
                "attribution_root_ref": empty.package.source_attribution_index.root_ref,
            }
        )
    empty_catalog, _ = create_typed_empty_catalog(
        target_package_ref="package:workflow@1.0.0"
    )
    assert typed["packages"] == expected_packages
    assert typed["catalog"] == {
        "empty_ref": empty_catalog.empty_ref,
        "catalog_ref": empty_catalog.catalog.catalog_ref,
        "package_index_root_ref": empty_catalog.catalog.package_index.root_ref,
        "owner_index_root_ref": empty_catalog.catalog.owner_index.root_ref,
    }

    store, catalog = _world()
    catalog_fixture = json.loads((_FIXTURES / "catalog.json").read_text())
    assert catalog_fixture["catalog_ref"] == catalog.catalog_ref
    assert catalog_fixture["package_index_root_ref"] == catalog.package_index.root_ref
    assert catalog_fixture["owner_index_root_ref"] == catalog.owner_index.root_ref
    result = resolve_composed_slice(
        catalog,
        root_type_refs=("workflow.Issue",),
        reader=store.reader(),
        request_ref="request:slice",
    )
    slice_fixture = json.loads((_FIXTURES / "composed-issue-slice.json").read_text())
    assert slice_fixture["slice_ref"] == result.slice.slice_ref
    assert (
        slice_fixture["membership_proof_bundle_ref"]
        == result.slice.membership_proofs.bundle_ref
    )
    assert slice_fixture["membership_count"] == len(
        result.slice.membership_proofs.memberships
    )
    assert slice_fixture["proof_node_count"] == len(
        result.slice.membership_proofs.nodes
    )
    assert slice_fixture["package_refs"] == [
        value.package_ref for value in result.slice.packages
    ]
    assert slice_fixture["type_refs"] == [
        value.type_ref for value in result.slice.definitions
    ]
