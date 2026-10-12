"""Zero-write package and catalog successor transitions."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, fields
from enum import Enum
from time import perf_counter_ns
from typing import Any, cast

from .composition import (
    TypeOwnerBinding,
    TypeSchemaCatalogRoot,
    TypeSchemaPackageRoot,
    _create_prevalidated_catalog_root,
    _create_prevalidated_package_root,
)
from .definition_fragment import (
    SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT,
    TYPE_DEFINITION_FRAGMENT_CONTRACT,
    TypeDefinitionFragment,
    TypeSchemaSourceAttributionFragment,
)
from .encoding import digest_payload
from .persistent_index import (
    PersistentBodyAuthority,
    PersistentBodyCoordinate,
    PersistentIndexNode,
    PersistentIndexRoot,
    TypeSchemaPersistentIndexError,
    _admit_and_detach_exact_graph,
    _create_prevalidated_body_authority,
    _flat_protected_operand_guard,
    _meta_type_schema_operation,
    _MetaTypeSchemaOperationContext,
    _prevalidated_digest,
    _prevalidated_json,
    _require_meta_type_schema_operation,
    _require_meta_type_schema_operation_operands,
    create_empty_persistent_index,
)
from .positive_reader import (
    IndexBindingMovement,
    PositiveReadObservation,
    TypeSchemaPositiveReaderCapability,
    _lookup_index_value_with_context,
    _OperationDecodedNodeArena,
    _patch_persistent_index_with_context,
)


def _prevalidated_transition_semantic_bytes(
    semantic: dict[str, object],
    *,
    emitted_bodies: tuple[PersistentBodyAuthority, ...],
    reused_coordinates: tuple[PersistentBodyCoordinate, ...],
    decoded_nodes: object,
) -> bytes:
    """Insert owner-retained coordinate wires into one transition body."""

    emitted_marker = "__aware_meta_emitted_coordinate_wires__"
    reused_marker = "__aware_meta_reused_coordinate_wires__"
    semantic["emitted_bodies"] = emitted_marker
    semantic["reused_coordinates"] = reused_marker
    template = _prevalidated_json(semantic)
    arena = (
        decoded_nodes
        if type(decoded_nodes) is _OperationDecodedNodeArena
        else None
    )

    def coordinate_wire(
        coordinate: PersistentBodyCoordinate,
        canonical_bytes: bytes | None,
    ) -> bytes:
        retained = (
            None
            if arena is None
            else arena.body_fragments.get(coordinate.coordinate_ref)
        )
        values = (
            coordinate.schema,
            coordinate.ref_field,
            coordinate.authority_ref,
            coordinate.body_ref,
            coordinate.body_digest,
            coordinate.size_bytes,
            coordinate.coordinate_ref,
            coordinate.contract,
        )
        if (
            retained is not None
            and retained[0] == values
            and (canonical_bytes is None or retained[1] == canonical_bytes)
        ):
            wire = retained[2]
        else:
            wire = _prevalidated_json(coordinate.to_wire())
        if arena is not None:
            arena.coordinate_wires[id(coordinate)] = (coordinate, wire)
        return wire

    emitted_bytes = b"[" + b",".join(
        coordinate_wire(body.coordinate, body.canonical_bytes)
        for body in emitted_bodies
    ) + b"]"
    reused_bytes = b"[" + b",".join(
        coordinate_wire(coordinate, None) for coordinate in reused_coordinates
    ) + b"]"
    encoded_emitted = b'"' + emitted_marker.encode("ascii") + b'"'
    encoded_reused = b'"' + reused_marker.encode("ascii") + b'"'
    if template.count(encoded_emitted) != 1 or template.count(encoded_reused) != 1:
        raise AssertionError("transition coordinate marker must be unique")
    return template.replace(encoded_emitted, emitted_bytes, 1).replace(
        encoded_reused, reused_bytes, 1
    )


def _detach_exact_admitted_graph(value: object) -> object:
    """Detach an already recursively admitted Meta operand without codecs."""

    memo: dict[int, object] = {}

    def detach(item: object) -> object:
        item_type = type(item)
        if item is None or item_type in (str, int, bool, float, bytes):
            return item
        if isinstance(item, Enum):
            return item
        identity = id(item)
        retained = memo.get(identity)
        if retained is not None:
            return retained
        if item_type is tuple:
            result = tuple(detach(child) for child in cast(tuple[object, ...], item))
            memo[identity] = result
            return result
        if item_type is list:
            result_list: list[object] = []
            memo[identity] = result_list
            result_list.extend(detach(child) for child in cast(list[object], item))
            return result_list
        if item_type is dict:
            result_dict: dict[object, object] = {}
            memo[identity] = result_dict
            for key, child in dict.items(cast(dict[object, object], item)):
                result_dict[detach(key)] = detach(child)
            return result_dict
        result = object.__new__(item_type)
        memo[identity] = result
        for field in fields(cast(Any, item_type)):
            object.__setattr__(
                result,
                field.name,
                detach(object.__getattribute__(item, field.name)),
            )
        return result

    return detach(value)


TYPED_EMPTY_PACKAGE_CONTRACT = "aware.meta.type-schema.typed-empty-package.v1"
TYPED_EMPTY_CATALOG_CONTRACT = "aware.meta.type-schema.typed-empty-catalog.v1"
PACKAGE_TRANSITION_CONTRACT = "aware.meta.type-schema.package-transition.v1"
CATALOG_TRANSITION_CONTRACT = "aware.meta.type-schema.catalog-transition.v1"
_WHITESPACE = re.compile(r"\s").search


class TypeSchemaTransitionError(ValueError):
    """Raised when a zero-write successor is not an exact delta."""


def _preflight_transition_operation(
    operands: tuple[object, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
) -> None:
    if type(reader) is not TypeSchemaPositiveReaderCapability:
        raise TypeSchemaTransitionError(
            "reader must be exact TypeSchemaPositiveReaderCapability"
        )
    if (
        type(request_ref) is not str
        or not request_ref
        or request_ref.strip() != request_ref
    ):
        raise TypeSchemaTransitionError("request_ref must be normalized text")
    retained_request_ref = object.__getattribute__(reader, "_request_ref")
    if type(retained_request_ref) is not str or retained_request_ref != request_ref:
        raise TypeSchemaTransitionError("reader capability belongs to another request")


def _package_operation_snapshot(
    prior: TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot,
    definition_movements: tuple[DefinitionFragmentMovement, ...],
    attribution_movements: tuple[SourceAttributionFragmentMovement, ...],
) -> object:
    return (
        "composition.transition-package",
        _flat_protected_operand_guard(
            (prior, definition_movements, attribution_movements)
        ),
    )


def _catalog_operation_snapshot(
    prior: TypeSchemaTypedEmptyCatalogAuthority | TypeSchemaCatalogRoot,
    package_movements: tuple[PackageRootMovement, ...],
    owner_movements: tuple[TypeOwnerBindingMovement, ...],
) -> object:
    return (
        "composition.transition-catalog",
        _flat_protected_operand_guard((prior, package_movements, owner_movements)),
    )


def _token(value: str, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.strip() != value
        or _WHITESPACE(value) is not None
    ):
        raise TypeSchemaTransitionError(f"{field} must be a nonempty token")
    return value


@dataclass(frozen=True, slots=True)
class TypeSchemaTypedEmptyPackageAuthority:
    package: TypeSchemaPackageRoot
    empty_ref: str
    contract: str = TYPED_EMPTY_PACKAGE_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != TYPED_EMPTY_PACKAGE_CONTRACT:
            raise TypeSchemaTransitionError("typed-empty package unsupported")
        if not isinstance(self.package, TypeSchemaPackageRoot):
            raise TypeError("package must be TypeSchemaPackageRoot")
        if (
            self.package.definition_index.binding_count != 0
            or self.package.source_attribution_index.binding_count != 0
        ):
            raise TypeSchemaTransitionError("typed-empty package indexes must be empty")
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.empty_ref != expected:
            raise TypeSchemaTransitionError(f"empty_ref mismatch; expected {expected}")

    def semantic_wire(self) -> dict[str, object]:
        return {"contract": self.contract, "package": self.package.to_wire()}

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "empty_ref": self.empty_ref}


@dataclass(frozen=True, slots=True)
class TypeSchemaTypedEmptyCatalogAuthority:
    catalog: TypeSchemaCatalogRoot
    empty_ref: str
    contract: str = TYPED_EMPTY_CATALOG_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != TYPED_EMPTY_CATALOG_CONTRACT:
            raise TypeSchemaTransitionError("typed-empty catalog unsupported")
        if not isinstance(self.catalog, TypeSchemaCatalogRoot):
            raise TypeError("catalog must be TypeSchemaCatalogRoot")
        if self.catalog.package_count != 0 or self.catalog.owner_count != 0:
            raise TypeSchemaTransitionError("typed-empty catalog indexes must be empty")
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.empty_ref != expected:
            raise TypeSchemaTransitionError(f"empty_ref mismatch; expected {expected}")

    def semantic_wire(self) -> dict[str, object]:
        return {"contract": self.contract, "catalog": self.catalog.to_wire()}

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "empty_ref": self.empty_ref}


@dataclass(frozen=True, slots=True)
class DefinitionFragmentMovement:
    type_ref: str
    prior: PersistentBodyCoordinate | None
    next: TypeDefinitionFragment | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        if self.prior is not None and not isinstance(
            self.prior, PersistentBodyCoordinate
        ):
            raise TypeError("prior must be body coordinate or None")
        if self.next is not None:
            if not isinstance(self.next, TypeDefinitionFragment):
                raise TypeError("next must be definition fragment or None")
            if self.next.type_ref != self.type_ref:
                raise TypeSchemaTransitionError("definition movement key mismatch")
        if self.prior is None and self.next is None:
            raise TypeSchemaTransitionError("definition movement cannot be empty")


@dataclass(frozen=True, slots=True)
class SourceAttributionFragmentMovement:
    source_path: str
    prior: PersistentBodyCoordinate | None
    next: TypeSchemaSourceAttributionFragment | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_path", _token(self.source_path, "source_path"))
        if self.prior is not None and not isinstance(
            self.prior, PersistentBodyCoordinate
        ):
            raise TypeError("prior must be body coordinate or None")
        if self.next is not None:
            if not isinstance(self.next, TypeSchemaSourceAttributionFragment):
                raise TypeError("next must be source attribution or None")
            if self.next.source_path != self.source_path:
                raise TypeSchemaTransitionError("attribution movement path mismatch")
        if self.prior is None and self.next is None:
            raise TypeSchemaTransitionError("attribution movement cannot be empty")


@dataclass(frozen=True, slots=True)
class PackageRootMovement:
    package_ref: str
    prior: PersistentBodyCoordinate | None
    next: TypeSchemaPackageRoot | None
    transition: TypeSchemaPackageTransition | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_ref", _token(self.package_ref, "package_ref"))
        if self.prior is not None and not isinstance(
            self.prior, PersistentBodyCoordinate
        ):
            raise TypeError("prior must be body coordinate or None")
        if self.next is not None:
            if not isinstance(self.next, TypeSchemaPackageRoot):
                raise TypeError("next must be package root or None")
            if self.next.package_ref != self.package_ref:
                raise TypeSchemaTransitionError("package movement key mismatch")
            if not isinstance(self.transition, TypeSchemaPackageTransition):
                raise TypeSchemaTransitionError(
                    "package successor requires exact package transition"
                )
            if self.transition.successor != self.next:
                raise TypeSchemaTransitionError("package successor/transition mismatch")
        elif self.transition is not None:
            raise TypeSchemaTransitionError(
                "deleted package cannot carry successor transition"
            )
        if self.prior is None and self.next is None:
            raise TypeSchemaTransitionError("package movement cannot be empty")


@dataclass(frozen=True, slots=True)
class TypeOwnerBindingMovement:
    type_ref: str
    prior: PersistentBodyCoordinate | None
    next: TypeOwnerBinding | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        if self.prior is not None and not isinstance(
            self.prior, PersistentBodyCoordinate
        ):
            raise TypeError("prior must be body coordinate or None")
        if self.next is not None:
            if not isinstance(self.next, TypeOwnerBinding):
                raise TypeError("next must be owner binding or None")
            if self.next.type_ref != self.type_ref:
                raise TypeSchemaTransitionError("owner movement key mismatch")
        if self.prior is None and self.next is None:
            raise TypeSchemaTransitionError("owner movement cannot be empty")


@dataclass(frozen=True, slots=True)
class TypeDefinitionLifecycleEvidence:
    type_ref: str
    prior: PersistentBodyCoordinate | None
    next: PersistentBodyCoordinate | None
    lifecycle_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        for coordinate in (self.prior, self.next):
            if coordinate is not None:
                if not isinstance(coordinate, PersistentBodyCoordinate):
                    raise TypeError("definition lifecycle requires body coordinates")
                if coordinate.schema != TYPE_DEFINITION_FRAGMENT_CONTRACT:
                    raise TypeSchemaTransitionError(
                        "definition lifecycle coordinate role mismatch"
                    )
        if self.prior is None and self.next is None:
            raise TypeSchemaTransitionError("definition lifecycle cannot be empty")
        expected = digest_payload(
            "aware.meta.type-schema.definition-movement.v1", self.semantic_wire()
        )
        if self.lifecycle_ref != expected:
            raise TypeSchemaTransitionError(
                f"definition lifecycle ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        type_ref: str,
        prior: PersistentBodyCoordinate | None,
        next: PersistentBodyCoordinate | None,
    ) -> TypeDefinitionLifecycleEvidence:
        normalized_type_ref = _token(type_ref, "type_ref")
        for coordinate in (prior, next):
            if coordinate is not None:
                if not isinstance(coordinate, PersistentBodyCoordinate):
                    raise TypeError("definition lifecycle requires body coordinates")
                if coordinate.schema != TYPE_DEFINITION_FRAGMENT_CONTRACT:
                    raise TypeSchemaTransitionError(
                        "definition lifecycle coordinate role mismatch"
                    )
        if prior is None and next is None:
            raise TypeSchemaTransitionError("definition lifecycle cannot be empty")
        semantic = {
            "type_ref": normalized_type_ref,
            "prior": None if prior is None else prior.to_wire(),
            "next": None if next is None else next.to_wire(),
        }
        value = object.__new__(cls)
        object.__setattr__(value, "type_ref", normalized_type_ref)
        object.__setattr__(value, "prior", prior)
        object.__setattr__(value, "next", next)
        object.__setattr__(
            value,
            "lifecycle_ref",
            _prevalidated_digest(
                "aware.meta.type-schema.definition-movement.v1", semantic
            ),
        )
        return value

    def semantic_wire(self) -> dict[str, object]:
        return {
            "type_ref": self.type_ref,
            "prior": None if self.prior is None else self.prior.to_wire(),
            "next": None if self.next is None else self.next.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "lifecycle_ref": self.lifecycle_ref}


@dataclass(frozen=True, slots=True)
class SourceAttributionLifecycleEvidence:
    source_path: str
    prior: PersistentBodyCoordinate | None
    next: PersistentBodyCoordinate | None
    lifecycle_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_path", _token(self.source_path, "source_path"))
        for coordinate in (self.prior, self.next):
            if coordinate is not None:
                if not isinstance(coordinate, PersistentBodyCoordinate):
                    raise TypeError("attribution lifecycle requires body coordinates")
                if coordinate.schema != SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT:
                    raise TypeSchemaTransitionError(
                        "attribution lifecycle coordinate role mismatch"
                    )
        if self.prior is None and self.next is None:
            raise TypeSchemaTransitionError("attribution lifecycle cannot be empty")
        expected = digest_payload(
            "aware.meta.type-schema.attribution-movement.v1", self.semantic_wire()
        )
        if self.lifecycle_ref != expected:
            raise TypeSchemaTransitionError(
                f"attribution lifecycle ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        source_path: str,
        prior: PersistentBodyCoordinate | None,
        next: PersistentBodyCoordinate | None,
    ) -> SourceAttributionLifecycleEvidence:
        normalized_path = _token(source_path, "source_path")
        for coordinate in (prior, next):
            if coordinate is not None:
                if not isinstance(coordinate, PersistentBodyCoordinate):
                    raise TypeError("attribution lifecycle requires body coordinates")
                if coordinate.schema != SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT:
                    raise TypeSchemaTransitionError(
                        "attribution lifecycle coordinate role mismatch"
                    )
        if prior is None and next is None:
            raise TypeSchemaTransitionError("attribution lifecycle cannot be empty")
        semantic = {
            "source_path": normalized_path,
            "prior": None if prior is None else prior.to_wire(),
            "next": None if next is None else next.to_wire(),
        }
        value = object.__new__(cls)
        object.__setattr__(value, "source_path", normalized_path)
        object.__setattr__(value, "prior", prior)
        object.__setattr__(value, "next", next)
        object.__setattr__(
            value,
            "lifecycle_ref",
            _prevalidated_digest(
                "aware.meta.type-schema.attribution-movement.v1", semantic
            ),
        )
        return value

    def semantic_wire(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "prior": None if self.prior is None else self.prior.to_wire(),
            "next": None if self.next is None else self.next.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "lifecycle_ref": self.lifecycle_ref}


@dataclass(frozen=True, slots=True)
class TypeSchemaPackageTransition:
    prior: TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot
    successor: TypeSchemaPackageRoot
    definition_lifecycle: tuple[TypeDefinitionLifecycleEvidence, ...]
    attribution_lifecycle: tuple[SourceAttributionLifecycleEvidence, ...]
    definition_movement_refs: tuple[str, ...]
    attribution_movement_refs: tuple[str, ...]
    emitted_bodies: tuple[PersistentBodyAuthority, ...]
    reused_coordinates: tuple[PersistentBodyCoordinate, ...]
    transition_ref: str
    observation: PositiveReadObservation
    contract: str = PACKAGE_TRANSITION_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PACKAGE_TRANSITION_CONTRACT:
            raise TypeSchemaTransitionError("package transition unsupported")
        if not isinstance(
            self.prior, (TypeSchemaTypedEmptyPackageAuthority, TypeSchemaPackageRoot)
        ):
            raise TypeError("package transition prior must be exact typed authority")
        if not isinstance(self.successor, TypeSchemaPackageRoot):
            raise TypeError("successor must be TypeSchemaPackageRoot")
        prior_package = (
            self.prior.package
            if isinstance(self.prior, TypeSchemaTypedEmptyPackageAuthority)
            else self.prior
        )
        if (
            prior_package.package_ref != self.successor.package_ref
            or prior_package.package_name != self.successor.package_name
            or prior_package.namespace != self.successor.namespace
            or prior_package.semantic_version != self.successor.semantic_version
            or prior_package.dependency_package_refs
            != self.successor.dependency_package_refs
        ):
            raise TypeSchemaTransitionError(
                "package transition predecessor does not bind successor package"
            )
        if type(self.definition_lifecycle) is not tuple:
            raise TypeSchemaTransitionError(
                "definition_lifecycle must be immutable tuple"
            )
        lifecycle = tuple(
            sorted(self.definition_lifecycle, key=lambda item: item.type_ref)
        )
        if lifecycle != self.definition_lifecycle or len(
            {item.type_ref for item in lifecycle}
        ) != len(lifecycle):
            raise TypeSchemaTransitionError(
                "definition_lifecycle must be typed, sorted and unique"
            )
        if type(self.attribution_lifecycle) is not tuple:
            raise TypeSchemaTransitionError(
                "attribution_lifecycle must be immutable tuple"
            )
        attribution_lifecycle = tuple(
            sorted(self.attribution_lifecycle, key=lambda item: item.source_path)
        )
        if attribution_lifecycle != self.attribution_lifecycle or len(
            {item.source_path for item in attribution_lifecycle}
        ) != len(attribution_lifecycle):
            raise TypeSchemaTransitionError(
                "attribution_lifecycle must be typed, sorted and unique"
            )
        for values, field in (
            (self.definition_movement_refs, "definition_movement_refs"),
            (self.attribution_movement_refs, "attribution_movement_refs"),
        ):
            if type(values) is not tuple or values != tuple(sorted(set(values))):
                raise TypeSchemaTransitionError(f"{field} must be sorted and unique")
        if self.definition_movement_refs != tuple(
            sorted(item.lifecycle_ref for item in lifecycle)
        ):
            raise TypeSchemaTransitionError(
                "definition movement refs/lifecycle evidence differ"
            )
        if self.attribution_movement_refs != tuple(
            sorted(item.lifecycle_ref for item in attribution_lifecycle)
        ):
            raise TypeSchemaTransitionError(
                "attribution movement refs/lifecycle evidence differ"
            )
        if (
            type(self.emitted_bodies) is not tuple
            or type(self.reused_coordinates) is not tuple
        ):
            raise TypeSchemaTransitionError("transition body evidence must be tuples")
        if not isinstance(self.observation, PositiveReadObservation):
            raise TypeError("observation must be PositiveReadObservation")
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.transition_ref != expected:
            raise TypeSchemaTransitionError(
                f"transition_ref mismatch; expected {expected}"
            )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "prior": {
                "kind": (
                    "typed_empty"
                    if isinstance(self.prior, TypeSchemaTypedEmptyPackageAuthority)
                    else "package_root"
                ),
                "authority": self.prior.to_wire(),
            },
            "successor": self.successor.to_wire(),
            "definition_lifecycle": [
                item.to_wire() for item in self.definition_lifecycle
            ],
            "attribution_lifecycle": [
                item.to_wire() for item in self.attribution_lifecycle
            ],
            "definition_movement_refs": list(self.definition_movement_refs),
            "attribution_movement_refs": list(self.attribution_movement_refs),
            "emitted_bodies": [
                item.coordinate.to_wire() for item in self.emitted_bodies
            ],
            "reused_coordinates": [item.to_wire() for item in self.reused_coordinates],
        }

    @property
    def prior_ref(self) -> str:
        return (
            self.prior.empty_ref
            if isinstance(self.prior, TypeSchemaTypedEmptyPackageAuthority)
            else self.prior.package_root_ref
        )


@dataclass(frozen=True, slots=True)
class TypeSchemaCatalogTransition:
    prior_ref: str
    successor: TypeSchemaCatalogRoot
    package_movement_refs: tuple[str, ...]
    owner_movement_refs: tuple[str, ...]
    emitted_bodies: tuple[PersistentBodyAuthority, ...]
    reused_coordinates: tuple[PersistentBodyCoordinate, ...]
    transition_ref: str
    observation: PositiveReadObservation
    contract: str = CATALOG_TRANSITION_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != CATALOG_TRANSITION_CONTRACT:
            raise TypeSchemaTransitionError("catalog transition unsupported")
        object.__setattr__(self, "prior_ref", _token(self.prior_ref, "prior_ref"))
        if not isinstance(self.successor, TypeSchemaCatalogRoot):
            raise TypeError("successor must be TypeSchemaCatalogRoot")
        for values, field in (
            (self.package_movement_refs, "package_movement_refs"),
            (self.owner_movement_refs, "owner_movement_refs"),
        ):
            if type(values) is not tuple or values != tuple(sorted(set(values))):
                raise TypeSchemaTransitionError(f"{field} must be sorted and unique")
        if (
            type(self.emitted_bodies) is not tuple
            or type(self.reused_coordinates) is not tuple
        ):
            raise TypeSchemaTransitionError("transition body evidence must be tuples")
        if not isinstance(self.observation, PositiveReadObservation):
            raise TypeError("observation must be PositiveReadObservation")
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.transition_ref != expected:
            raise TypeSchemaTransitionError(
                f"transition_ref mismatch; expected {expected}"
            )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "prior_ref": self.prior_ref,
            "successor": self.successor.to_wire(),
            "package_movement_refs": list(self.package_movement_refs),
            "owner_movement_refs": list(self.owner_movement_refs),
            "emitted_bodies": [
                item.coordinate.to_wire() for item in self.emitted_bodies
            ],
            "reused_coordinates": [item.to_wire() for item in self.reused_coordinates],
        }


def _create_prevalidated_package_transition(
    context: _MetaTypeSchemaOperationContext,
    *,
    prior: TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot,
    successor: TypeSchemaPackageRoot,
    definition_lifecycle: tuple[TypeDefinitionLifecycleEvidence, ...],
    attribution_lifecycle: tuple[SourceAttributionLifecycleEvidence, ...],
    definition_movement_refs: tuple[str, ...],
    attribution_movement_refs: tuple[str, ...],
    emitted_bodies: tuple[PersistentBodyAuthority, ...],
    reused_coordinates: tuple[PersistentBodyCoordinate, ...],
    transition_ref: str,
    observation: PositiveReadObservation,
) -> TypeSchemaPackageTransition:
    _require_meta_type_schema_operation(context)
    value = object.__new__(TypeSchemaPackageTransition)
    object.__setattr__(value, "prior", prior)
    object.__setattr__(value, "successor", successor)
    object.__setattr__(value, "definition_lifecycle", definition_lifecycle)
    object.__setattr__(value, "attribution_lifecycle", attribution_lifecycle)
    object.__setattr__(value, "definition_movement_refs", definition_movement_refs)
    object.__setattr__(value, "attribution_movement_refs", attribution_movement_refs)
    object.__setattr__(value, "emitted_bodies", emitted_bodies)
    object.__setattr__(value, "reused_coordinates", reused_coordinates)
    object.__setattr__(value, "transition_ref", transition_ref)
    object.__setattr__(value, "observation", observation)
    object.__setattr__(value, "contract", PACKAGE_TRANSITION_CONTRACT)
    return value


def _create_prevalidated_catalog_transition(
    context: _MetaTypeSchemaOperationContext,
    *,
    prior_ref: str,
    successor: TypeSchemaCatalogRoot,
    package_movement_refs: tuple[str, ...],
    owner_movement_refs: tuple[str, ...],
    emitted_bodies: tuple[PersistentBodyAuthority, ...],
    reused_coordinates: tuple[PersistentBodyCoordinate, ...],
    transition_ref: str,
    observation: PositiveReadObservation,
) -> TypeSchemaCatalogTransition:
    _require_meta_type_schema_operation(context)
    value = object.__new__(TypeSchemaCatalogTransition)
    object.__setattr__(value, "prior_ref", prior_ref)
    object.__setattr__(value, "successor", successor)
    object.__setattr__(value, "package_movement_refs", package_movement_refs)
    object.__setattr__(value, "owner_movement_refs", owner_movement_refs)
    object.__setattr__(value, "emitted_bodies", emitted_bodies)
    object.__setattr__(value, "reused_coordinates", reused_coordinates)
    object.__setattr__(value, "transition_ref", transition_ref)
    object.__setattr__(value, "observation", observation)
    object.__setattr__(value, "contract", CATALOG_TRANSITION_CONTRACT)
    return value


def _detached_coordinate(
    value: PersistentBodyCoordinate,
) -> PersistentBodyCoordinate:
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


def _detached_prevalidated_coordinate(
    context: _MetaTypeSchemaOperationContext,
    value: PersistentBodyCoordinate,
) -> PersistentBodyCoordinate:
    _require_meta_type_schema_operation(context)
    if type(value) is not PersistentBodyCoordinate:
        raise TypeSchemaTransitionError("detached coordinate must be exact")
    result = object.__new__(PersistentBodyCoordinate)
    for field in (
        "schema",
        "ref_field",
        "authority_ref",
        "body_ref",
        "body_digest",
        "size_bytes",
        "coordinate_ref",
        "contract",
    ):
        object.__setattr__(result, field, object.__getattribute__(value, field))
    return result


def _detached_prevalidated_index_root(
    context: _MetaTypeSchemaOperationContext,
    value: PersistentIndexRoot,
) -> PersistentIndexRoot:
    _require_meta_type_schema_operation(context)
    if type(value) is not PersistentIndexRoot:
        raise TypeSchemaTransitionError("detached index root must be exact")
    result = object.__new__(PersistentIndexRoot)
    object.__setattr__(result, "keyspace", value.keyspace)
    object.__setattr__(
        result,
        "root_node",
        _detached_prevalidated_coordinate(context, value.root_node),
    )
    object.__setattr__(result, "binding_count", value.binding_count)
    object.__setattr__(result, "root_ref", value.root_ref)
    object.__setattr__(result, "contract", value.contract)
    return result


def _detached_prevalidated_package_root(
    context: _MetaTypeSchemaOperationContext,
    value: TypeSchemaPackageRoot,
) -> TypeSchemaPackageRoot:
    _require_meta_type_schema_operation(context)
    if type(value) is not TypeSchemaPackageRoot:
        raise TypeSchemaTransitionError("detached package root must be exact")
    result = object.__new__(TypeSchemaPackageRoot)
    object.__setattr__(result, "package_ref", value.package_ref)
    object.__setattr__(result, "package_name", value.package_name)
    object.__setattr__(result, "namespace", value.namespace)
    object.__setattr__(result, "semantic_version", value.semantic_version)
    object.__setattr__(result, "dependency_package_refs", value.dependency_package_refs)
    object.__setattr__(
        result,
        "definition_index",
        _detached_prevalidated_index_root(context, value.definition_index),
    )
    object.__setattr__(
        result,
        "source_attribution_index",
        _detached_prevalidated_index_root(context, value.source_attribution_index),
    )
    object.__setattr__(result, "package_root_ref", value.package_root_ref)
    object.__setattr__(result, "contract", value.contract)
    return result


def _detached_prevalidated_body(
    context: _MetaTypeSchemaOperationContext,
    value: PersistentBodyAuthority,
) -> PersistentBodyAuthority:
    _require_meta_type_schema_operation(context)
    if type(value) is not PersistentBodyAuthority:
        raise TypeSchemaTransitionError("detached body must be exact")
    result = object.__new__(PersistentBodyAuthority)
    object.__setattr__(
        result,
        "coordinate",
        _detached_prevalidated_coordinate(context, value.coordinate),
    )
    object.__setattr__(result, "canonical_bytes", bytes(value.canonical_bytes))
    return result


def _detached_prevalidated_definition_lifecycle(
    context: _MetaTypeSchemaOperationContext,
    value: TypeDefinitionLifecycleEvidence,
) -> TypeDefinitionLifecycleEvidence:
    _require_meta_type_schema_operation(context)
    if type(value) is not TypeDefinitionLifecycleEvidence:
        raise TypeSchemaTransitionError("detached definition lifecycle must be exact")
    result = object.__new__(TypeDefinitionLifecycleEvidence)
    object.__setattr__(result, "type_ref", value.type_ref)
    object.__setattr__(
        result,
        "prior",
        (
            None
            if value.prior is None
            else _detached_prevalidated_coordinate(context, value.prior)
        ),
    )
    object.__setattr__(
        result,
        "next",
        (
            None
            if value.next is None
            else _detached_prevalidated_coordinate(context, value.next)
        ),
    )
    object.__setattr__(result, "lifecycle_ref", value.lifecycle_ref)
    return result


def _detached_prevalidated_attribution_lifecycle(
    context: _MetaTypeSchemaOperationContext,
    value: SourceAttributionLifecycleEvidence,
) -> SourceAttributionLifecycleEvidence:
    _require_meta_type_schema_operation(context)
    if type(value) is not SourceAttributionLifecycleEvidence:
        raise TypeSchemaTransitionError("detached attribution lifecycle must be exact")
    result = object.__new__(SourceAttributionLifecycleEvidence)
    object.__setattr__(result, "source_path", value.source_path)
    object.__setattr__(
        result,
        "prior",
        (
            None
            if value.prior is None
            else _detached_prevalidated_coordinate(context, value.prior)
        ),
    )
    object.__setattr__(
        result,
        "next",
        (
            None
            if value.next is None
            else _detached_prevalidated_coordinate(context, value.next)
        ),
    )
    object.__setattr__(result, "lifecycle_ref", value.lifecycle_ref)
    return result


def _detached_body(value: PersistentBodyAuthority) -> PersistentBodyAuthority:
    return PersistentBodyAuthority(
        _detached_coordinate(value.coordinate),
        bytes(value.canonical_bytes),
    )


def _detached_package_transition(
    context: _MetaTypeSchemaOperationContext,
    value: TypeSchemaPackageTransition,
) -> TypeSchemaPackageTransition:
    _require_meta_type_schema_operation(context)

    # The complete transition graph was recursively admitted before the
    # operation context was issued.  Clone its many content-addressed bodies
    # with one context check: repeating the same registry check for every trie
    # fragment adds authority-free work proportional to the emitted graph.
    def coordinate(
        source: PersistentBodyCoordinate,
    ) -> PersistentBodyCoordinate:
        result = object.__new__(PersistentBodyCoordinate)
        object.__setattr__(result, "schema", source.schema)
        object.__setattr__(result, "ref_field", source.ref_field)
        object.__setattr__(result, "authority_ref", source.authority_ref)
        object.__setattr__(result, "body_ref", source.body_ref)
        object.__setattr__(result, "body_digest", source.body_digest)
        object.__setattr__(result, "size_bytes", source.size_bytes)
        object.__setattr__(result, "coordinate_ref", source.coordinate_ref)
        object.__setattr__(result, "contract", source.contract)
        return result

    def index_root(source: PersistentIndexRoot) -> PersistentIndexRoot:
        result = object.__new__(PersistentIndexRoot)
        object.__setattr__(result, "keyspace", source.keyspace)
        object.__setattr__(result, "root_node", coordinate(source.root_node))
        object.__setattr__(result, "binding_count", source.binding_count)
        object.__setattr__(result, "root_ref", source.root_ref)
        object.__setattr__(result, "contract", source.contract)
        return result

    def package_root(source: TypeSchemaPackageRoot) -> TypeSchemaPackageRoot:
        result = object.__new__(TypeSchemaPackageRoot)
        object.__setattr__(result, "package_ref", source.package_ref)
        object.__setattr__(result, "package_name", source.package_name)
        object.__setattr__(result, "namespace", source.namespace)
        object.__setattr__(result, "semantic_version", source.semantic_version)
        object.__setattr__(
            result, "dependency_package_refs", source.dependency_package_refs
        )
        object.__setattr__(
            result, "definition_index", index_root(source.definition_index)
        )
        object.__setattr__(
            result,
            "source_attribution_index",
            index_root(source.source_attribution_index),
        )
        object.__setattr__(result, "package_root_ref", source.package_root_ref)
        object.__setattr__(result, "contract", source.contract)
        return result

    if isinstance(value.prior, TypeSchemaTypedEmptyPackageAuthority):
        detached_prior: TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot = (
            TypeSchemaTypedEmptyPackageAuthority(
                package_root(value.prior.package),
                value.prior.empty_ref,
                value.prior.contract,
            )
        )
    else:
        detached_prior = package_root(value.prior)

    detached_definition_lifecycle: list[TypeDefinitionLifecycleEvidence] = []
    for source in value.definition_lifecycle:
        result = object.__new__(TypeDefinitionLifecycleEvidence)
        object.__setattr__(result, "type_ref", source.type_ref)
        object.__setattr__(
            result, "prior", None if source.prior is None else coordinate(source.prior)
        )
        object.__setattr__(
            result, "next", None if source.next is None else coordinate(source.next)
        )
        object.__setattr__(result, "lifecycle_ref", source.lifecycle_ref)
        detached_definition_lifecycle.append(result)

    detached_attribution_lifecycle: list[SourceAttributionLifecycleEvidence] = []
    for source in value.attribution_lifecycle:
        result = object.__new__(SourceAttributionLifecycleEvidence)
        object.__setattr__(result, "source_path", source.source_path)
        object.__setattr__(
            result, "prior", None if source.prior is None else coordinate(source.prior)
        )
        object.__setattr__(
            result, "next", None if source.next is None else coordinate(source.next)
        )
        object.__setattr__(result, "lifecycle_ref", source.lifecycle_ref)
        detached_attribution_lifecycle.append(result)

    return _create_prevalidated_package_transition(
        context,
        prior=detached_prior,
        successor=package_root(value.successor),
        definition_lifecycle=tuple(detached_definition_lifecycle),
        attribution_lifecycle=tuple(detached_attribution_lifecycle),
        definition_movement_refs=value.definition_movement_refs,
        attribution_movement_refs=value.attribution_movement_refs,
        # The catalog operation captures every body's exact scalar coordinate
        # and immutable bytes before its first provider callback. Keeping this
        # tuple briefly avoids allocating thousands of detached objects that
        # cannot enter the catalog result.
        emitted_bodies=value.emitted_bodies,
        reused_coordinates=tuple(coordinate(item) for item in value.reused_coordinates),
        transition_ref=value.transition_ref,
        observation=PositiveReadObservation(
            read_count=value.observation.read_count,
            read_bytes=value.observation.read_bytes,
            cache_hits=value.observation.cache_hits,
            max_lookup_depth=value.observation.max_lookup_depth,
            elapsed_ns=value.observation.elapsed_ns,
            enumeration_attempts=value.observation.enumeration_attempts,
        ),
    )


def _detached_catalog_transition(
    context: _MetaTypeSchemaOperationContext,
    value: TypeSchemaCatalogTransition,
) -> TypeSchemaCatalogTransition:
    from .composition_codec import decode_catalog_root, encode_composition_value

    return _create_prevalidated_catalog_transition(
        context,
        prior_ref=value.prior_ref,
        successor=decode_catalog_root(encode_composition_value(value.successor)),
        package_movement_refs=value.package_movement_refs,
        owner_movement_refs=value.owner_movement_refs,
        emitted_bodies=tuple(_detached_body(item) for item in value.emitted_bodies),
        reused_coordinates=tuple(
            _detached_coordinate(item) for item in value.reused_coordinates
        ),
        transition_ref=value.transition_ref,
        observation=PositiveReadObservation(
            read_count=value.observation.read_count,
            read_bytes=value.observation.read_bytes,
            cache_hits=value.observation.cache_hits,
            max_lookup_depth=value.observation.max_lookup_depth,
            elapsed_ns=value.observation.elapsed_ns,
            enumeration_attempts=value.observation.enumeration_attempts,
        ),
    )


def _detached_package_prior(
    value: TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot,
) -> TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot:
    from .composition_codec import decode_package_root, encode_composition_value

    if isinstance(value, TypeSchemaTypedEmptyPackageAuthority):
        return TypeSchemaTypedEmptyPackageAuthority(
            decode_package_root(encode_composition_value(value.package)),
            value.empty_ref,
            value.contract,
        )
    return decode_package_root(encode_composition_value(value))


def _detached_catalog_prior(
    value: TypeSchemaTypedEmptyCatalogAuthority | TypeSchemaCatalogRoot,
) -> TypeSchemaTypedEmptyCatalogAuthority | TypeSchemaCatalogRoot:
    from .composition_codec import decode_catalog_root, encode_composition_value

    if isinstance(value, TypeSchemaTypedEmptyCatalogAuthority):
        return TypeSchemaTypedEmptyCatalogAuthority(
            decode_catalog_root(encode_composition_value(value.catalog)),
            value.empty_ref,
            value.contract,
        )
    return decode_catalog_root(encode_composition_value(value))


def _detached_definition_movement(
    value: DefinitionFragmentMovement,
) -> DefinitionFragmentMovement:
    from .composition_codec import decode_definition_fragment, encode_composition_value

    return DefinitionFragmentMovement(
        value.type_ref,
        None if value.prior is None else _detached_coordinate(value.prior),
        (
            None
            if value.next is None
            else decode_definition_fragment(encode_composition_value(value.next))
        ),
    )


def _detached_attribution_movement(
    value: SourceAttributionFragmentMovement,
) -> SourceAttributionFragmentMovement:
    from .composition_codec import (
        decode_source_attribution_fragment,
        encode_composition_value,
    )

    return SourceAttributionFragmentMovement(
        value.source_path,
        None if value.prior is None else _detached_coordinate(value.prior),
        (
            None
            if value.next is None
            else decode_source_attribution_fragment(
                encode_composition_value(value.next)
            )
        ),
    )


def _detached_package_movement(
    context: _MetaTypeSchemaOperationContext,
    value: PackageRootMovement,
) -> PackageRootMovement:
    detached_transition = (
        None
        if value.transition is None
        else _detached_package_transition(context, value.transition)
    )

    return PackageRootMovement(
        value.package_ref,
        None if value.prior is None else _detached_coordinate(value.prior),
        (
            None
            if value.next is None
            else (
                detached_transition.successor
                if detached_transition is not None
                else _detached_prevalidated_package_root(context, value.next)
            )
        ),
        detached_transition,
    )


def _detached_owner_movement(
    value: TypeOwnerBindingMovement,
) -> TypeOwnerBindingMovement:
    from .composition_codec import decode_type_owner_binding, encode_composition_value

    return TypeOwnerBindingMovement(
        value.type_ref,
        None if value.prior is None else _detached_coordinate(value.prior),
        (
            None
            if value.next is None
            else decode_type_owner_binding(encode_composition_value(value.next))
        ),
    )


def create_typed_empty_package(
    *,
    package_ref: str,
    package_name: str,
    namespace: str,
    semantic_version: str,
    dependency_package_refs: tuple[str, ...] = (),
) -> tuple[TypeSchemaTypedEmptyPackageAuthority, tuple[PersistentBodyAuthority, ...]]:
    definition_root, definition_bodies = create_empty_persistent_index(
        f"definition:{package_ref}"
    )
    attribution_root, attribution_bodies = create_empty_persistent_index(
        f"source-attribution:{package_ref}"
    )
    package = TypeSchemaPackageRoot.create(
        package_ref=package_ref,
        package_name=package_name,
        namespace=namespace,
        semantic_version=semantic_version,
        dependency_package_refs=dependency_package_refs,
        definition_index=definition_root,
        source_attribution_index=attribution_root,
    )
    semantic = {"contract": TYPED_EMPTY_PACKAGE_CONTRACT, "package": package.to_wire()}
    authority = TypeSchemaTypedEmptyPackageAuthority(
        package,
        digest_payload(TYPED_EMPTY_PACKAGE_CONTRACT, semantic),
    )
    return authority, (*definition_bodies, *attribution_bodies)


def create_typed_empty_catalog(
    *, target_package_ref: str
) -> tuple[TypeSchemaTypedEmptyCatalogAuthority, tuple[PersistentBodyAuthority, ...]]:
    package_root, package_bodies = create_empty_persistent_index(
        "type-schema:catalog:packages"
    )
    owner_root, owner_bodies = create_empty_persistent_index(
        "type-schema:catalog:owners"
    )
    catalog = TypeSchemaCatalogRoot.create(
        target_package_ref=target_package_ref,
        package_index=package_root,
        owner_index=owner_root,
    )
    semantic = {"contract": TYPED_EMPTY_CATALOG_CONTRACT, "catalog": catalog.to_wire()}
    authority = TypeSchemaTypedEmptyCatalogAuthority(
        catalog,
        digest_payload(TYPED_EMPTY_CATALOG_CONTRACT, semantic),
    )
    return authority, (*package_bodies, *owner_bodies)


def transition_package(
    prior: TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot,
    *,
    definition_movements: tuple[DefinitionFragmentMovement, ...],
    attribution_movements: tuple[SourceAttributionFragmentMovement, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    _operation_context: object | None = None,
) -> TypeSchemaPackageTransition:
    operands = (prior, definition_movements, attribution_movements)
    _preflight_transition_operation(operands, reader, request_ref)
    admission_started = perf_counter_ns()
    try:
        if _operation_context is None:
            operand_snapshot = _package_operation_snapshot(
                prior,
                definition_movements,
                attribution_movements,
            )
            admitted_values = None
        else:
            admitted_guard, admitted_values = _admit_and_detach_exact_graph(operands)
            operand_snapshot = (
                "composition.transition-package",
                admitted_guard,
            )
    except TypeSchemaPersistentIndexError as error:
        raise TypeSchemaTransitionError(
            f"transition operand admission failed: {error}"
        ) from error
    admission_finished = perf_counter_ns()
    with _meta_type_schema_operation(
        operation_ref="composition.transition-package",
        operands=operands,
        reader=reader,
        request_ref=request_ref,
        operand_snapshot=operand_snapshot,
    ) as context:
        if _operation_context is None:
            admitted_prior = _detached_package_prior(prior)
            admitted_definitions = tuple(
                _detached_definition_movement(value) for value in definition_movements
            )
            admitted_attributions = tuple(
                _detached_attribution_movement(value) for value in attribution_movements
            )
        else:
            if admitted_values is None:
                raise AssertionError("admitted package operands are absent")
            admitted_prior, admitted_definitions, admitted_attributions = cast(
                tuple[
                    TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot,
                    tuple[DefinitionFragmentMovement, ...],
                    tuple[SourceAttributionFragmentMovement, ...],
                ],
                admitted_values,
            )
        decoded_nodes = None
        if _operation_context is not None:
            from .type_schema_operation import _type_schema_operation_decoded_nodes

            decoded_nodes = _type_schema_operation_decoded_nodes(  # type: ignore[arg-type]
                _operation_context
            )
        construction_started = perf_counter_ns()
        result, result_canonical_bytes = _transition_package(
            context,
            admitted_prior,
            definition_movements=admitted_definitions,
            attribution_movements=admitted_attributions,
            reader=reader,
            request_ref=request_ref,
            decoded_nodes=decoded_nodes,
        )
        construction_finished = perf_counter_ns()
        try:
            _require_meta_type_schema_operation_operands(
                context,
                operation_ref="composition.transition-package",
                operands=operands,
            )
        except TypeSchemaPersistentIndexError as error:
            raise TypeSchemaTransitionError(
                f"package transition operands changed after admission: {error}"
            ) from error
        verification_finished = perf_counter_ns()
    if _operation_context is not None:
        from .type_schema_operation import (
            _record_type_schema_operation_diagnostic,
            _record_type_schema_package_transition,
        )

        record_started = perf_counter_ns()
        _record_type_schema_package_transition(  # type: ignore[arg-type]
            _operation_context, result, result_canonical_bytes
        )
        record_finished = perf_counter_ns()
        for name, duration_ns in (
            ("meta_package_operand_admission", admission_finished - admission_started),
            ("meta_package_construction", construction_finished - construction_started),
            (
                "meta_package_terminal_verification",
                verification_finished - construction_finished,
            ),
            ("meta_package_result_record", record_finished - record_started),
        ):
            _record_type_schema_operation_diagnostic(
                _operation_context,  # type: ignore[arg-type]
                name,
                duration_ns,
            )
    return result


def _transition_package(
    context: _MetaTypeSchemaOperationContext,
    prior: TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot,
    *,
    definition_movements: tuple[DefinitionFragmentMovement, ...],
    attribution_movements: tuple[SourceAttributionFragmentMovement, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    decoded_nodes: dict[
        str,
        tuple[
            tuple[str, str, str, str, str, int, str, str],
            bytes,
            PersistentIndexNode,
        ],
    ]
    | None = None,
) -> tuple[TypeSchemaPackageTransition, bytes]:
    _require_meta_type_schema_operation(context)
    from .composition_codec import (
        decode_package_root,
        decode_source_attribution_fragment,
        encode_composition_value,
    )

    package = (
        prior.package
        if isinstance(prior, TypeSchemaTypedEmptyPackageAuthority)
        else prior
    )
    definitions = tuple(sorted(definition_movements, key=lambda item: item.type_ref))
    attributions = tuple(
        sorted(attribution_movements, key=lambda item: item.source_path)
    )
    if len({item.type_ref for item in definitions}) != len(definitions):
        raise TypeSchemaTransitionError("duplicate definition movement")
    if len({item.source_path for item in attributions}) != len(attributions):
        raise TypeSchemaTransitionError("duplicate attribution movement")
    if not definitions and not attributions:
        semantic = {
            "contract": PACKAGE_TRANSITION_CONTRACT,
            "prior": {
                "kind": (
                    "typed_empty"
                    if isinstance(prior, TypeSchemaTypedEmptyPackageAuthority)
                    else "package_root"
                ),
                "authority": prior.to_wire(),
            },
            "successor": package.to_wire(),
            "definition_lifecycle": [],
            "attribution_lifecycle": [],
            "definition_movement_refs": [],
            "attribution_movement_refs": [],
            "emitted_bodies": [],
            "reused_coordinates": [],
        }
        detached_successor = decode_package_root(encode_composition_value(package))
        if isinstance(prior, TypeSchemaTypedEmptyPackageAuthority):
            detached_prior: (
                TypeSchemaTypedEmptyPackageAuthority | TypeSchemaPackageRoot
            ) = TypeSchemaTypedEmptyPackageAuthority(
                decode_package_root(encode_composition_value(prior.package)),
                prior.empty_ref,
            )
        else:
            detached_prior = decode_package_root(encode_composition_value(prior))
        semantic_bytes = _prevalidated_json(semantic)
        return _create_prevalidated_package_transition(
            context,
            prior=detached_prior,
            successor=detached_successor,
            definition_lifecycle=(),
            attribution_lifecycle=(),
            definition_movement_refs=(),
            attribution_movement_refs=(),
            emitted_bodies=(),
            reused_coordinates=(),
            transition_ref="sha256:"
            + hashlib.sha256(
                PACKAGE_TRANSITION_CONTRACT.encode("utf-8")
                + b"\n"
                + semantic_bytes
            ).hexdigest(),
            observation=PositiveReadObservation(),
        ), semantic_bytes

    observation = PositiveReadObservation()
    prior_bindings: dict[str, PersistentBodyCoordinate] = {}
    next_bindings: dict[str, PersistentBodyCoordinate] = {}
    attribution_index_movements: list[IndexBindingMovement] = []
    attribution_lifecycle: list[SourceAttributionLifecycleEvidence] = []
    bodies: dict[str, PersistentBodyAuthority] = {}
    for movement in attributions:
        if movement.prior is not None:
            body, read_observation = reader.read_exact(
                request_ref=request_ref,
                expected=movement.prior,
                lookup_depth=0,
            )
            observation = observation.plus(read_observation)
            prior_value = decode_source_attribution_fragment(body.canonical_bytes)
            if (
                prior_value.package_ref != package.package_ref
                or prior_value.source_path != movement.source_path
            ):
                raise TypeSchemaTransitionError("prior attribution scope mismatch")
            for binding in prior_value.bindings:
                if binding.type_ref in prior_bindings:
                    raise TypeSchemaTransitionError("type has multiple prior sources")
                prior_bindings[binding.type_ref] = binding.definition
        next_coordinate = None
        if movement.next is not None:
            if movement.next.package_ref != package.package_ref:
                raise TypeSchemaTransitionError("next attribution package mismatch")
            body = _create_prevalidated_body_authority(
                context,
                schema=movement.next.contract,
                ref_field="attribution_ref",
                authority_ref=movement.next.attribution_ref,
                wire=movement.next.to_wire(),
            )
            bodies[body.coordinate.coordinate_ref] = body
            next_coordinate = body.coordinate
            for binding in movement.next.bindings:
                if binding.type_ref in next_bindings:
                    raise TypeSchemaTransitionError(
                        "type has multiple successor sources"
                    )
                next_bindings[binding.type_ref] = binding.definition
        attribution_index_movements.append(
            IndexBindingMovement(movement.source_path, movement.prior, next_coordinate)
        )
        attribution_lifecycle.append(
            SourceAttributionLifecycleEvidence.create(
                source_path=movement.source_path,
                prior=movement.prior,
                next=next_coordinate,
            )
        )

    definition_index_movements: list[IndexBindingMovement] = []
    definition_lifecycle: list[TypeDefinitionLifecycleEvidence] = []
    definition_refs: list[str] = []
    for movement in definitions:
        next_coordinate = None
        if movement.next is not None:
            body = _create_prevalidated_body_authority(
                context,
                schema=movement.next.contract,
                ref_field="fragment_ref",
                authority_ref=movement.next.fragment_ref,
                wire=movement.next.to_wire(),
            )
            bodies[body.coordinate.coordinate_ref] = body
            next_coordinate = body.coordinate
        if prior_bindings.get(movement.type_ref) != movement.prior:
            raise TypeSchemaTransitionError(
                "definition prior is not exactly source-attributed"
            )
        if next_bindings.get(movement.type_ref) != next_coordinate:
            raise TypeSchemaTransitionError(
                "definition successor is not exactly source-attributed"
            )
        definition_index_movements.append(
            IndexBindingMovement(movement.type_ref, movement.prior, next_coordinate)
        )
        lifecycle = TypeDefinitionLifecycleEvidence.create(
            type_ref=movement.type_ref,
            prior=movement.prior,
            next=next_coordinate,
        )
        definition_lifecycle.append(lifecycle)
        definition_refs.append(lifecycle.lifecycle_ref)
    changed_binding_types = {
        type_ref
        for type_ref in {*prior_bindings, *next_bindings}
        if prior_bindings.get(type_ref) != next_bindings.get(type_ref)
    }
    if changed_binding_types != {item.type_ref for item in definitions}:
        raise TypeSchemaTransitionError(
            "attribution binding changes and definition movements differ"
        )

    if decoded_nodes is None:
        decoded_nodes = {}
    definition_result = _patch_persistent_index_with_context(
        context,
        package.definition_index,
        movements=tuple(definition_index_movements),
        reader=reader,
        request_ref=request_ref,
        decoded_nodes=decoded_nodes,
    )
    attribution_result = _patch_persistent_index_with_context(
        context,
        package.source_attribution_index,
        movements=tuple(attribution_index_movements),
        reader=reader,
        request_ref=request_ref,
        decoded_nodes=decoded_nodes,
    )
    observation = observation.plus(definition_result.observation).plus(
        attribution_result.observation
    )
    for body in (*definition_result.emitted_bodies, *attribution_result.emitted_bodies):
        bodies[body.coordinate.coordinate_ref] = body
    successor = _create_prevalidated_package_root(
        context,
        package_ref=package.package_ref,
        package_name=package.package_name,
        namespace=package.namespace,
        semantic_version=package.semantic_version,
        dependency_package_refs=package.dependency_package_refs,
        definition_index=definition_result.root,
        source_attribution_index=attribution_result.root,
    )
    successor_body = _create_prevalidated_body_authority(
        context,
        schema=successor.contract,
        ref_field="package_root_ref",
        authority_ref=successor.package_root_ref,
        wire=successor.to_wire(),
    )
    bodies[successor_body.coordinate.coordinate_ref] = successor_body
    attribution_lifecycle = sorted(
        attribution_lifecycle, key=lambda value: value.source_path
    )
    attribution_refs = tuple(item.lifecycle_ref for item in attribution_lifecycle)
    reused = tuple(
        sorted(
            {
                value.coordinate_ref: value
                for value in (
                    *definition_result.reused_coordinates,
                    *attribution_result.reused_coordinates,
                )
            }.values(),
            key=lambda item: item.coordinate_ref,
        )
    )
    emitted = tuple(bodies[key] for key in sorted(bodies))
    semantic = {
        "contract": PACKAGE_TRANSITION_CONTRACT,
        "prior": {
            "kind": (
                "typed_empty"
                if isinstance(prior, TypeSchemaTypedEmptyPackageAuthority)
                else "package_root"
            ),
            "authority": prior.to_wire(),
        },
        "successor": successor.to_wire(),
        "definition_lifecycle": [
            item.to_wire()
            for item in sorted(definition_lifecycle, key=lambda value: value.type_ref)
        ],
        "attribution_lifecycle": [item.to_wire() for item in attribution_lifecycle],
        "definition_movement_refs": sorted(definition_refs),
        "attribution_movement_refs": sorted(attribution_refs),
    }
    semantic_bytes = _prevalidated_transition_semantic_bytes(
        semantic,
        emitted_bodies=emitted,
        reused_coordinates=reused,
        decoded_nodes=decoded_nodes,
    )
    return _create_prevalidated_package_transition(
        context,
        prior=prior,
        successor=successor,
        definition_lifecycle=tuple(
            sorted(definition_lifecycle, key=lambda item: item.type_ref)
        ),
        attribution_lifecycle=tuple(attribution_lifecycle),
        definition_movement_refs=tuple(sorted(definition_refs)),
        attribution_movement_refs=tuple(sorted(attribution_refs)),
        emitted_bodies=emitted,
        reused_coordinates=reused,
        transition_ref="sha256:"
        + hashlib.sha256(
            PACKAGE_TRANSITION_CONTRACT.encode("utf-8") + b"\n" + semantic_bytes
        ).hexdigest(),
        observation=observation,
    ), semantic_bytes


def transition_catalog(
    prior: TypeSchemaTypedEmptyCatalogAuthority | TypeSchemaCatalogRoot,
    *,
    package_movements: tuple[PackageRootMovement, ...],
    owner_movements: tuple[TypeOwnerBindingMovement, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    _operation_context: object | None = None,
) -> TypeSchemaCatalogTransition:
    operands = (prior, package_movements, owner_movements)
    _preflight_transition_operation(operands, reader, request_ref)
    admission_started = perf_counter_ns()
    admitted_packages = None
    projected_package_guard = False
    operation_guard_operands = operands
    if _operation_context is not None:
        from .type_schema_operation import _operation_bootstrap_package_movements

        admitted_packages = _operation_bootstrap_package_movements(
            _operation_context, package_movements
        )
        if admitted_packages is not None:
            projected_package_guard = True
            operation_guard_operands = (
                prior,
                tuple(
                    (
                        id(original),
                        original.package_ref,
                        original.prior,
                        id(original.next),
                        id(original.transition),
                    )
                    for original in package_movements
                ),
                owner_movements,
            )
    try:
        if _operation_context is None:
            operand_snapshot = _catalog_operation_snapshot(
                prior,
                package_movements,
                owner_movements,
            )
            admitted_guard_values = None
        else:
            admitted_guard, admitted_guard_values = _admit_and_detach_exact_graph(
                operation_guard_operands
            )
            operand_snapshot = (
                "composition.transition-catalog",
                admitted_guard,
            )
    except TypeSchemaPersistentIndexError as error:
        raise TypeSchemaTransitionError(
            f"transition operand admission failed: {error}"
        ) from error
    admission_finished = perf_counter_ns()
    with _meta_type_schema_operation(
        operation_ref="composition.transition-catalog",
        operands=operation_guard_operands,
        reader=reader,
        request_ref=request_ref,
        operand_snapshot=operand_snapshot,
    ) as context:
        if _operation_context is None:
            admitted_prior = _detached_catalog_prior(prior)
        else:
            if admitted_guard_values is None:
                raise AssertionError("admitted catalog operands are absent")
            admitted_prior = cast(
                tuple[object, object, object], admitted_guard_values
            )[0]
        if admitted_packages is None:
            admitted_packages = tuple(
                _detached_package_movement(context, value)
                for value in package_movements
            )
        admitted_packages = cast(tuple[PackageRootMovement, ...], admitted_packages)
        if _operation_context is not None:
            from .type_schema_operation import (
                _is_recorded_type_schema_package_successor,
                _record_type_schema_operation_detached_package_successor,
            )

            for original, detached in zip(
                package_movements, admitted_packages, strict=True
            ):
                if (
                    original.transition is not None
                    and detached.transition is not None
                    and _is_recorded_type_schema_package_successor(
                        _operation_context,  # type: ignore[arg-type]
                        original.transition,
                        original.transition.successor,
                    )
                ):
                    _record_type_schema_operation_detached_package_successor(
                        _operation_context,  # type: ignore[arg-type]
                        original.transition,
                        detached.transition,
                    )
        admitted_owners = (
            tuple(_detached_owner_movement(value) for value in owner_movements)
            if _operation_context is None
            else cast(
                tuple[TypeOwnerBindingMovement, ...],
                cast(tuple[object, object, object], admitted_guard_values)[2],
            )
        )
        decoded_nodes = None
        if _operation_context is not None:
            from .type_schema_operation import _type_schema_operation_decoded_nodes

            decoded_nodes = _type_schema_operation_decoded_nodes(  # type: ignore[arg-type]
                _operation_context
            )
        construction_started = perf_counter_ns()
        result, result_canonical_bytes = _transition_catalog(
            context,
            admitted_prior,
            package_movements=admitted_packages,
            owner_movements=admitted_owners,
            reader=reader,
            request_ref=request_ref,
            decoded_nodes=decoded_nodes,
            owner_operation=_operation_context,
        )
        construction_finished = perf_counter_ns()
        try:
            terminal_guard_operands = operands
            if projected_package_guard:
                terminal_guard_operands = (
                    prior,
                    tuple(
                        (
                            id(original),
                            original.package_ref,
                            original.prior,
                            id(original.next),
                            id(original.transition),
                        )
                        for original in package_movements
                    ),
                    owner_movements,
                )
            _require_meta_type_schema_operation_operands(
                context,
                operation_ref="composition.transition-catalog",
                operands=terminal_guard_operands,
            )
        except TypeSchemaPersistentIndexError as error:
            raise TypeSchemaTransitionError(
                f"catalog transition operands changed after admission: {error}"
            ) from error
        verification_finished = perf_counter_ns()
    if _operation_context is not None:
        from .type_schema_operation import (
            _record_type_schema_catalog_transition,
            _record_type_schema_operation_diagnostic,
        )

        record_started = perf_counter_ns()
        _record_type_schema_catalog_transition(  # type: ignore[arg-type]
            _operation_context, result, result_canonical_bytes
        )
        record_finished = perf_counter_ns()
        for name, duration_ns in (
            ("meta_catalog_operand_admission", admission_finished - admission_started),
            ("meta_catalog_construction", construction_finished - construction_started),
            (
                "meta_catalog_terminal_verification",
                verification_finished - construction_finished,
            ),
            ("meta_catalog_result_record", record_finished - record_started),
        ):
            _record_type_schema_operation_diagnostic(
                _operation_context,  # type: ignore[arg-type]
                name,
                duration_ns,
            )
    return result


def _transition_catalog(
    context: _MetaTypeSchemaOperationContext,
    prior: TypeSchemaTypedEmptyCatalogAuthority | TypeSchemaCatalogRoot,
    *,
    package_movements: tuple[PackageRootMovement, ...],
    owner_movements: tuple[TypeOwnerBindingMovement, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    decoded_nodes: dict[
        str,
        tuple[
            tuple[str, str, str, str, str, int, str, str],
            bytes,
            PersistentIndexNode,
        ],
    ]
    | None = None,
    owner_operation: object | None = None,
) -> tuple[TypeSchemaCatalogTransition, bytes]:
    _require_meta_type_schema_operation(context)
    from .composition_codec import (
        decode_catalog_root,
        decode_definition_fragment,
        decode_package_root,
        decode_source_attribution_fragment,
        decode_type_owner_binding,
        encode_composition_value,
    )

    catalog = (
        prior.catalog
        if isinstance(prior, TypeSchemaTypedEmptyCatalogAuthority)
        else prior
    )
    prior_ref = (
        prior.empty_ref
        if isinstance(prior, TypeSchemaTypedEmptyCatalogAuthority)
        else prior.catalog_ref
    )
    packages = tuple(sorted(package_movements, key=lambda item: item.package_ref))
    owners = tuple(sorted(owner_movements, key=lambda item: item.type_ref))
    if len({item.package_ref for item in packages}) != len(packages):
        raise TypeSchemaTransitionError("duplicate package movement")
    if len({item.type_ref for item in owners}) != len(owners):
        raise TypeSchemaTransitionError("duplicate owner movement")
    if not packages and not owners:
        semantic = {
            "contract": CATALOG_TRANSITION_CONTRACT,
            "prior_ref": prior_ref,
            "successor": catalog.to_wire(),
            "package_movement_refs": [],
            "owner_movement_refs": [],
            "emitted_bodies": [],
            "reused_coordinates": [],
        }
        detached_successor = decode_catalog_root(encode_composition_value(catalog))
        semantic_bytes = _prevalidated_json(semantic)
        return _create_prevalidated_catalog_transition(
            context,
            prior_ref=prior_ref,
            successor=detached_successor,
            package_movement_refs=(),
            owner_movement_refs=(),
            emitted_bodies=(),
            reused_coordinates=(),
            transition_ref="sha256:"
            + hashlib.sha256(
                CATALOG_TRANSITION_CONTRACT.encode("utf-8")
                + b"\n"
                + semantic_bytes
            ).hexdigest(),
            observation=PositiveReadObservation(),
        ), semantic_bytes

    observation = PositiveReadObservation()
    if decoded_nodes is None:
        decoded_nodes = {}

    def lookup(
        root,
        *,
        key: str,
    ):
        return _lookup_index_value_with_context(
            context,
            root,
            key=key,
            reader=reader,
            request_ref=request_ref,
            decoded_nodes=decoded_nodes,
        )

    prior_packages: dict[str, TypeSchemaPackageRoot] = {}
    package_movements_by_ref = {item.package_ref: item for item in packages}
    prior_owner_packages: dict[str, str] = {}
    next_owner_packages: dict[str, str] = {}
    transition_emitted_body_maps: dict[
        str,
        tuple[
            dict[str, int],
            tuple[object, ...],
            tuple[bytes, ...],
        ],
    ] = {}

    def is_recorded_successor(
        transition: TypeSchemaPackageTransition,
        package: TypeSchemaPackageRoot,
    ) -> bool:
        if owner_operation is None:
            return False
        from .type_schema_operation import (
            _is_recorded_type_schema_package_successor,
        )

        return _is_recorded_type_schema_package_successor(  # type: ignore[arg-type]
            owner_operation,
            transition,
            package,
        )
    for movement in packages:
        transition = movement.transition
        if transition is None:
            continue
        emitted_by_coordinate: dict[str, int] = {}
        emitted_coordinate_values: list[object] = []
        emitted_canonical_bodies: list[bytes] = []
        for body in transition.emitted_bodies:
            coordinate = body.coordinate
            if coordinate.coordinate_ref in emitted_by_coordinate:
                raise TypeSchemaTransitionError(
                    "package transition contains duplicate emitted body"
                )
            emitted_by_coordinate[coordinate.coordinate_ref] = len(
                emitted_canonical_bodies
            )
            emitted_coordinate_values.extend(
                (
                    coordinate.schema,
                    coordinate.ref_field,
                    coordinate.authority_ref,
                    coordinate.body_ref,
                    coordinate.body_digest,
                    coordinate.size_bytes,
                    coordinate.coordinate_ref,
                    coordinate.contract,
                )
            )
            emitted_canonical_bodies.append(body.canonical_bytes)
        transition_emitted_body_maps[transition.transition_ref] = (
            emitted_by_coordinate,
            tuple(emitted_coordinate_values),
            tuple(emitted_canonical_bodies),
        )

    def read_package_coordinate(
        coordinate: PersistentBodyCoordinate,
    ) -> TypeSchemaPackageRoot:
        nonlocal observation
        body, read_observation = reader.read_exact(
            request_ref=request_ref,
            expected=coordinate,
            lookup_depth=0,
        )
        observation = observation.plus(read_observation)
        package = decode_package_root(body.canonical_bytes)
        if package.to_body().coordinate != coordinate:
            raise TypeSchemaTransitionError(
                "package coordinate does not bind exact package root"
            )
        return package

    def prior_package_for(
        movement: PackageRootMovement,
    ) -> TypeSchemaPackageRoot | None:
        nonlocal observation
        actual, lookup_observation = lookup(
            catalog.package_index,
            key=movement.package_ref,
        )
        observation = observation.plus(lookup_observation)
        if actual != movement.prior:
            raise TypeSchemaTransitionError(
                "package movement prior differs from catalog binding"
            )
        if actual is None:
            return None
        package = read_package_coordinate(actual)
        if package.package_ref != movement.package_ref:
            raise TypeSchemaTransitionError("prior package key/body mismatch")
        prior_packages[movement.package_ref] = package
        return package

    def read_transition_body(
        transition: TypeSchemaPackageTransition,
        coordinate: PersistentBodyCoordinate,
    ) -> PersistentBodyAuthority:
        nonlocal observation
        emitted_by_coordinate, coordinate_values, canonical_bodies = (
            transition_emitted_body_maps[transition.transition_ref]
        )
        emitted_index = emitted_by_coordinate.get(coordinate.coordinate_ref)
        if emitted_index is not None:
            value_index = emitted_index * 8
            if (
                coordinate_values[value_index] != coordinate.schema
                or coordinate_values[value_index + 1] != coordinate.ref_field
                or coordinate_values[value_index + 2] != coordinate.authority_ref
                or coordinate_values[value_index + 3] != coordinate.body_ref
                or coordinate_values[value_index + 4] != coordinate.body_digest
                or coordinate_values[value_index + 5] != coordinate.size_bytes
                or coordinate_values[value_index + 6] != coordinate.coordinate_ref
                or coordinate_values[value_index + 7] != coordinate.contract
            ):
                raise TypeSchemaTransitionError("emitted body coordinate substitution")
            result = object.__new__(PersistentBodyAuthority)
            object.__setattr__(
                result,
                "coordinate",
                _detached_prevalidated_coordinate(context, coordinate),
            )
            object.__setattr__(
                result, "canonical_bytes", canonical_bodies[emitted_index]
            )
            return result
        body, read_observation = reader.read_exact(
            request_ref=request_ref,
            expected=coordinate,
            lookup_depth=0,
        )
        observation = observation.plus(read_observation)
        return body

    def require_definition_binding(
        transition: TypeSchemaPackageTransition,
        package: TypeSchemaPackageRoot,
        *,
        type_ref: str,
        expected: PersistentBodyCoordinate,
    ) -> None:
        nonlocal observation
        if not is_recorded_successor(transition, package):
            actual, lookup_observation = lookup(
                package.definition_index,
                key=type_ref,
            )
            observation = observation.plus(lookup_observation)
            if actual != expected:
                raise TypeSchemaTransitionError(
                    "definition lifecycle differs from package index binding"
                )
        fragment = decode_definition_fragment(
            read_transition_body(transition, expected).canonical_bytes
        )
        if fragment.type_ref != type_ref:
            raise TypeSchemaTransitionError(
                "definition lifecycle key differs from fragment type_ref"
            )

    def attribution_bindings(
        transition: TypeSchemaPackageTransition,
        package: TypeSchemaPackageRoot,
        *,
        prior_side: bool,
    ) -> dict[str, PersistentBodyCoordinate]:
        nonlocal observation
        result: dict[str, PersistentBodyCoordinate] = {}
        recorded_successor = (
            not prior_side and is_recorded_successor(transition, package)
        )
        for lifecycle in transition.attribution_lifecycle:
            coordinate = lifecycle.prior if prior_side else lifecycle.next
            if coordinate is None:
                continue
            if not recorded_successor:
                actual, lookup_observation = lookup(
                    package.source_attribution_index,
                    key=lifecycle.source_path,
                )
                observation = observation.plus(lookup_observation)
                if actual != coordinate:
                    raise TypeSchemaTransitionError(
                        "attribution lifecycle differs from package index binding"
                    )
            attribution = decode_source_attribution_fragment(
                read_transition_body(transition, coordinate).canonical_bytes
            )
            if (
                attribution.package_ref != package.package_ref
                or attribution.source_path != lifecycle.source_path
            ):
                raise TypeSchemaTransitionError(
                    "attribution lifecycle key/body scope mismatch"
                )
            for binding in attribution.bindings:
                if binding.type_ref in result:
                    raise TypeSchemaTransitionError(
                        "attribution lifecycle contains duplicate type ownership"
                    )
                result[binding.type_ref] = binding.definition
        return result

    for movement in packages:
        prior_package = prior_package_for(movement)
        if movement.next is None:
            if prior_package is None:
                raise TypeSchemaTransitionError(
                    "package deletion requires exact prior package"
                )
            continue
        transition = movement.transition
        if transition is None:
            raise TypeSchemaTransitionError(
                "package successor requires exact package transition"
            )
        if prior_package is None:
            if not isinstance(transition.prior, TypeSchemaTypedEmptyPackageAuthority):
                raise TypeSchemaTransitionError(
                    "created package transition requires typed-empty predecessor"
                )
            empty_package = transition.prior.package
            if (
                empty_package.package_ref != movement.package_ref
                or empty_package.package_name != movement.next.package_name
                or empty_package.namespace != movement.next.namespace
                or empty_package.semantic_version != movement.next.semantic_version
                or empty_package.dependency_package_refs
                != movement.next.dependency_package_refs
            ):
                raise TypeSchemaTransitionError(
                    "created package transition has foreign typed-empty predecessor"
                )
            if any(item.prior is not None for item in transition.definition_lifecycle):
                raise TypeSchemaTransitionError(
                    "created package lifecycle contains prior definitions"
                )
            if (
                len(transition.definition_lifecycle)
                != movement.next.definition_index.binding_count
            ):
                raise TypeSchemaTransitionError(
                    "created package lifecycle is not definition-complete"
                )
        elif transition.prior != prior_package:
            raise TypeSchemaTransitionError(
                "package transition does not bind exact prior package"
            )
        definition_lifecycle_by_ref = {
            lifecycle.type_ref: lifecycle
            for lifecycle in transition.definition_lifecycle
        }
        prior_attribution_bindings = (
            {}
            if prior_package is None
            else attribution_bindings(transition, prior_package, prior_side=True)
        )
        next_attribution_bindings = attribution_bindings(
            transition, movement.next, prior_side=False
        )
        changed_attribution_types = {
            type_ref
            for type_ref in {
                *prior_attribution_bindings,
                *next_attribution_bindings,
            }
            if prior_attribution_bindings.get(type_ref)
            != next_attribution_bindings.get(type_ref)
        }
        if changed_attribution_types != set(definition_lifecycle_by_ref):
            raise TypeSchemaTransitionError(
                "definition and source-attribution binding deltas differ"
            )
        for type_ref, lifecycle in definition_lifecycle_by_ref.items():
            if (
                prior_attribution_bindings.get(type_ref) != lifecycle.prior
                or next_attribution_bindings.get(type_ref) != lifecycle.next
            ):
                raise TypeSchemaTransitionError(
                    "definition and source-attribution lifecycle values differ"
                )
        for lifecycle in transition.definition_lifecycle:
            if lifecycle.prior is not None:
                if prior_package is None:
                    raise TypeSchemaTransitionError(
                        "definition prior exists without prior package"
                    )
                require_definition_binding(
                    transition,
                    prior_package,
                    type_ref=lifecycle.type_ref,
                    expected=lifecycle.prior,
                )
                if lifecycle.type_ref in prior_owner_packages:
                    raise TypeSchemaTransitionError(
                        "type has multiple prior package lifecycles"
                    )
                prior_owner_packages[lifecycle.type_ref] = movement.package_ref
            if lifecycle.next is not None:
                require_definition_binding(
                    transition,
                    movement.next,
                    type_ref=lifecycle.type_ref,
                    expected=lifecycle.next,
                )
                if lifecycle.type_ref in next_owner_packages:
                    raise TypeSchemaTransitionError(
                        "type has multiple successor package lifecycles"
                    )
                next_owner_packages[lifecycle.type_ref] = movement.package_ref

    decoded_prior_owners: dict[str, TypeOwnerBinding | None] = {}
    for movement in owners:
        actual, lookup_observation = lookup(
            catalog.owner_index,
            key=movement.type_ref,
        )
        observation = observation.plus(lookup_observation)
        if actual != movement.prior:
            raise TypeSchemaTransitionError(
                "owner movement prior differs from catalog binding"
            )
        prior_owner = None
        if actual is not None:
            body, read_observation = reader.read_exact(
                request_ref=request_ref,
                expected=actual,
                lookup_depth=0,
            )
            observation = observation.plus(read_observation)
            prior_owner = decode_type_owner_binding(body.canonical_bytes)
            if prior_owner.type_ref != movement.type_ref:
                raise TypeSchemaTransitionError("prior owner key/body mismatch")
        decoded_prior_owners[movement.type_ref] = prior_owner

    deleted_package_refs = {
        movement.package_ref for movement in packages if movement.next is None
    }
    for package_ref in deleted_package_refs:
        prior_package = prior_packages[package_ref]
        affected_values: list[tuple[TypeOwnerBindingMovement, TypeOwnerBinding]] = []
        for movement in owners:
            prior_owner = decoded_prior_owners[movement.type_ref]
            if prior_owner is not None and prior_owner.package_ref == package_ref:
                affected_values.append((movement, prior_owner))
        affected = tuple(affected_values)
        if len(affected) != prior_package.definition_index.binding_count:
            raise TypeSchemaTransitionError(
                "package deletion does not move every owned definition"
            )
        for owner_movement, prior_owner in affected:
            if prior_owner is None:
                raise TypeSchemaTransitionError("deleted package owner is absent")
            definition_coordinate, lookup_observation = lookup(
                prior_package.definition_index,
                key=owner_movement.type_ref,
            )
            observation = observation.plus(lookup_observation)
            if definition_coordinate is None:
                raise TypeSchemaTransitionError(
                    "deleted package owner lacks prior definition"
                )
            if owner_movement.type_ref in prior_owner_packages:
                raise TypeSchemaTransitionError(
                    "type has duplicate prior lifecycle evidence"
                )
            prior_owner_packages[owner_movement.type_ref] = package_ref

    changed_owner_types = {
        type_ref
        for type_ref in {*prior_owner_packages, *next_owner_packages}
        if prior_owner_packages.get(type_ref) != next_owner_packages.get(type_ref)
    }
    if {item.type_ref for item in owners} != changed_owner_types:
        raise TypeSchemaTransitionError(
            "definition lifecycle and owner movements differ"
        )
    for movement in owners:
        prior_owner = decoded_prior_owners[movement.type_ref]
        expected_prior_package = prior_owner_packages.get(movement.type_ref)
        expected_next_package = next_owner_packages.get(movement.type_ref)
        if (
            None if prior_owner is None else prior_owner.package_ref
        ) != expected_prior_package:
            raise TypeSchemaTransitionError(
                "owner prior does not match definition lifecycle"
            )
        if (
            None if movement.next is None else movement.next.package_ref
        ) != expected_next_package:
            raise TypeSchemaTransitionError(
                "owner successor does not match definition lifecycle"
            )

    retained_package_cache: dict[str, TypeSchemaPackageRoot] = {}

    def successor_package(package_ref: str) -> TypeSchemaPackageRoot:
        nonlocal observation
        moved = package_movements_by_ref.get(package_ref)
        if moved is not None:
            if moved.next is None:
                raise TypeSchemaTransitionError(
                    f"successor package is deleted: {package_ref!r}"
                )
            return moved.next
        cached = retained_package_cache.get(package_ref)
        if cached is not None:
            return cached
        coordinate, lookup_observation = lookup(
            catalog.package_index,
            key=package_ref,
        )
        observation = observation.plus(lookup_observation)
        if coordinate is None:
            raise TypeSchemaTransitionError(
                f"successor package is absent: {package_ref!r}"
            )
        package = read_package_coordinate(coordinate)
        if package.package_ref != package_ref:
            raise TypeSchemaTransitionError("retained package key/body mismatch")
        retained_package_cache[package_ref] = package
        return package

    reachable_packages: set[str] = set()
    visiting_packages: set[str] = set()

    def visit_successor_package(package_ref: str) -> None:
        if package_ref in visiting_packages:
            raise TypeSchemaTransitionError("successor package dependency cycle")
        if package_ref in reachable_packages:
            return
        visiting_packages.add(package_ref)
        package = successor_package(package_ref)
        for dependency_ref in package.dependency_package_refs:
            visit_successor_package(dependency_ref)
        visiting_packages.remove(package_ref)
        reachable_packages.add(package_ref)

    visit_successor_package(catalog.target_package_ref)
    if any(
        movement.next is not None and movement.package_ref not in reachable_packages
        for movement in packages
    ):
        raise TypeSchemaTransitionError(
            "successor package movement is outside target-reachable closure"
        )
    if any(
        package_ref not in reachable_packages
        for package_ref in next_owner_packages.values()
    ):
        raise TypeSchemaTransitionError(
            "successor owner package is outside target-reachable closure"
        )

    bodies: dict[str, PersistentBodyAuthority] = {}
    package_index_movements: list[IndexBindingMovement] = []
    package_refs: list[str] = []
    for movement in packages:
        next_coordinate = None
        if movement.next is not None:
            body = _create_prevalidated_body_authority(
                context,
                schema=movement.next.contract,
                ref_field="package_root_ref",
                authority_ref=movement.next.package_root_ref,
                wire=movement.next.to_wire(),
            )
            bodies[body.coordinate.coordinate_ref] = body
            next_coordinate = body.coordinate
        package_index_movements.append(
            IndexBindingMovement(movement.package_ref, movement.prior, next_coordinate)
        )
        package_refs.append(
            _prevalidated_digest(
                "aware.meta.type-schema.package-root-movement.v1",
                {
                    "package_ref": movement.package_ref,
                    "prior": (
                        None if movement.prior is None else movement.prior.to_wire()
                    ),
                    "next": (
                        None if next_coordinate is None else next_coordinate.to_wire()
                    ),
                },
            )
        )
    owner_index_movements: list[IndexBindingMovement] = []
    owner_refs: list[str] = []
    for movement in owners:
        next_coordinate = None
        if movement.next is not None:
            body = _create_prevalidated_body_authority(
                context,
                schema=movement.next.contract,
                ref_field="owner_ref",
                authority_ref=movement.next.owner_ref,
                wire=movement.next.to_wire(),
            )
            bodies[body.coordinate.coordinate_ref] = body
            next_coordinate = body.coordinate
        owner_index_movements.append(
            IndexBindingMovement(movement.type_ref, movement.prior, next_coordinate)
        )
        owner_refs.append(
            _prevalidated_digest(
                "aware.meta.type-schema.owner-movement.v1",
                {
                    "type_ref": movement.type_ref,
                    "prior": (
                        None if movement.prior is None else movement.prior.to_wire()
                    ),
                    "next": (
                        None if next_coordinate is None else next_coordinate.to_wire()
                    ),
                },
            )
        )
    package_result = _patch_persistent_index_with_context(
        context,
        catalog.package_index,
        movements=tuple(package_index_movements),
        reader=reader,
        request_ref=request_ref,
        decoded_nodes=decoded_nodes,
    )
    owner_result = _patch_persistent_index_with_context(
        context,
        catalog.owner_index,
        movements=tuple(owner_index_movements),
        reader=reader,
        request_ref=request_ref,
        decoded_nodes=decoded_nodes,
    )
    for body in (*package_result.emitted_bodies, *owner_result.emitted_bodies):
        bodies[body.coordinate.coordinate_ref] = body
    successor = _create_prevalidated_catalog_root(
        context,
        target_package_ref=catalog.target_package_ref,
        package_index=package_result.root,
        owner_index=owner_result.root,
    )
    reused = tuple(
        sorted(
            {
                value.coordinate_ref: value
                for value in (
                    *package_result.reused_coordinates,
                    *owner_result.reused_coordinates,
                )
            }.values(),
            key=lambda item: item.coordinate_ref,
        )
    )
    emitted = tuple(bodies[key] for key in sorted(bodies))
    semantic = {
        "contract": CATALOG_TRANSITION_CONTRACT,
        "prior_ref": prior_ref,
        "successor": successor.to_wire(),
        "package_movement_refs": sorted(package_refs),
        "owner_movement_refs": sorted(owner_refs),
    }
    semantic_bytes = _prevalidated_transition_semantic_bytes(
        semantic,
        emitted_bodies=emitted,
        reused_coordinates=reused,
        decoded_nodes=decoded_nodes,
    )
    return _create_prevalidated_catalog_transition(
        context,
        prior_ref=prior_ref,
        successor=successor,
        package_movement_refs=tuple(sorted(package_refs)),
        owner_movement_refs=tuple(sorted(owner_refs)),
        emitted_bodies=emitted,
        reused_coordinates=reused,
        transition_ref="sha256:"
        + hashlib.sha256(
            CATALOG_TRANSITION_CONTRACT.encode("utf-8") + b"\n" + semantic_bytes
        ).hexdigest(),
        observation=observation.plus(package_result.observation).plus(
            owner_result.observation
        ),
    ), semantic_bytes


__all__ = [
    "CATALOG_TRANSITION_CONTRACT",
    "PACKAGE_TRANSITION_CONTRACT",
    "TYPED_EMPTY_CATALOG_CONTRACT",
    "TYPED_EMPTY_PACKAGE_CONTRACT",
    "DefinitionFragmentMovement",
    "PackageRootMovement",
    "SourceAttributionFragmentMovement",
    "SourceAttributionLifecycleEvidence",
    "TypeDefinitionLifecycleEvidence",
    "TypeOwnerBindingMovement",
    "TypeSchemaCatalogTransition",
    "TypeSchemaPackageTransition",
    "TypeSchemaTransitionError",
    "TypeSchemaTypedEmptyCatalogAuthority",
    "TypeSchemaTypedEmptyPackageAuthority",
    "create_typed_empty_catalog",
    "create_typed_empty_package",
    "transition_catalog",
    "transition_package",
]
