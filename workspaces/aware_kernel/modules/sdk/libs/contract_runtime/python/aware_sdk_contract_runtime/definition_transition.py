from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum

from aware_meta_type_schema import FrozenJson, canonical_json

from .definition import SdkDefinitionState
from .validation import validate_sdk_definition_state_graph

SDK_DEFINITION_TRANSITION = "aware.sdk.definition-transition.v1"
SDK_PREPARED_DEFINITION_EFFECT = "aware.sdk.prepared-definition-effect.v1"


def _sha256(contract: str, purpose: str, value: object) -> str:
    body = f"{contract}\n{purpose}\n{canonical_json(value)}".encode("utf-8")
    return f"sha256:{hashlib.sha256(body).hexdigest()}"


def _token(value: object, field: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or any(character.isspace() for character in value)
    ):
        raise ValueError(f"{field} must be an exact normalized nonempty token")
    return value


class SdkDefinitionPredecessorKind(StrEnum):
    TYPED_EMPTY = "typed_empty"
    DEFINITION = "definition"


class SdkDefinitionSemanticKind(StrEnum):
    MANIFEST_METADATA = "manifest_metadata"
    TARGET = "target"
    SCHEMA_SLICE = "schema_slice"
    SCHEMA = "schema"
    OPERATION = "operation"
    METHOD = "method"
    INVENTORY_OPERATION = "inventory_operation"
    INVENTORY_METHOD = "inventory_method"


class SdkDefinitionMovementOperation(StrEnum):
    ADD = "add"
    CHANGE = "change"
    REMOVE = "remove"


_ARITY = {
    SdkDefinitionSemanticKind.MANIFEST_METADATA: 1,
    SdkDefinitionSemanticKind.TARGET: 1,
    SdkDefinitionSemanticKind.SCHEMA_SLICE: 1,
    SdkDefinitionSemanticKind.SCHEMA: 2,
    SdkDefinitionSemanticKind.OPERATION: 1,
    SdkDefinitionSemanticKind.METHOD: 1,
    SdkDefinitionSemanticKind.INVENTORY_OPERATION: 1,
    SdkDefinitionSemanticKind.INVENTORY_METHOD: 1,
}


@dataclass(frozen=True, slots=True)
class SdkDefinitionSemanticCoordinate:
    kind: SdkDefinitionSemanticKind
    parts: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.kind) is not SdkDefinitionSemanticKind:
            raise TypeError("coordinate kind must be exact SdkDefinitionSemanticKind")
        if type(self.parts) is not tuple:
            raise TypeError("coordinate parts must be an exact tuple")
        parts = tuple(_token(value, "coordinate part") for value in self.parts)
        if len(parts) != _ARITY[self.kind]:
            raise ValueError(f"{self.kind.value} coordinate requires {_ARITY[self.kind]} parts")
        if self.kind is SdkDefinitionSemanticKind.MANIFEST_METADATA and parts != ("semantic_version",):
            raise ValueError("manifest_metadata coordinate must select semantic_version")
        object.__setattr__(self, "parts", parts)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"kind": self.kind.value, "parts": list(self.parts)}

    def order_key(self) -> bytes:
        return canonical_json(self.to_wire()).encode("utf-8")


def _member_digest(
    coordinate: SdkDefinitionSemanticCoordinate, body: FrozenJson
) -> str:
    if type(coordinate) is not SdkDefinitionSemanticCoordinate:
        raise TypeError("coordinate must be exact SdkDefinitionSemanticCoordinate")
    if type(body) is not FrozenJson:
        raise TypeError("body must be exact FrozenJson")
    return _sha256(
        SDK_DEFINITION_TRANSITION,
        "semantic-member",
        {"coordinate": coordinate.to_wire(), "body": body.to_wire()},
    )


@dataclass(frozen=True, slots=True, init=False)
class SdkDefinitionMovement:
    coordinate: SdkDefinitionSemanticCoordinate
    operation: SdkDefinitionMovementOperation
    predecessor_body: FrozenJson | None
    predecessor_digest: str | None
    result_body: FrozenJson | None
    result_digest: str | None

    def __init__(
        self,
        coordinate: SdkDefinitionSemanticCoordinate,
        predecessor_body: FrozenJson | None,
        result_body: FrozenJson | None,
    ) -> None:
        if type(coordinate) is not SdkDefinitionSemanticCoordinate:
            raise TypeError("coordinate must be exact SdkDefinitionSemanticCoordinate")
        if predecessor_body is not None and type(predecessor_body) is not FrozenJson:
            raise TypeError("predecessor_body must be exact FrozenJson or None")
        if result_body is not None and type(result_body) is not FrozenJson:
            raise TypeError("result_body must be exact FrozenJson or None")
        if predecessor_body is None and result_body is None:
            raise ValueError("movement requires a predecessor or result body")
        if predecessor_body is not None and result_body is not None:
            if predecessor_body.canonical == result_body.canonical:
                raise ValueError("equal semantic bodies do not produce a movement")
            operation = SdkDefinitionMovementOperation.CHANGE
        elif predecessor_body is None:
            operation = SdkDefinitionMovementOperation.ADD
        else:
            operation = SdkDefinitionMovementOperation.REMOVE
        object.__setattr__(self, "coordinate", coordinate)
        object.__setattr__(self, "operation", operation)
        object.__setattr__(self, "predecessor_body", predecessor_body)
        object.__setattr__(self, "predecessor_digest", None if predecessor_body is None else _member_digest(coordinate, predecessor_body))
        object.__setattr__(self, "result_body", result_body)
        object.__setattr__(self, "result_digest", None if result_body is None else _member_digest(coordinate, result_body))

    def to_wire(self) -> dict[str, object]:
        if type(self.coordinate) is not SdkDefinitionSemanticCoordinate:
            raise TypeError("movement coordinate must be exact")
        self.coordinate.__post_init__()
        if type(self.operation) is not SdkDefinitionMovementOperation:
            raise TypeError("movement operation must be exact")
        expected = SdkDefinitionMovement(self.coordinate, self.predecessor_body, self.result_body)
        if self.predecessor_digest != expected.predecessor_digest or self.result_digest != expected.result_digest or self.operation is not expected.operation:
            raise ValueError("movement differs from fresh semantic derivation")
        return {
            "coordinate": self.coordinate.to_wire(),
            "operation": self.operation.value,
            "predecessor_body": None if self.predecessor_body is None else self.predecessor_body.to_wire(),
            "predecessor_digest": self.predecessor_digest,
            "result_body": None if self.result_body is None else self.result_body.to_wire(),
            "result_digest": self.result_digest,
        }


def _coordinate(
    kind: SdkDefinitionSemanticKind, *parts: str
) -> SdkDefinitionSemanticCoordinate:
    return SdkDefinitionSemanticCoordinate(kind, parts)


def _body(value: object) -> FrozenJson:
    return FrozenJson.from_value(value)


def _catalog(
    state: SdkDefinitionState,
) -> dict[SdkDefinitionSemanticCoordinate, FrozenJson]:
    validate_sdk_definition_state_graph(state)
    result: dict[SdkDefinitionSemanticCoordinate, FrozenJson] = {}

    def add(coordinate: SdkDefinitionSemanticCoordinate, body: object) -> None:
        if coordinate in result:
            raise ValueError(f"duplicate semantic coordinate {coordinate.to_wire()!r}")
        result[coordinate] = _body(body)

    manifest = state.manifest
    add(
        _coordinate(SdkDefinitionSemanticKind.MANIFEST_METADATA, "semantic_version"),
        {"semantic_version": manifest.semantic_version},
    )
    for target in manifest.targets:
        add(_coordinate(SdkDefinitionSemanticKind.TARGET, target.language), target.to_wire())
    for schema_slice in manifest.schema_slices:
        add(_coordinate(SdkDefinitionSemanticKind.SCHEMA_SLICE, schema_slice.slice_digest), schema_slice.to_wire())
        for definition in schema_slice.types:
            add(_coordinate(SdkDefinitionSemanticKind.SCHEMA, schema_slice.slice_digest, definition.type_ref), definition.to_wire())
    for operation in manifest.operations:
        add(_coordinate(SdkDefinitionSemanticKind.OPERATION, operation.operation_ref), operation.to_wire())
    for method in manifest.methods:
        add(_coordinate(SdkDefinitionSemanticKind.METHOD, method.method_ref), method.to_wire())
    for operation in state.inventory.operations:
        add(_coordinate(SdkDefinitionSemanticKind.INVENTORY_OPERATION, operation.operation_ref), operation.to_wire())
    for method in state.inventory.methods:
        add(_coordinate(SdkDefinitionSemanticKind.INVENTORY_METHOD, method.method_ref), method.to_wire())
    return result


def _movements(
    predecessor: dict[SdkDefinitionSemanticCoordinate, FrozenJson],
    result: dict[SdkDefinitionSemanticCoordinate, FrozenJson],
) -> tuple[SdkDefinitionMovement, ...]:
    values: list[SdkDefinitionMovement] = []
    for coordinate in sorted(set(predecessor) | set(result), key=lambda item: item.order_key()):
        before = predecessor.get(coordinate)
        after = result.get(coordinate)
        if before is not None and after is not None and before.canonical == after.canonical:
            continue
        values.append(SdkDefinitionMovement(coordinate, before, after))
    return tuple(values)


@dataclass(frozen=True, slots=True, init=False)
class SdkDefinitionTransition:
    sdk_ref: str
    predecessor_kind: SdkDefinitionPredecessorKind
    predecessor_definition_digest: str | None
    result_definition_digest: str
    predecessor_manifest_digest: str | None
    result_manifest_digest: str
    predecessor_inventory_digest: str | None
    result_inventory_digest: str
    movements: tuple[SdkDefinitionMovement, ...]
    transition_digest: str
    contract: str

    def __init__(
        self, predecessor: SdkDefinitionState | None, result: SdkDefinitionState
    ) -> None:
        validate_sdk_definition_state_graph(result, "result")
        if predecessor is not None:
            validate_sdk_definition_state_graph(predecessor, "predecessor")
            if predecessor.manifest.sdk_ref != result.manifest.sdk_ref:
                raise ValueError("predecessor and result sdk_ref must match")
        before_catalog = {} if predecessor is None else _catalog(predecessor)
        after_catalog = _catalog(result)
        movements = _movements(before_catalog, after_catalog)
        object.__setattr__(self, "sdk_ref", result.manifest.sdk_ref)
        object.__setattr__(self, "predecessor_kind", SdkDefinitionPredecessorKind.TYPED_EMPTY if predecessor is None else SdkDefinitionPredecessorKind.DEFINITION)
        object.__setattr__(self, "predecessor_definition_digest", None if predecessor is None else predecessor.definition_digest)
        object.__setattr__(self, "result_definition_digest", result.definition_digest)
        object.__setattr__(self, "predecessor_manifest_digest", None if predecessor is None else predecessor.manifest.manifest_digest)
        object.__setattr__(self, "result_manifest_digest", result.manifest.manifest_digest)
        object.__setattr__(self, "predecessor_inventory_digest", None if predecessor is None else predecessor.inventory.inventory_digest)
        object.__setattr__(self, "result_inventory_digest", result.inventory.inventory_digest)
        object.__setattr__(self, "movements", movements)
        object.__setattr__(self, "contract", SDK_DEFINITION_TRANSITION)
        object.__setattr__(self, "transition_digest", _sha256(SDK_DEFINITION_TRANSITION, "transition", self._wire_without_digest()))

    def _wire_without_digest(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "sdk_ref": self.sdk_ref,
            "predecessor_kind": self.predecessor_kind.value,
            "predecessor_definition_digest": self.predecessor_definition_digest,
            "result_definition_digest": self.result_definition_digest,
            "predecessor_manifest_digest": self.predecessor_manifest_digest,
            "result_manifest_digest": self.result_manifest_digest,
            "predecessor_inventory_digest": self.predecessor_inventory_digest,
            "result_inventory_digest": self.result_inventory_digest,
            "movements": [value.to_wire() for value in self.movements],
        }

    def to_wire(
        self, *, predecessor: SdkDefinitionState | None, result: SdkDefinitionState
    ) -> dict[str, object]:
        if type(self) is not SdkDefinitionTransition:
            raise TypeError("transition must be exact SdkDefinitionTransition")
        expected = SdkDefinitionTransition(predecessor, result)
        if canonical_json(self._wire_without_digest()) != canonical_json(expected._wire_without_digest()) or self.transition_digest != expected.transition_digest:
            raise ValueError("transition differs from fresh supplied-state derivation")
        return {**expected._wire_without_digest(), "transition_digest": expected.transition_digest}


@dataclass(frozen=True, slots=True, init=False)
class SdkPreparedDefinitionEffect:
    transition_digest: str
    predecessor_definition_digest: str | None
    result_definition_digest: str
    result_state: SdkDefinitionState
    movements: tuple[SdkDefinitionMovement, ...]
    effect_digest: str
    contract: str

    def __init__(
        self, predecessor: SdkDefinitionState | None, result: SdkDefinitionState
    ) -> None:
        transition = SdkDefinitionTransition(predecessor, result)
        object.__setattr__(self, "transition_digest", transition.transition_digest)
        object.__setattr__(self, "predecessor_definition_digest", transition.predecessor_definition_digest)
        object.__setattr__(self, "result_definition_digest", result.definition_digest)
        object.__setattr__(self, "result_state", result)
        object.__setattr__(self, "movements", transition.movements)
        object.__setattr__(self, "contract", SDK_PREPARED_DEFINITION_EFFECT)
        object.__setattr__(self, "effect_digest", _sha256(SDK_PREPARED_DEFINITION_EFFECT, "effect", self._wire_without_digest()))

    def _wire_without_digest(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "transition_digest": self.transition_digest,
            "predecessor_definition_digest": self.predecessor_definition_digest,
            "result_definition_digest": self.result_definition_digest,
            "result_state": self.result_state.to_wire(),
            "movements": [value.to_wire() for value in self.movements],
        }

    def to_wire(
        self, *, predecessor: SdkDefinitionState | None, result: SdkDefinitionState
    ) -> dict[str, object]:
        if type(self) is not SdkPreparedDefinitionEffect:
            raise TypeError("effect must be exact SdkPreparedDefinitionEffect")
        expected = SdkPreparedDefinitionEffect(predecessor, result)
        if canonical_json(self._wire_without_digest()) != canonical_json(expected._wire_without_digest()) or self.effect_digest != expected.effect_digest:
            raise ValueError("effect differs from fresh supplied-state derivation")
        return {**expected._wire_without_digest(), "effect_digest": expected.effect_digest}


def derive_sdk_definition_transition(
    predecessor: SdkDefinitionState | None, result: SdkDefinitionState
) -> SdkDefinitionTransition:
    return SdkDefinitionTransition(predecessor, result)


def prepare_sdk_definition_effect(
    predecessor: SdkDefinitionState | None, result: SdkDefinitionState
) -> SdkPreparedDefinitionEffect:
    return SdkPreparedDefinitionEffect(predecessor, result)


__all__ = [
    "SDK_DEFINITION_TRANSITION",
    "SDK_PREPARED_DEFINITION_EFFECT",
    "SdkDefinitionMovement",
    "SdkDefinitionMovementOperation",
    "SdkDefinitionPredecessorKind",
    "SdkDefinitionSemanticCoordinate",
    "SdkDefinitionSemanticKind",
    "SdkDefinitionTransition",
    "SdkPreparedDefinitionEffect",
    "derive_sdk_definition_transition",
    "prepare_sdk_definition_effect",
]
