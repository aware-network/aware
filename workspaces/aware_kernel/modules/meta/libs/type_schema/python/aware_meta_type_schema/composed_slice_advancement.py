"""Meta-owned incremental advancement of admitted composed type slices."""

from __future__ import annotations

import copy
import hashlib
import weakref
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, cast

from .composition import (
    ComposedPackageEvidence,
    TypeOwnerBinding,
    TypeSchemaCatalogRoot,
    TypeSchemaComposedSlice,
    TypeSchemaPackageRoot,
    _create_prevalidated_composed_slice,
    _prevalidated_owner_evidence,
    _prevalidated_package_evidence,
    _take_prevalidated_composed_slice_bytes,
)
from .composition_codec import (
    decode_catalog_root,
    decode_composed_slice,
    decode_package_root,
    encode_composition_value,
)
from .composition_transition import (
    PackageRootMovement,
    SourceAttributionLifecycleEvidence,
    TypeDefinitionLifecycleEvidence,
    TypeSchemaCatalogTransition,
    TypeSchemaPackageTransition,
    transition_catalog,
)
from .encoding import digest_payload
from .persistent_index import (
    PersistentBodyAuthority,
    PersistentBodyCoordinate,
    PersistentIndexRoot,
    TypeSchemaPersistentIndexError,
    _meta_type_schema_operation,
    _MetaTypeSchemaOperationContext,
    _require_meta_type_schema_operation,
    _require_meta_type_schema_operation_operands,
)
from .positive_reader import (
    PersistentIndexMembershipProof,
    PositiveReadObservation,
    TypeSchemaPositiveReaderCapability,
    _admit_validated_proof_bundle,
    _AdmittedPersistentIndexProofBundle,
    _advance_admitted_proof_bundle,
    _prove_index_membership,
)


class TypeSchemaComposedSliceAdvancementError(ValueError):
    """Raised when incremental advancement must fail closed."""

    code = "full_resolution_required"


class AdmittedTypeSchemaComposedSlice:
    """Opaque execution-local admission for one strict composed-slice body."""

    __slots__ = ("__weakref__",)


@dataclass(frozen=True, slots=True)
class TypeSchemaComposedSliceAdvancementResult:
    slice: TypeSchemaComposedSlice
    observation: PositiveReadObservation
    prior_slice_ref: str
    successor_slice_ref: str
    prior_catalog_ref: str
    successor_catalog_ref: str
    changed_package_refs: tuple[str, ...]
    fresh_membership_count: int
    retained_membership_count: int
    fresh_node_count: int
    retained_node_count: int


@dataclass(frozen=True, slots=True)
class _SliceAdmissionContext:
    slice: TypeSchemaComposedSlice
    canonical_bytes: bytes
    canonical_digest: str
    proof_admission: _AdmittedPersistentIndexProofBundle


_SLICE_ADMISSIONS: dict[
    int,
    tuple[
        weakref.ReferenceType[AdmittedTypeSchemaComposedSlice],
        _SliceAdmissionContext,
    ],
] = {}
_PREVALIDATED_SLICE_ADMISSION_TOKEN = object()


_PREFLIGHT_TYPES = {
    PackageRootMovement,
    PersistentBodyAuthority,
    PersistentBodyCoordinate,
    PersistentIndexRoot,
    PositiveReadObservation,
    SourceAttributionLifecycleEvidence,
    TypeDefinitionLifecycleEvidence,
    TypeSchemaCatalogRoot,
    TypeSchemaCatalogTransition,
    TypeSchemaPackageRoot,
    TypeSchemaPackageTransition,
}


def admit_composed_slice(
    canonical_bytes: bytes,
) -> AdmittedTypeSchemaComposedSlice:
    """Strictly decode and nominally admit one stable composed-slice body."""

    if type(canonical_bytes) is not bytes:
        raise TypeError("composed slice admission requires exact bytes")
    value = decode_composed_slice(canonical_bytes)
    if encode_composition_value(value) != canonical_bytes:
        raise TypeSchemaComposedSliceAdvancementError(
            "composed slice admission bytes are not canonical"
        )
    return _admit_prevalidated_composed_slice(
        value,
        canonical_bytes,
        _token=_PREVALIDATED_SLICE_ADMISSION_TOKEN,
    )


def _admit_prevalidated_composed_slice(
    value: TypeSchemaComposedSlice,
    canonical_bytes: bytes,
    *,
    _token: object,
    _proof_bundle_token: object | None = None,
) -> AdmittedTypeSchemaComposedSlice:
    """Admit exact bytes emitted by the active Meta owner operation."""

    if _token is not _PREVALIDATED_SLICE_ADMISSION_TOKEN:
        raise TypeSchemaComposedSliceAdvancementError(
            "prevalidated composed slice admission lacks Meta authority"
        )
    if type(value) is not TypeSchemaComposedSlice or type(canonical_bytes) is not bytes:
        raise TypeError("prevalidated composed slice evidence must be exact")
    admission = AdmittedTypeSchemaComposedSlice()
    admission_id = id(admission)

    def discard(
        reference: weakref.ReferenceType[AdmittedTypeSchemaComposedSlice],
        *,
        retained_id: int = admission_id,
    ) -> None:
        retained = _SLICE_ADMISSIONS.get(retained_id)
        if retained is not None and retained[0] is reference:
            _SLICE_ADMISSIONS.pop(retained_id, None)

    reference = weakref.ref(admission, discard)
    _SLICE_ADMISSIONS[admission_id] = (
        reference,
        _SliceAdmissionContext(
            slice=value,
            canonical_bytes=canonical_bytes,
            canonical_digest="sha256:" + hashlib.sha256(canonical_bytes).hexdigest(),
            proof_admission=_admit_validated_proof_bundle(
                value.membership_proofs,
                _token=_proof_bundle_token,
            ),
        ),
    )
    return admission


def advance_attribution_only_composed_slice(
    admission: AdmittedTypeSchemaComposedSlice,
    *,
    catalog_transition: TypeSchemaCatalogTransition,
    successor_catalog: TypeSchemaCatalogRoot,
    package_movements: tuple[PackageRootMovement, ...],
    package_transitions: tuple[TypeSchemaPackageTransition, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    _operation_context: object | None = None,
) -> TypeSchemaComposedSliceAdvancementResult:
    _slice_admission_context(admission)
    if type(reader) is not TypeSchemaPositiveReaderCapability:
        raise TypeSchemaComposedSliceAdvancementError(
            "reader must be exact TypeSchemaPositiveReaderCapability"
        )
    if (
        type(request_ref) is not str
        or not request_ref
        or request_ref.strip() != request_ref
    ):
        raise TypeSchemaComposedSliceAdvancementError(
            "request_ref must be normalized text"
        )
    retained_request_ref = object.__getattribute__(reader, "_request_ref")
    if type(retained_request_ref) is not str:
        raise TypeSchemaComposedSliceAdvancementError(
            "reader request_ref is not exact normalized text"
        )
    if retained_request_ref != request_ref:
        raise TypeSchemaComposedSliceAdvancementError(
            "reader capability belongs to another request"
        )
    _preflight_meta_value(catalog_transition)
    _preflight_meta_value(successor_catalog)
    _preflight_meta_value(package_movements)
    _preflight_meta_value(package_transitions)
    operands = (
        admission,
        catalog_transition,
        successor_catalog,
        package_movements,
        package_transitions,
    )
    with _meta_type_schema_operation(
        operation_ref="composition.advance-attribution",
        operands=operands,
        reader=reader,
        request_ref=request_ref,
    ) as operation_context:
        result = _advance_attribution_only_composed_slice(
            operation_context,
            admission,
            catalog_transition=catalog_transition,
            successor_catalog=successor_catalog,
            package_movements=package_movements,
            package_transitions=package_transitions,
            reader=reader,
            request_ref=request_ref,
        )
        try:
            _require_meta_type_schema_operation_operands(
                operation_context,
                operation_ref="composition.advance-attribution",
                operands=operands,
            )
        except TypeSchemaPersistentIndexError as error:
            raise TypeSchemaComposedSliceAdvancementError(
                f"advancement operands changed after admission: {error}"
            ) from error
    successor_canonical_bytes = _take_prevalidated_composed_slice_bytes(result.slice)
    if _operation_context is not None:
        from .type_schema_operation import _record_type_schema_composed_slice

        _record_type_schema_composed_slice(
            _operation_context,  # pyright: ignore[reportArgumentType]
            result.slice,
            successor_canonical_bytes,
        )
    return result


def _advance_attribution_only_composed_slice(
    operation_context: _MetaTypeSchemaOperationContext,
    admission: AdmittedTypeSchemaComposedSlice,
    *,
    catalog_transition: TypeSchemaCatalogTransition,
    successor_catalog: TypeSchemaCatalogRoot,
    package_movements: tuple[PackageRootMovement, ...],
    package_transitions: tuple[TypeSchemaPackageTransition, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
) -> TypeSchemaComposedSliceAdvancementResult:
    """Advance an admitted slice through exact attribution-only movements."""

    _require_meta_type_schema_operation(operation_context)
    context = _slice_admission_context(admission)
    if type(reader) is not TypeSchemaPositiveReaderCapability:
        raise TypeSchemaComposedSliceAdvancementError(
            "reader must be exact TypeSchemaPositiveReaderCapability"
        )
    if (
        type(request_ref) is not str
        or not request_ref
        or request_ref.strip() != request_ref
    ):
        raise TypeSchemaComposedSliceAdvancementError(
            "request_ref must be normalized text"
        )
    retained_request_ref = object.__getattribute__(reader, "_request_ref")
    if (
        type(retained_request_ref) is not str
        or not retained_request_ref
        or retained_request_ref.strip() != retained_request_ref
    ):
        raise TypeSchemaComposedSliceAdvancementError(
            "reader request_ref is not exact normalized text"
        )
    if retained_request_ref != request_ref:
        raise TypeSchemaComposedSliceAdvancementError(
            "reader capability belongs to another request"
        )
    _preflight_meta_value(catalog_transition)
    _preflight_meta_value(successor_catalog)
    _preflight_meta_value(package_movements)
    _preflight_meta_value(package_transitions)
    strict_successor_catalog = _require_strict_catalog_root(successor_catalog)
    strict_successor_package_by_ref: dict[str, TypeSchemaPackageRoot] = {}
    for movement in package_movements:
        if movement.next is not None:
            strict_successor_package_by_ref[movement.package_ref] = (
                _require_strict_package_root(movement.next)
            )
    for transition in package_transitions:
        if type(transition.prior) is not TypeSchemaPackageRoot:
            raise TypeSchemaComposedSliceAdvancementError(
                "incremental transition requires exact package predecessor"
            )
        _require_strict_package_root(transition.prior)
        _require_strict_package_root(transition.successor)
        _require_strict_package_transition(transition)

    if type(package_movements) is not tuple or package_movements != tuple(
        sorted(package_movements, key=lambda value: value.package_ref)
    ):
        raise TypeSchemaComposedSliceAdvancementError(
            "package movements must be exact package-ref order"
        )
    if not package_movements or len(
        {value.package_ref for value in package_movements}
    ) != len(package_movements):
        raise TypeSchemaComposedSliceAdvancementError(
            "package movements must be nonempty and unique"
        )
    if type(package_transitions) is not tuple or len(
        {value.transition_ref for value in package_transitions}
    ) != len(package_transitions):
        raise TypeSchemaComposedSliceAdvancementError(
            "package transitions must be exact and unique"
        )

    prior = context.slice
    if (
        catalog_transition.prior_ref != prior.catalog_ref
        or catalog_transition.successor != successor_catalog
        or successor_catalog.target_package_ref != prior.target_package_ref
        or successor_catalog.owner_index != prior.catalog.owner_index
        or successor_catalog.package_count != prior.catalog.package_count
        or successor_catalog.owner_count != prior.catalog.owner_count
        or catalog_transition.owner_movement_refs
    ):
        raise TypeSchemaComposedSliceAdvancementError(
            "catalog transition is not attribution-only"
        )

    prior_packages = {value.package_ref: value for value in prior.packages}
    movement_by_ref = {value.package_ref: value for value in package_movements}
    if not set(movement_by_ref).issubset(prior_packages):
        raise TypeSchemaComposedSliceAdvancementError(
            "package movement is outside admitted slice"
        )
    transition_by_ref = {
        value.successor.package_ref: value for value in package_transitions
    }
    if set(transition_by_ref) != set(movement_by_ref):
        raise TypeSchemaComposedSliceAdvancementError(
            "package transition closure differs from movements"
        )
    _require_dependency_first(package_transitions, set(movement_by_ref))

    movement_refs: list[str] = []
    successor_package_by_ref = {
        value.package_ref: _require_strict_package_root(value.package)
        for value in prior.packages
    }
    for package_ref, movement in movement_by_ref.items():
        prior_evidence = prior_packages[package_ref]
        transition = transition_by_ref[package_ref]
        if (
            movement.prior != prior_evidence.coordinate
            or movement.next is None
            or movement.transition is None
            or movement.transition.transition_ref != transition.transition_ref
            or transition.prior != prior_evidence.package
            or transition.successor != movement.next
        ):
            raise TypeSchemaComposedSliceAdvancementError(
                "package transition does not bind admitted predecessor"
            )
        _require_attribution_only(prior_evidence.package, movement.next, transition)
        successor_package_by_ref[package_ref] = strict_successor_package_by_ref[
            package_ref
        ]
        movement_refs.append(_package_movement_ref(movement))
    if tuple(sorted(movement_refs)) != catalog_transition.package_movement_refs:
        raise TypeSchemaComposedSliceAdvancementError(
            "catalog package movement refs are incomplete"
        )

    freshly_derived = transition_catalog(
        prior.catalog,
        package_movements=package_movements,
        owner_movements=(),
        reader=reader,
        request_ref=request_ref,
    )
    if (
        freshly_derived.transition_ref != catalog_transition.transition_ref
        or freshly_derived.successor != successor_catalog
        or freshly_derived.semantic_wire() != catalog_transition.semantic_wire()
    ):
        raise TypeSchemaComposedSliceAdvancementError(
            "catalog transition differs from fresh contextual derivation"
        )

    expected_package_refs = {
        prior.target_package_ref,
        *prior.dependency_package_refs,
    }
    if set(successor_package_by_ref) != expected_package_refs:
        raise TypeSchemaComposedSliceAdvancementError(
            "successor package closure differs from admitted slice"
        )

    observation = freshly_derived.observation
    fresh_memberships: list[PersistentIndexMembershipProof] = []
    fresh_nodes_by_ref = {}
    successor_packages: list[ComposedPackageEvidence] = []
    for package_ref in sorted(successor_package_by_ref):
        package = successor_package_by_ref[package_ref]
        proof, nodes, read_observation = _prove_index_membership(
            operation_context,
            strict_successor_catalog.package_index,
            key=package_ref,
            reader=reader,
            request_ref=request_ref,
        )
        observation = observation.plus(read_observation)
        coordinate = package.to_body().coordinate
        if proof is None or proof.value != coordinate:
            raise TypeSchemaComposedSliceAdvancementError(
                "successor package membership differs from exact package"
            )
        fresh_memberships.append(proof)
        fresh_nodes_by_ref.update((value.node_ref, value) for value in nodes)
        successor_packages.append(
            _prevalidated_package_evidence(operation_context, package, coordinate)
        )

    retained_root_refs = {strict_successor_catalog.owner_index.root_ref}
    retained_root_refs.update(
        value.definition_index.root_ref for value in successor_package_by_ref.values()
    )
    retained_memberships = tuple(
        value
        for value in prior.membership_proofs.memberships
        if value.root.root_ref in retained_root_refs
    )
    expected_retained_count = len(prior.owners) + len(prior.definitions)
    if len(retained_memberships) != expected_retained_count:
        raise TypeSchemaComposedSliceAdvancementError(
            "admitted retained proof closure is incomplete"
        )
    retained_refs = tuple(
        sorted(value.membership_ref for value in retained_memberships)
    )
    proof_bundle = _advance_admitted_proof_bundle(
        operation_context,
        context.proof_admission,
        retained_membership_refs=retained_refs,
        fresh_memberships=tuple(fresh_memberships),
        fresh_nodes=tuple(fresh_nodes_by_ref.values()),
    )

    package_coordinate_by_ref = {
        value.package_ref: value.coordinate for value in successor_packages
    }
    successor_owners = tuple(
        _prevalidated_owner_evidence(
            operation_context,
            TypeOwnerBinding.create(
                type_ref=value.type_ref,
                package_ref=value.package_ref,
            ),
            _strict_coordinate(value.owner),
            package_coordinate_by_ref[value.package_ref],
            _strict_coordinate(value.definition),
        )
        for value in prior.owners
    )
    successor_definitions = tuple(copy.deepcopy(value) for value in prior.definitions)
    successor_slice = _create_prevalidated_composed_slice(
        operation_context,
        catalog=strict_successor_catalog,
        target_package_ref=prior.target_package_ref,
        dependency_package_refs=prior.dependency_package_refs,
        root_type_refs=prior.root_type_refs,
        packages=tuple(successor_packages),
        definitions=successor_definitions,
        owners=successor_owners,
        membership_proofs=proof_bundle,
    )
    fresh_node_refs = {value.node_ref for value in fresh_nodes_by_ref.values()}
    retained_node_refs = {
        node_ref for value in retained_memberships for node_ref in value.node_refs
    } - fresh_node_refs
    return TypeSchemaComposedSliceAdvancementResult(
        slice=successor_slice,
        observation=observation,
        prior_slice_ref=prior.slice_ref,
        successor_slice_ref=successor_slice.slice_ref,
        prior_catalog_ref=prior.catalog_ref,
        successor_catalog_ref=strict_successor_catalog.catalog_ref,
        changed_package_refs=tuple(sorted(movement_by_ref)),
        fresh_membership_count=len(fresh_memberships),
        retained_membership_count=len(retained_memberships),
        fresh_node_count=len(fresh_node_refs),
        retained_node_count=len(retained_node_refs),
    )


def _slice_admission_context(
    admission: AdmittedTypeSchemaComposedSlice,
) -> _SliceAdmissionContext:
    if type(admission) is not AdmittedTypeSchemaComposedSlice:
        raise TypeSchemaComposedSliceAdvancementError(
            "composed slice admission is not exact"
        )
    retained = _SLICE_ADMISSIONS.get(id(admission))
    if retained is None or retained[0]() is not admission:
        raise TypeSchemaComposedSliceAdvancementError(
            "composed slice admission is not active"
        )
    context = retained[1]
    if (
        "sha256:" + hashlib.sha256(context.canonical_bytes).hexdigest()
        != context.canonical_digest
    ):
        raise TypeSchemaComposedSliceAdvancementError(
            "composed slice admission context changed"
        )
    return context


def _require_prevalidated_composed_slice_admission(
    admission: AdmittedTypeSchemaComposedSlice,
    value: TypeSchemaComposedSlice,
    canonical_bytes: bytes,
) -> None:
    """Verify exact Meta-owned successor evidence without re-encoding it."""

    if type(value) is not TypeSchemaComposedSlice or type(canonical_bytes) is not bytes:
        raise TypeSchemaComposedSliceAdvancementError(
            "composed slice verification evidence is not exact"
        )
    retained = _slice_admission_context(admission)
    if retained.slice is not value or retained.canonical_bytes != canonical_bytes:
        raise TypeSchemaComposedSliceAdvancementError(
            "composed slice admission differs from exact successor"
        )


def _require_dependency_first(
    transitions: tuple[TypeSchemaPackageTransition, ...],
    changed_refs: set[str],
) -> None:
    seen: set[str] = set()
    for transition in transitions:
        package_ref = transition.successor.package_ref
        if any(
            dependency in changed_refs and dependency not in seen
            for dependency in transition.successor.dependency_package_refs
        ):
            raise TypeSchemaComposedSliceAdvancementError(
                "package transitions are not dependency-first"
            )
        seen.add(package_ref)


def _require_attribution_only(
    prior: TypeSchemaPackageRoot,
    successor: TypeSchemaPackageRoot,
    transition: TypeSchemaPackageTransition,
) -> None:
    if (
        prior.package_ref != successor.package_ref
        or prior.package_name != successor.package_name
        or prior.namespace != successor.namespace
        or prior.semantic_version != successor.semantic_version
        or prior.dependency_package_refs != successor.dependency_package_refs
        or prior.definition_index != successor.definition_index
        or not transition.attribution_lifecycle
        or not transition.attribution_movement_refs
        or transition.definition_lifecycle
        or transition.definition_movement_refs
        or prior.source_attribution_index == successor.source_attribution_index
    ):
        raise TypeSchemaComposedSliceAdvancementError(
            "package transition is not attribution-only"
        )


def _package_movement_ref(movement: PackageRootMovement) -> str:
    if movement.next is None:
        raise TypeSchemaComposedSliceAdvancementError(
            "attribution advancement cannot delete package"
        )
    next_coordinate = movement.next.to_body().coordinate
    return digest_payload(
        "aware.meta.type-schema.package-root-movement.v1",
        {
            "package_ref": movement.package_ref,
            "prior": None if movement.prior is None else movement.prior.to_wire(),
            "next": next_coordinate.to_wire(),
        },
    )


def _require_strict_catalog_root(
    value: TypeSchemaCatalogRoot,
) -> TypeSchemaCatalogRoot:
    try:
        decoded = decode_catalog_root(encode_composition_value(value))
    except (TypeError, ValueError) as error:
        raise TypeSchemaComposedSliceAdvancementError(
            f"successor catalog is not strict: {error}"
        ) from error
    if decoded != value:
        raise TypeSchemaComposedSliceAdvancementError(
            "successor catalog differs from strict reconstruction"
        )
    return decoded


def _require_strict_package_root(
    value: TypeSchemaPackageRoot,
) -> TypeSchemaPackageRoot:
    try:
        decoded = decode_package_root(encode_composition_value(value))
    except (TypeError, ValueError) as error:
        raise TypeSchemaComposedSliceAdvancementError(
            f"package root is not strict: {error}"
        ) from error
    if decoded != value:
        raise TypeSchemaComposedSliceAdvancementError(
            "package root differs from strict reconstruction"
        )
    return decoded


def _require_strict_package_transition(
    value: TypeSchemaPackageTransition,
) -> None:
    try:
        prior = value.prior
        if type(prior) is not TypeSchemaPackageRoot:
            raise TypeSchemaComposedSliceAdvancementError(
                "incremental transition predecessor is not package root"
            )
        definition_lifecycle = tuple(
            TypeDefinitionLifecycleEvidence(
                item.type_ref,
                None if item.prior is None else _strict_coordinate(item.prior),
                None if item.next is None else _strict_coordinate(item.next),
                item.lifecycle_ref,
            )
            for item in value.definition_lifecycle
        )
        attribution_lifecycle = tuple(
            SourceAttributionLifecycleEvidence(
                item.source_path,
                None if item.prior is None else _strict_coordinate(item.prior),
                None if item.next is None else _strict_coordinate(item.next),
                item.lifecycle_ref,
            )
            for item in value.attribution_lifecycle
        )
        emitted_bodies = tuple(
            PersistentBodyAuthority(
                _strict_coordinate(item.coordinate),
                item.canonical_bytes,
            )
            for item in value.emitted_bodies
        )
        reused_coordinates = tuple(
            _strict_coordinate(item) for item in value.reused_coordinates
        )
        rebuilt = TypeSchemaPackageTransition(
            prior=decode_package_root(encode_composition_value(prior)),
            successor=decode_package_root(encode_composition_value(value.successor)),
            definition_lifecycle=definition_lifecycle,
            attribution_lifecycle=attribution_lifecycle,
            definition_movement_refs=value.definition_movement_refs,
            attribution_movement_refs=value.attribution_movement_refs,
            emitted_bodies=emitted_bodies,
            reused_coordinates=reused_coordinates,
            transition_ref=value.transition_ref,
            observation=PositiveReadObservation(
                read_count=value.observation.read_count,
                read_bytes=value.observation.read_bytes,
                cache_hits=value.observation.cache_hits,
                max_lookup_depth=value.observation.max_lookup_depth,
                elapsed_ns=value.observation.elapsed_ns,
                enumeration_attempts=value.observation.enumeration_attempts,
            ),
            contract=value.contract,
        )
    except (TypeError, ValueError) as error:
        if isinstance(error, TypeSchemaComposedSliceAdvancementError):
            raise
        raise TypeSchemaComposedSliceAdvancementError(
            f"package transition is not strict: {error}"
        ) from error
    if rebuilt != value:
        raise TypeSchemaComposedSliceAdvancementError(
            "package transition differs from strict reconstruction"
        )


def _strict_coordinate(value: PersistentBodyCoordinate) -> PersistentBodyCoordinate:
    return PersistentBodyCoordinate(
        schema=value.schema,
        ref_field=value.ref_field,
        authority_ref=value.authority_ref,
        body_ref=value.body_ref,
        body_digest=value.body_digest,
        size_bytes=value.size_bytes,
        coordinate_ref=value.coordinate_ref,
        contract=value.contract,
    )


def _preflight_meta_value(value: object) -> None:
    value_type = type(value)
    if value is None or value_type in {str, int, bool, bytes}:
        return
    if value_type is tuple:
        for item in cast(tuple[object, ...], value):
            _preflight_meta_value(item)
        return
    if value_type not in _PREFLIGHT_TYPES or not is_dataclass(value):
        raise TypeSchemaComposedSliceAdvancementError(
            f"foreign Meta value rejected before behavior: {value_type.__name__}"
        )
    for field in fields(cast(Any, value)):
        _preflight_meta_value(object.__getattribute__(value, field.name))


__all__ = [
    "AdmittedTypeSchemaComposedSlice",
    "TypeSchemaComposedSliceAdvancementError",
    "TypeSchemaComposedSliceAdvancementResult",
    "admit_composed_slice",
    "advance_attribution_only_composed_slice",
]
