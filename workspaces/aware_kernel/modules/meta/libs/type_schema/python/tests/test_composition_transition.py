from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import Enum

import pytest
from aware_meta_type_schema.composition import (
    TypeOwnerBinding,
    TypeSchemaPackageRoot,
)
from aware_meta_type_schema.composition_transition import (
    CATALOG_TRANSITION_CONTRACT,
    PACKAGE_TRANSITION_CONTRACT,
    DefinitionFragmentMovement,
    PackageRootMovement,
    SourceAttributionFragmentMovement,
    SourceAttributionLifecycleEvidence,
    TypeDefinitionLifecycleEvidence,
    TypeOwnerBindingMovement,
    TypeSchemaCatalogTransition,
    TypeSchemaPackageTransition,
    TypeSchemaTransitionError,
    TypeSchemaTypedEmptyPackageAuthority,
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
    IndexBindingMovement,
    PositiveBodyRead,
    TypeSchemaPositiveReaderCapability,
    lookup_index_value,
    patch_persistent_index,
)


@dataclass
class _Store:
    bodies: dict[str, PersistentBodyAuthority]
    writes: int = 0

    def ingest(self, values: tuple[PersistentBodyAuthority, ...]) -> None:
        self.bodies.update((value.coordinate.body_ref, value) for value in values)

    def reader(
        self,
        request_ref: str = "request:test",
        *,
        on_read: Callable[[], None] | None = None,
    ):
        def read(expected):
            if on_read is not None:
                on_read()
            body = self.bodies[expected.body_ref]
            return PositiveBodyRead(
                body.coordinate.body_ref,
                body.coordinate.body_digest,
                body.coordinate.size_bytes,
                body.coordinate.schema,
                body.canonical_bytes,
            )

        return TypeSchemaPositiveReaderCapability(
            request_ref=request_ref,
            read_body=read,
        )


def _definition(type_ref: str, *named_refs: str) -> TypeDefinitionFragment:
    fields = tuple(
        FieldDefinition(
            field_ref=f"{type_ref}.field{index}",
            name=f"field{index}",
            shape=ValueShape.named(value),
        )
        for index, value in enumerate(named_refs)
    )
    definition = (
        TypeDefinition(
            type_ref=type_ref,
            name=type_ref.rsplit(".", 1)[-1],
            kind=TypeKind.GRAPH_OBJECT,
            fields=fields,
        )
        if named_refs
        else TypeDefinition(
            type_ref=type_ref,
            name=type_ref.rsplit(".", 1)[-1],
            kind=TypeKind.SCALAR_ALIAS,
            scalar_target=ScalarKind.STRING,
        )
    )
    return TypeDefinitionFragment.create(definition)


def _genesis_package(
    store: _Store,
    *,
    package_ref: str,
    package_name: str,
    dependencies: tuple[str, ...],
    fragment: TypeDefinitionFragment,
):
    empty, bodies = create_typed_empty_package(
        package_ref=package_ref,
        package_name=package_name,
        namespace=package_name,
        semantic_version="1.0.0",
        dependency_package_refs=dependencies,
    )
    store.ingest(bodies)
    definition_body = fragment.to_body()
    attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref=package_ref,
        source_path=f"{package_name}/{package_name}.aware",
        document_coordinate_ref=f"coordinate:{package_name}",
        bindings=(
            SourceDefinitionBinding(fragment.type_ref, definition_body.coordinate),
        ),
    )
    result = transition_package(
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
        request_ref="request:test",
    )
    assert store.writes == 0
    store.ingest(result.emitted_bodies)
    return result, fragment, attribution


def _forged_transition(
    original: TypeSchemaPackageTransition,
    *,
    successor: TypeSchemaPackageRoot,
    definition_lifecycle: tuple[TypeDefinitionLifecycleEvidence, ...],
    attribution_lifecycle: tuple[SourceAttributionLifecycleEvidence, ...],
    emitted_bodies: tuple[PersistentBodyAuthority, ...],
) -> TypeSchemaPackageTransition:
    definition_refs = tuple(item.lifecycle_ref for item in definition_lifecycle)
    attribution_refs = tuple(item.lifecycle_ref for item in attribution_lifecycle)
    semantic = {
        "contract": PACKAGE_TRANSITION_CONTRACT,
        "prior": {
            "kind": "typed_empty",
            "authority": original.prior.to_wire(),
        },
        "successor": successor.to_wire(),
        "definition_lifecycle": [item.to_wire() for item in definition_lifecycle],
        "attribution_lifecycle": [item.to_wire() for item in attribution_lifecycle],
        "definition_movement_refs": list(definition_refs),
        "attribution_movement_refs": list(attribution_refs),
        "emitted_bodies": [item.coordinate.to_wire() for item in emitted_bodies],
        "reused_coordinates": [],
    }
    return TypeSchemaPackageTransition(
        prior=original.prior,
        successor=successor,
        definition_lifecycle=definition_lifecycle,
        attribution_lifecycle=attribution_lifecycle,
        definition_movement_refs=definition_refs,
        attribution_movement_refs=attribution_refs,
        emitted_bodies=emitted_bodies,
        reused_coordinates=(),
        transition_ref=digest_payload(PACKAGE_TRANSITION_CONTRACT, semantic),
        observation=original.observation,
    )


def test_typed_empty_workflow_content_storage_genesis_is_delta_only() -> None:
    store = _Store({})
    content = _genesis_package(
        store,
        package_ref="package:content@1.0.0",
        package_name="content",
        dependencies=(),
        fragment=_definition("content.Text"),
    )
    storage = _genesis_package(
        store,
        package_ref="package:storage@1.0.0",
        package_name="storage",
        dependencies=(),
        fragment=_definition("storage.Blob"),
    )
    workflow = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=("package:content@1.0.0", "package:storage@1.0.0"),
        fragment=_definition("workflow.Issue", "content.Text", "storage.Blob"),
    )

    assert workflow[0].successor.definition_index.binding_count == 1
    assert workflow[0].successor.source_attribution_index.binding_count == 1
    assert (
        content[0].successor.package_root_ref != storage[0].successor.package_root_ref
    )
    assert store.writes == 0


def test_private_transition_issuance_matches_strict_public_values() -> None:
    store = _Store({})
    package, fragment, _ = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    strict_package = TypeSchemaPackageTransition(
        package.prior,
        package.successor,
        package.definition_lifecycle,
        package.attribution_lifecycle,
        package.definition_movement_refs,
        package.attribution_movement_refs,
        package.emitted_bodies,
        package.reused_coordinates,
        package.transition_ref,
        package.observation,
        PACKAGE_TRANSITION_CONTRACT,
    )
    assert strict_package == package
    assert strict_package.semantic_wire() == package.semantic_wire()

    empty, bodies = create_typed_empty_catalog(
        target_package_ref=package.successor.package_ref
    )
    store.ingest(bodies)
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package.successor.package_ref,
    )
    catalog = transition_catalog(
        empty,
        package_movements=(
            PackageRootMovement(
                package.successor.package_ref,
                None,
                package.successor,
                package,
            ),
        ),
        owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
        reader=store.reader(),
        request_ref="request:test",
    )
    strict_catalog = TypeSchemaCatalogTransition(
        catalog.prior_ref,
        catalog.successor,
        catalog.package_movement_refs,
        catalog.owner_movement_refs,
        catalog.emitted_bodies,
        catalog.reused_coordinates,
        catalog.transition_ref,
        catalog.observation,
        CATALOG_TRANSITION_CONTRACT,
    )
    assert strict_catalog == catalog
    assert strict_catalog.semantic_wire() == catalog.semantic_wire()


def test_catalog_transition_rejects_callback_mutation_and_terminates_context() -> None:
    store = _Store({})
    package, fragment, _ = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package.successor.package_ref,
    )
    for target in ("catalog", "movement", "root"):
        empty, bodies = create_typed_empty_catalog(
            target_package_ref=package.successor.package_ref
        )
        store.ingest(bodies)
        package_movement = PackageRootMovement(
            package.successor.package_ref,
            None,
            package.successor,
            package,
        )
        owner_movement = TypeOwnerBindingMovement(fragment.type_ref, None, owner)
        original_root_ref = empty.catalog.package_index.root_ref
        mutated = False

        def mutate(
            *,
            target: str = target,
            empty=empty,
            owner_movement: TypeOwnerBindingMovement = owner_movement,
        ) -> None:
            nonlocal mutated
            if mutated:
                return
            mutated = True
            if target == "catalog":
                object.__setattr__(empty.catalog, "target_package_ref", "poison")
            elif target == "movement":
                object.__setattr__(owner_movement, "type_ref", "poison.Type")
            else:
                object.__setattr__(
                    empty.catalog.package_index,
                    "root_ref",
                    "sha256:" + "9" * 64,
                )

        with pytest.raises(TypeSchemaTransitionError, match="changed after admission"):
            transition_catalog(
                empty,
                package_movements=(package_movement,),
                owner_movements=(owner_movement,),
                reader=store.reader(on_read=mutate),
                request_ref="request:test",
            )
        if target == "catalog":
            object.__setattr__(
                empty.catalog,
                "target_package_ref",
                package.successor.package_ref,
            )
        elif target == "movement":
            object.__setattr__(owner_movement, "type_ref", fragment.type_ref)
        else:
            object.__setattr__(
                empty.catalog.package_index,
                "root_ref",
                original_root_ref,
            )
        assert transition_catalog(
            empty,
            package_movements=(package_movement,),
            owner_movements=(owner_movement,),
            reader=store.reader(),
            request_ref="request:test",
        ).successor.target_package_ref == package.successor.package_ref


def test_one_definition_update_reuses_unchanged_package_coordinates() -> None:
    store = _Store({})
    initial, fragment, attribution = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    changed = _definition("workflow.Issue", "workflow.Status")
    changed_body = changed.to_body()
    changed_attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref=initial.successor.package_ref,
        source_path=attribution.source_path,
        document_coordinate_ref="coordinate:workflow:changed",
        bindings=(SourceDefinitionBinding(changed.type_ref, changed_body.coordinate),),
    )

    result = transition_package(
        initial.successor,
        definition_movements=(
            DefinitionFragmentMovement(
                fragment.type_ref,
                fragment.to_body().coordinate,
                changed,
            ),
        ),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                attribution.source_path,
                attribution.to_body().coordinate,
                changed_attribution,
            ),
        ),
        reader=store.reader(),
        request_ref="request:test",
    )

    assert result.successor.definition_index.binding_count == 1
    assert result.successor.package_root_ref != initial.successor.package_root_ref
    assert result.observation.enumeration_attempts == 0
    assert store.writes == 0
    second = transition_package(
        initial.successor,
        definition_movements=(
            DefinitionFragmentMovement(
                fragment.type_ref,
                fragment.to_body().coordinate,
                changed,
            ),
        ),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                attribution.source_path,
                attribution.to_body().coordinate,
                changed_attribution,
            ),
        ),
        reader=store.reader(),
        request_ref="request:test",
    )
    assert result.prior is not initial.successor
    assert result.prior is not second.prior
    assert result.successor is not second.successor
    assert isinstance(result.prior, TypeSchemaPackageRoot)
    assert isinstance(second.prior, TypeSchemaPackageRoot)
    object.__setattr__(result.prior, "package_name", "poison")
    object.__setattr__(result.successor, "package_name", "poison")
    assert initial.successor.package_name == "workflow"
    assert second.prior.package_name == "workflow"
    assert second.successor.package_name == "workflow"
    later = transition_package(
        initial.successor,
        definition_movements=(
            DefinitionFragmentMovement(
                fragment.type_ref,
                fragment.to_body().coordinate,
                changed,
            ),
        ),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                attribution.source_path,
                attribution.to_body().coordinate,
                changed_attribution,
            ),
        ),
        reader=store.reader(),
        request_ref="request:test",
    )
    assert isinstance(later.prior, TypeSchemaPackageRoot)
    assert later.prior.package_name == "workflow"
    assert later.successor.package_name == "workflow"


def test_transition_rejects_foreign_nested_movement_before_behavior() -> None:
    store = _Store({})
    initial, fragment, attribution = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    calls: list[str] = []

    class ForeignDefinitionFragment(TypeDefinitionFragment):
        def to_wire(self):
            calls.append("foreign_to_wire")
            raise AssertionError("foreign behavior executed")

    foreign = ForeignDefinitionFragment(
        fragment.definition,
        fragment.referenced_type_refs,
        fragment.fragment_ref,
        fragment.contract,
    )
    movement = DefinitionFragmentMovement(
        fragment.type_ref,
        fragment.to_body().coordinate,
        fragment,
    )
    object.__setattr__(movement, "next", foreign)
    with pytest.raises(TypeSchemaTransitionError, match="operand admission"):
        transition_package(
            initial.successor,
            definition_movements=(movement,),
            attribution_movements=(
                SourceAttributionFragmentMovement(
                    attribution.source_path,
                    attribution.to_body().coordinate,
                    attribution,
                ),
            ),
            reader=store.reader(),
            request_ref="request:test",
        )
    assert calls == []


def test_package_transition_rejects_module_spoof_and_fake_nominal() -> None:
    store = _Store({})
    initial, fragment, attribution = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    calls: list[str] = []

    class ModuleSpoofedMovement(DefinitionFragmentMovement):
        __module__ = "aware_meta_type_schema.composition_transition"

        @property
        def type_ref(self):  # pyright: ignore[reportIncompatibleVariableOverride]
            calls.append("module_spoof_type_ref")
            raise AssertionError("foreign behavior executed")

    ordinary = DefinitionFragmentMovement(
        fragment.type_ref,
        fragment.to_body().coordinate,
        fragment,
    )
    spoofed = object.__new__(ModuleSpoofedMovement)
    for field_name in DefinitionFragmentMovement.__slots__:
        DefinitionFragmentMovement.__dict__[field_name].__set__(
            spoofed,
            object.__getattribute__(ordinary, field_name),
        )

    class AdmittedForeignFragment:
        __module__ = "aware_meta_type_schema.composition_transition"

        @property
        def type_ref(self):
            calls.append("fake_nominal_type_ref")
            raise AssertionError("foreign behavior executed")

    fake_nominal_movement = DefinitionFragmentMovement(
        fragment.type_ref,
        fragment.to_body().coordinate,
        fragment,
    )
    object.__setattr__(
        fake_nominal_movement,
        "next",
        AdmittedForeignFragment(),
    )

    class ForeignHashMeta(type):
        def __hash__(cls) -> int:
            calls.append("foreign_metaclass_hash")
            raise AssertionError("foreign metaclass hash executed")

    class ForeignEqualityMeta(type):
        def __hash__(cls) -> int:
            return type.__hash__(DefinitionFragmentMovement)

        def __eq__(cls, other: object) -> bool:
            calls.append("foreign_metaclass_equality")
            raise AssertionError("foreign metaclass equality executed")

    class HashingMovement(DefinitionFragmentMovement, metaclass=ForeignHashMeta):
        __module__ = "aware_meta_type_schema.composition_transition"

    class EqualityMovement(
        DefinitionFragmentMovement,
        metaclass=ForeignEqualityMeta,
    ):
        __module__ = "aware_meta_type_schema.composition_transition"

    hostile_metaclass_movements = []
    for foreign_type in (HashingMovement, EqualityMovement):
        foreign = object.__new__(foreign_type)
        for field_name in DefinitionFragmentMovement.__slots__:
            DefinitionFragmentMovement.__dict__[field_name].__set__(
                foreign,
                object.__getattribute__(ordinary, field_name),
            )
        hostile_metaclass_movements.append(foreign)

    for movement in (
        spoofed,
        fake_nominal_movement,
        *hostile_metaclass_movements,
    ):
        with pytest.raises(TypeSchemaTransitionError, match="operand admission"):
            transition_package(
                initial.successor,
                definition_movements=(movement,),
                attribution_movements=(
                    SourceAttributionFragmentMovement(
                        attribution.source_path,
                        attribution.to_body().coordinate,
                        attribution,
                    ),
                ),
                reader=store.reader(),
                request_ref="request:test",
            )

    class ModuleSpoofedTypeKind(str, Enum):
        __module__ = "aware_meta_type_schema.model"

        GRAPH_OBJECT = "graph_object"

        def __eq__(self, other):
            calls.append("module_spoof_enum_equality")
            raise AssertionError("foreign behavior executed")

        __hash__ = str.__hash__

    original_kind = fragment.definition.kind
    object.__setattr__(
        fragment.definition,
        "kind",
        ModuleSpoofedTypeKind.GRAPH_OBJECT,
    )
    with pytest.raises(TypeSchemaTransitionError, match="operand admission"):
        transition_package(
            initial.successor,
            definition_movements=(ordinary,),
            attribution_movements=(
                SourceAttributionFragmentMovement(
                    attribution.source_path,
                    attribution.to_body().coordinate,
                    attribution,
                ),
            ),
            reader=store.reader(),
            request_ref="request:test",
        )
    object.__setattr__(fragment.definition, "kind", original_kind)
    assert calls == []


def test_catalog_transition_rejects_module_spoof_and_fake_nominal() -> None:
    store = _Store({})
    package, fragment, _ = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    empty, bodies = create_typed_empty_catalog(
        target_package_ref=package.successor.package_ref
    )
    store.ingest(bodies)
    ordinary = PackageRootMovement(
        package.successor.package_ref,
        None,
        package.successor,
        package,
    )
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package.successor.package_ref,
    )
    calls: list[str] = []

    class ModuleSpoofedMovement(PackageRootMovement):
        __module__ = "aware_meta_type_schema.composition_transition"

        @property
        def package_ref(self):  # pyright: ignore[reportIncompatibleVariableOverride]
            calls.append("module_spoof_package_ref")
            raise AssertionError("foreign behavior executed")

    spoofed = object.__new__(ModuleSpoofedMovement)
    for field_name in PackageRootMovement.__slots__:
        PackageRootMovement.__dict__[field_name].__set__(
            spoofed,
            object.__getattribute__(ordinary, field_name),
        )

    class AdmittedForeignPackage:
        __module__ = "aware_meta_type_schema.composition_transition"

        @property
        def package_ref(self):
            calls.append("fake_nominal_package_ref")
            raise AssertionError("foreign behavior executed")

    fake_nominal_movement = PackageRootMovement(
        package.successor.package_ref,
        None,
        package.successor,
        package,
    )
    object.__setattr__(
        fake_nominal_movement,
        "next",
        AdmittedForeignPackage(),
    )

    class ForeignHashMeta(type):
        def __hash__(cls) -> int:
            calls.append("foreign_metaclass_hash")
            raise AssertionError("foreign metaclass hash executed")

    class ForeignEqualityMeta(type):
        def __hash__(cls) -> int:
            return type.__hash__(PackageRootMovement)

        def __eq__(cls, other: object) -> bool:
            calls.append("foreign_metaclass_equality")
            raise AssertionError("foreign metaclass equality executed")

    class HashingMovement(PackageRootMovement, metaclass=ForeignHashMeta):
        __module__ = "aware_meta_type_schema.composition_transition"

    class EqualityMovement(PackageRootMovement, metaclass=ForeignEqualityMeta):
        __module__ = "aware_meta_type_schema.composition_transition"

    hostile_metaclass_movements = []
    for foreign_type in (HashingMovement, EqualityMovement):
        foreign = object.__new__(foreign_type)
        for field_name in PackageRootMovement.__slots__:
            PackageRootMovement.__dict__[field_name].__set__(
                foreign,
                object.__getattribute__(ordinary, field_name),
            )
        hostile_metaclass_movements.append(foreign)

    for movement in (
        spoofed,
        fake_nominal_movement,
        *hostile_metaclass_movements,
    ):
        with pytest.raises(TypeSchemaTransitionError, match="operand admission"):
            transition_catalog(
                empty,
                package_movements=(movement,),
                owner_movements=(
                    TypeOwnerBindingMovement(fragment.type_ref, None, owner),
                ),
                reader=store.reader(),
                request_ref="request:test",
            )
    assert calls == []


def test_package_transition_rejects_callback_mutation_and_terminates_context() -> None:
    store = _Store({})
    fragment = _definition("workflow.Issue")
    for target in ("package", "movement", "root"):
        empty, bodies = create_typed_empty_package(
            package_ref="package:workflow@1.0.0",
            package_name="workflow",
            namespace="workflow",
            semantic_version="1.0.0",
        )
        store.ingest(bodies)
        attribution = TypeSchemaSourceAttributionFragment.create(
            package_ref=empty.package.package_ref,
            source_path="workflow/issue.aware",
            document_coordinate_ref="coordinate:workflow",
            bindings=(
                SourceDefinitionBinding(
                    fragment.type_ref,
                    fragment.to_body().coordinate,
                ),
            ),
        )
        definition_movement = DefinitionFragmentMovement(
            fragment.type_ref,
            None,
            fragment,
        )
        attribution_movement = SourceAttributionFragmentMovement(
            attribution.source_path,
            None,
            attribution,
        )
        original_root_ref = empty.package.definition_index.root_ref
        mutated = False

        def mutate(
            *,
            target: str = target,
            empty=empty,
            definition_movement: DefinitionFragmentMovement = definition_movement,
        ) -> None:
            nonlocal mutated
            if mutated:
                return
            mutated = True
            if target == "package":
                object.__setattr__(empty.package, "package_name", "poison")
            elif target == "movement":
                object.__setattr__(definition_movement, "type_ref", "poison.Type")
            else:
                object.__setattr__(
                    empty.package.definition_index,
                    "root_ref",
                    "sha256:" + "9" * 64,
                )

        with pytest.raises(TypeSchemaTransitionError, match="changed after admission"):
            transition_package(
                empty,
                definition_movements=(definition_movement,),
                attribution_movements=(attribution_movement,),
                reader=store.reader(on_read=mutate),
                request_ref="request:test",
            )
        if target == "package":
            object.__setattr__(empty.package, "package_name", "workflow")
        elif target == "movement":
            object.__setattr__(definition_movement, "type_ref", fragment.type_ref)
        else:
            object.__setattr__(
                empty.package.definition_index,
                "root_ref",
                original_root_ref,
            )
        # A new operation succeeds after rejection, proving the failed
        # operation left no live/stacked private context.
        assert transition_package(
            empty,
            definition_movements=(definition_movement,),
            attribution_movements=(attribution_movement,),
            reader=store.reader(),
            request_ref="request:test",
        ).successor.package_name == "workflow"


def test_source_only_update_and_path_move_preserve_definition_root() -> None:
    store = _Store({})
    initial, fragment, attribution = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    same_path_attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref=initial.successor.package_ref,
        source_path=attribution.source_path,
        document_coordinate_ref="coordinate:workflow:comments-changed",
        bindings=attribution.bindings,
    )
    source_only = transition_package(
        initial.successor,
        definition_movements=(),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                attribution.source_path,
                attribution.to_body().coordinate,
                same_path_attribution,
            ),
        ),
        reader=store.reader(),
        request_ref="request:test",
    )
    assert source_only.definition_lifecycle == ()
    assert source_only.successor.definition_index == initial.successor.definition_index
    store.ingest(source_only.emitted_bodies)

    empty_catalog, catalog_bodies = create_typed_empty_catalog(
        target_package_ref=initial.successor.package_ref
    )
    store.ingest(catalog_bodies)
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=initial.successor.package_ref,
    )
    created = transition_catalog(
        empty_catalog,
        package_movements=(
            PackageRootMovement(
                initial.successor.package_ref,
                None,
                initial.successor,
                initial,
            ),
        ),
        owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
        reader=store.reader(),
        request_ref="request:test",
    )
    store.ingest(created.emitted_bodies)
    prior_package_coordinate, _ = lookup_index_value(
        created.successor.package_index,
        key=initial.successor.package_ref,
        reader=store.reader(),
        request_ref="request:test",
    )
    assert prior_package_coordinate is not None
    source_only_catalog = transition_catalog(
        created.successor,
        package_movements=(
            PackageRootMovement(
                source_only.successor.package_ref,
                prior_package_coordinate,
                source_only.successor,
                source_only,
            ),
        ),
        owner_movements=(),
        reader=store.reader(),
        request_ref="request:test",
    )
    assert source_only_catalog.successor.owner_index == created.successor.owner_index
    assert source_only_catalog.observation.enumeration_attempts == 0
    store.ingest(source_only_catalog.emitted_bodies)

    moved_attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref=source_only.successor.package_ref,
        source_path="workflow/moved.aware",
        document_coordinate_ref="coordinate:workflow:moved",
        bindings=same_path_attribution.bindings,
    )
    path_move = transition_package(
        source_only.successor,
        definition_movements=(),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                same_path_attribution.source_path,
                same_path_attribution.to_body().coordinate,
                None,
            ),
            SourceAttributionFragmentMovement(
                moved_attribution.source_path,
                None,
                moved_attribution,
            ),
        ),
        reader=store.reader(),
        request_ref="request:test",
    )
    assert path_move.definition_lifecycle == ()
    assert path_move.successor.definition_index == initial.successor.definition_index
    store.ingest(path_move.emitted_bodies)
    moved_prior_coordinate, _ = lookup_index_value(
        source_only_catalog.successor.package_index,
        key=source_only.successor.package_ref,
        reader=store.reader(),
        request_ref="request:test",
    )
    assert moved_prior_coordinate is not None
    moved_catalog = transition_catalog(
        source_only_catalog.successor,
        package_movements=(
            PackageRootMovement(
                path_move.successor.package_ref,
                moved_prior_coordinate,
                path_move.successor,
                path_move,
            ),
        ),
        owner_movements=(),
        reader=store.reader(),
        request_ref="request:test",
    )
    assert moved_catalog.successor.owner_index == created.successor.owner_index
    assert moved_catalog.observation.enumeration_attempts == 0
    assert store.writes == 0


def test_delete_uses_prior_attribution_and_requires_no_new_fragment() -> None:
    store = _Store({})
    initial, fragment, attribution = _genesis_package(
        store,
        package_ref="package:content@1.0.0",
        package_name="content",
        dependencies=(),
        fragment=_definition("content.Text"),
    )

    deleted = transition_package(
        initial.successor,
        definition_movements=(
            DefinitionFragmentMovement(
                fragment.type_ref,
                fragment.to_body().coordinate,
                None,
            ),
        ),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                attribution.source_path,
                attribution.to_body().coordinate,
                None,
            ),
        ),
        reader=store.reader(),
        request_ref="request:test",
    )

    assert deleted.successor.definition_index.binding_count == 0
    assert deleted.successor.source_attribution_index.binding_count == 0
    assert all(
        body.coordinate.authority_ref != fragment.fragment_ref
        for body in deleted.emitted_bodies
    )


def test_definition_without_exact_attribution_fails_before_patch() -> None:
    store = _Store({})
    empty, bodies = create_typed_empty_package(
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        namespace="workflow",
        semantic_version="1.0.0",
    )
    store.ingest(bodies)
    fragment = _definition("workflow.Issue")
    with pytest.raises(TypeSchemaTransitionError, match="source-attributed"):
        transition_package(
            empty,
            definition_movements=(
                DefinitionFragmentMovement(fragment.type_ref, None, fragment),
            ),
            attribution_movements=(),
            reader=store.reader(),
            request_ref="request:test",
        )


def test_source_current_package_transition_has_zero_reads_and_outputs() -> None:
    store = _Store({})
    empty, bodies = create_typed_empty_package(
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        namespace="workflow",
        semantic_version="1.0.0",
    )
    store.ingest(bodies)

    current = transition_package(
        empty,
        definition_movements=(),
        attribution_movements=(),
        reader=store.reader(),
        request_ref="request:test",
    )
    second = transition_package(
        empty,
        definition_movements=(),
        attribution_movements=(),
        reader=store.reader(),
        request_ref="request:test",
    )

    assert current.successor == empty.package
    assert current.successor is not empty.package
    assert current.successor is not second.successor
    assert current.prior is not empty
    assert current.prior is not second.prior
    assert isinstance(current.prior, TypeSchemaTypedEmptyPackageAuthority)
    assert current.emitted_bodies == ()
    assert current.reused_coordinates == ()
    assert current.observation.read_count == 0
    object.__setattr__(current.successor, "package_name", "poison")
    assert empty.package.package_name == "workflow"
    assert second.successor.package_name == "workflow"
    assert current.prior.package.package_name == "workflow"

    empty_catalog, catalog_bodies = create_typed_empty_catalog(
        target_package_ref=empty.package.package_ref
    )
    store.ingest(catalog_bodies)
    catalog_current = transition_catalog(
        empty_catalog,
        package_movements=(),
        owner_movements=(),
        reader=store.reader(),
        request_ref="request:test",
    )
    second_catalog_current = transition_catalog(
        empty_catalog,
        package_movements=(),
        owner_movements=(),
        reader=store.reader(),
        request_ref="request:test",
    )
    assert catalog_current.successor is not empty_catalog.catalog
    assert catalog_current.successor is not second_catalog_current.successor
    object.__setattr__(
        catalog_current.successor, "target_package_ref", "package:poison@1.0.0"
    )
    assert empty_catalog.catalog.target_package_ref == empty.package.package_ref
    assert (
        second_catalog_current.successor.target_package_ref
        == empty.package.package_ref
    )


def test_catalog_transition_patches_exact_package_and_owner_bindings() -> None:
    store = _Store({})
    package_result, fragment, _ = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    empty, bodies = create_typed_empty_catalog(
        target_package_ref=package_result.successor.package_ref
    )
    store.ingest(bodies)
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package_result.successor.package_ref,
    )

    result = transition_catalog(
        empty,
        package_movements=(
            PackageRootMovement(
                package_result.successor.package_ref,
                None,
                package_result.successor,
                package_result,
            ),
        ),
        owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
        reader=store.reader(),
        request_ref="request:test",
    )

    assert result.successor.package_count == 1
    assert result.successor.owner_count == 1
    assert result.observation.enumeration_attempts == 0
    assert store.writes == 0
    second = transition_catalog(
        empty,
        package_movements=(
            PackageRootMovement(
                package_result.successor.package_ref,
                None,
                package_result.successor,
                package_result,
            ),
        ),
        owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
        reader=store.reader(),
        request_ref="request:test",
    )
    assert result.successor is not empty.catalog
    assert result.successor is not second.successor
    object.__setattr__(result.successor, "target_package_ref", "package:poison")
    object.__setattr__(result.successor.package_index, "keyspace", "poison")
    assert empty.catalog.target_package_ref == package_result.successor.package_ref
    assert second.successor.target_package_ref == package_result.successor.package_ref
    assert second.successor.package_index.keyspace == "type-schema:catalog:packages"


def test_package_transition_predecessor_is_exact_typed_authority() -> None:
    store = _Store({})
    package_result, _fragment_value, _ = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    foreign_empty, foreign_bodies = create_typed_empty_package(
        package_ref="package:foreign@1.0.0",
        package_name="foreign",
        namespace="foreign",
        semantic_version="1.0.0",
    )
    store.ingest(foreign_bodies)
    semantic = package_result.semantic_wire()
    semantic["prior"] = {
        "kind": "typed_empty",
        "authority": foreign_empty.to_wire(),
    }
    with pytest.raises(TypeSchemaTransitionError, match="predecessor"):
        replace(
            package_result,
            prior=foreign_empty,
            transition_ref=digest_payload(package_result.contract, semantic),
        )


def test_catalog_revalidates_fragment_type_and_source_attribution_lifecycle() -> None:
    store = _Store({})
    package_result, fragment, attribution = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    assert hasattr(package_result.prior, "package")
    empty_package = package_result.prior.package  # type: ignore[union-attr]
    missing_attribution_successor = TypeSchemaPackageRoot.create(
        package_ref=package_result.successor.package_ref,
        package_name=package_result.successor.package_name,
        namespace=package_result.successor.namespace,
        semantic_version=package_result.successor.semantic_version,
        dependency_package_refs=package_result.successor.dependency_package_refs,
        definition_index=package_result.successor.definition_index,
        source_attribution_index=empty_package.source_attribution_index,
    )
    missing_attribution = _forged_transition(
        package_result,
        successor=missing_attribution_successor,
        definition_lifecycle=package_result.definition_lifecycle,
        attribution_lifecycle=(),
        emitted_bodies=(
            *package_result.emitted_bodies,
            missing_attribution_successor.to_body(),
        ),
    )
    empty_catalog, catalog_bodies = create_typed_empty_catalog(
        target_package_ref=package_result.successor.package_ref
    )
    store.ingest(catalog_bodies)
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package_result.successor.package_ref,
    )
    with pytest.raises(TypeSchemaTransitionError, match="binding deltas differ"):
        transition_catalog(
            empty_catalog,
            package_movements=(
                PackageRootMovement(
                    missing_attribution_successor.package_ref,
                    None,
                    missing_attribution_successor,
                    missing_attribution,
                ),
            ),
            owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
            reader=store.reader(),
            request_ref="request:test",
        )

    foreign_fragment = _definition("other.Type")
    foreign_body = foreign_fragment.to_body()
    definition_patch = patch_persistent_index(
        package_result.successor.definition_index,
        movements=(
            IndexBindingMovement(
                fragment.type_ref,
                fragment.to_body().coordinate,
                foreign_body.coordinate,
            ),
        ),
        reader=store.reader(),
        request_ref="request:test",
    )
    substituted_attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref=package_result.successor.package_ref,
        source_path=attribution.source_path,
        document_coordinate_ref="coordinate:substituted",
        bindings=(SourceDefinitionBinding(fragment.type_ref, foreign_body.coordinate),),
    )
    attribution_patch = patch_persistent_index(
        package_result.successor.source_attribution_index,
        movements=(
            IndexBindingMovement(
                attribution.source_path,
                attribution.to_body().coordinate,
                substituted_attribution.to_body().coordinate,
            ),
        ),
        reader=store.reader(),
        request_ref="request:test",
    )
    store.ingest(
        (
            foreign_body,
            substituted_attribution.to_body(),
            *definition_patch.emitted_bodies,
            *attribution_patch.emitted_bodies,
        )
    )
    foreign_successor = TypeSchemaPackageRoot.create(
        package_ref=package_result.successor.package_ref,
        package_name=package_result.successor.package_name,
        namespace=package_result.successor.namespace,
        semantic_version=package_result.successor.semantic_version,
        dependency_package_refs=package_result.successor.dependency_package_refs,
        definition_index=definition_patch.root,
        source_attribution_index=attribution_patch.root,
    )
    foreign_transition = _forged_transition(
        package_result,
        successor=foreign_successor,
        definition_lifecycle=(
            TypeDefinitionLifecycleEvidence.create(
                type_ref=fragment.type_ref,
                prior=None,
                next=foreign_body.coordinate,
            ),
        ),
        attribution_lifecycle=(
            SourceAttributionLifecycleEvidence.create(
                source_path=attribution.source_path,
                prior=None,
                next=substituted_attribution.to_body().coordinate,
            ),
        ),
        emitted_bodies=(
            foreign_body,
            substituted_attribution.to_body(),
            *definition_patch.emitted_bodies,
            *attribution_patch.emitted_bodies,
            foreign_successor.to_body(),
        ),
    )
    with pytest.raises(TypeSchemaTransitionError, match="fragment type_ref"):
        transition_catalog(
            empty_catalog,
            package_movements=(
                PackageRootMovement(
                    foreign_successor.package_ref,
                    None,
                    foreign_successor,
                    foreign_transition,
                ),
            ),
            owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
            reader=store.reader(),
            request_ref="request:test",
        )

    package_root_predecessor = replace(
        package_result,
        prior=package_result.successor,
        transition_ref=digest_payload(
            package_result.contract,
            {
                **package_result.semantic_wire(),
                "prior": {
                    "kind": "package_root",
                    "authority": package_result.successor.to_wire(),
                },
            },
        ),
    )
    empty_catalog, bodies = create_typed_empty_catalog(
        target_package_ref=package_result.successor.package_ref
    )
    store.ingest(bodies)
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package_result.successor.package_ref,
    )
    with pytest.raises(TypeSchemaTransitionError, match="typed-empty predecessor"):
        transition_catalog(
            empty_catalog,
            package_movements=(
                PackageRootMovement(
                    package_result.successor.package_ref,
                    None,
                    package_result.successor,
                    package_root_predecessor,
                ),
            ),
            owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
            reader=store.reader(),
            request_ref="request:test",
        )


def test_catalog_rejects_missing_or_extra_owner_lifecycle() -> None:
    store = _Store({})
    package_result, fragment, _ = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    empty, bodies = create_typed_empty_catalog(
        target_package_ref=package_result.successor.package_ref
    )
    store.ingest(bodies)
    package_movement = PackageRootMovement(
        package_result.successor.package_ref,
        None,
        package_result.successor,
        package_result,
    )
    with pytest.raises(TypeSchemaTransitionError, match="lifecycle and owner"):
        transition_catalog(
            empty,
            package_movements=(package_movement,),
            owner_movements=(),
            reader=store.reader(),
            request_ref="request:test",
        )

    absent_owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref="package:absent@1.0.0",
    )
    with pytest.raises(TypeSchemaTransitionError, match="lifecycle and owner"):
        transition_catalog(
            empty,
            package_movements=(),
            owner_movements=(
                TypeOwnerBindingMovement(fragment.type_ref, None, absent_owner),
            ),
            reader=store.reader(),
            request_ref="request:test",
        )


def test_catalog_rejects_disconnected_package_successor() -> None:
    store = _Store({})
    target, target_bodies = create_typed_empty_package(
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        namespace="workflow",
        semantic_version="1.0.0",
    )
    extra, extra_bodies = create_typed_empty_package(
        package_ref="package:extra@1.0.0",
        package_name="extra",
        namespace="extra",
        semantic_version="1.0.0",
    )
    store.ingest((*target_bodies, *extra_bodies))
    target_transition = transition_package(
        target,
        definition_movements=(),
        attribution_movements=(),
        reader=store.reader(),
        request_ref="request:test",
    )
    extra_transition = transition_package(
        extra,
        definition_movements=(),
        attribution_movements=(),
        reader=store.reader(),
        request_ref="request:test",
    )
    catalog, catalog_bodies = create_typed_empty_catalog(
        target_package_ref=target.package.package_ref
    )
    store.ingest(catalog_bodies)

    with pytest.raises(TypeSchemaTransitionError, match="outside target-reachable"):
        transition_catalog(
            catalog,
            package_movements=(
                PackageRootMovement(
                    target.package.package_ref,
                    None,
                    target.package,
                    target_transition,
                ),
                PackageRootMovement(
                    extra.package.package_ref,
                    None,
                    extra.package,
                    extra_transition,
                ),
            ),
            owner_movements=(),
            reader=store.reader(),
            request_ref="request:test",
        )


def test_catalog_rejects_incomplete_package_deletion_and_target_deletion() -> None:
    store = _Store({})
    package_result, fragment, _ = _genesis_package(
        store,
        package_ref="package:workflow@1.0.0",
        package_name="workflow",
        dependencies=(),
        fragment=_definition("workflow.Issue"),
    )
    empty, bodies = create_typed_empty_catalog(
        target_package_ref=package_result.successor.package_ref
    )
    store.ingest(bodies)
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package_result.successor.package_ref,
    )
    created = transition_catalog(
        empty,
        package_movements=(
            PackageRootMovement(
                package_result.successor.package_ref,
                None,
                package_result.successor,
                package_result,
            ),
        ),
        owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
        reader=store.reader(),
        request_ref="request:test",
    )
    store.ingest(created.emitted_bodies)
    package_coordinate, _ = lookup_index_value(
        created.successor.package_index,
        key=package_result.successor.package_ref,
        reader=store.reader(),
        request_ref="request:test",
    )
    owner_coordinate, _ = lookup_index_value(
        created.successor.owner_index,
        key=fragment.type_ref,
        reader=store.reader(),
        request_ref="request:test",
    )
    assert package_coordinate is not None
    assert owner_coordinate is not None

    deletion = PackageRootMovement(
        package_result.successor.package_ref,
        package_coordinate,
        None,
        None,
    )
    with pytest.raises(TypeSchemaTransitionError, match="every owned definition"):
        transition_catalog(
            created.successor,
            package_movements=(deletion,),
            owner_movements=(),
            reader=store.reader(),
            request_ref="request:test",
        )
    with pytest.raises(TypeSchemaTransitionError, match="successor package is deleted"):
        transition_catalog(
            created.successor,
            package_movements=(deletion,),
            owner_movements=(
                TypeOwnerBindingMovement(fragment.type_ref, owner_coordinate, None),
            ),
            reader=store.reader(),
            request_ref="request:test",
        )
