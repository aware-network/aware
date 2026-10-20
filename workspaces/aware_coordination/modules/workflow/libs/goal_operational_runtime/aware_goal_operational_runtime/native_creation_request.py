"""Authored native creation requests, not qualified plans or created Goals.

Reuse the owning definition/Gate/dependency codecs. No source resolution,
ownership issuance, lifecycle effect, document rendering or publication occurs.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import cast

from .identity import fingerprint, normalize_goal_tag, required_token
from .phase_codec import decode_goal_phase_bundle, goal_phase_bundle_to_wire
from .phase_contracts import GOAL_PHASE_BUNDLE_SCHEMA, GoalPhaseCoordinate
from .phase_document import (
    GoalLanePhaseDefinitionV1,
    _decode_definition, _decode_unresolved, _definition_wire, _unresolved_wire,  # pyright: ignore[reportPrivateUsage]
)

REQUEST_SCHEMA = "aware.goal.native-creation-request.v1"
_FIELDS = {
    "schema_id", "idempotency_key", "goal_tag", "title", "intent", "owner_ref",
    "definition_of_done_ref", "priority", "locks_ref", "lanes", "definitions",
    "dependencies", "unresolved_dependencies", "request_ref",
}
_LANE_FIELDS = {"lane_key", "title", "role", "owner_ref"}
_MEMBER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class NativeGoalCreationRequestError(ValueError):
    """Invalid authored inputs, not a provider qualification verdict."""


def _text(value: object) -> str:
    if type(value) is not str or not value or value != value.strip() or "\x00" in value:
        raise NativeGoalCreationRequestError("creation_request_text")
    try:
        _ = value.encode("utf-8")
    except UnicodeError as exc:
        raise NativeGoalCreationRequestError("creation_request_encoding") from exc
    return value


def _token(value: object) -> str:
    text = _text(value)
    if required_token(text, "creation_request") != text or re.search(r"[\x00-\x1f\x7f]", text):
        raise NativeGoalCreationRequestError("creation_request_token")
    return text


def _array(value: object) -> list[object]:
    if type(value) is not list:
        raise NativeGoalCreationRequestError("creation_request_array")
    return cast(list[object], value)


def _object(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(cast(dict[str, object], value)) != fields:
        raise NativeGoalCreationRequestError("creation_request_fields")
    return cast(dict[str, object], value)


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _same_wire(raw: object, canonical: object) -> None:
    if _json(raw) != _json(canonical):
        raise NativeGoalCreationRequestError("creation_request_nested_noncanonical")


def _check_json_strings(raw: object) -> None:
    if type(raw) is str:
        text = raw
        if "\x00" in text:
            raise NativeGoalCreationRequestError("creation_request_encoding")
        _ = text.encode("utf-8")
    elif type(raw) is dict:
        for key, value in cast(dict[str, object], raw).items():
            if type(key) is not str:
                raise NativeGoalCreationRequestError("creation_request_fields")
            _check_json_strings(key)
            _check_json_strings(value)
    elif type(raw) is list:
        for value in cast(list[object], raw):
            _check_json_strings(value)


def _validate(raw: object) -> dict[str, object]:
    body = _object(raw, _FIELDS)
    _check_json_strings(body)
    if body["schema_id"] != REQUEST_SCHEMA:
        raise NativeGoalCreationRequestError("creation_request_schema")
    for field in ("idempotency_key", "goal_tag", "owner_ref", "priority", "request_ref"):
        _ = _token(body[field])
    goal = normalize_goal_tag(body["goal_tag"])
    for field in ("title", "intent"):
        _ = _text(body[field])
    for field in ("definition_of_done_ref", "locks_ref"):
        if body[field] is not None:
            _ = _token(body[field])

    lane_keys: list[str] = []
    for raw_lane in _array(body["lanes"]):
        lane = _object(raw_lane, _LANE_FIELDS)
        key = _token(lane["lane_key"])
        if _MEMBER.fullmatch(key) is None:
            raise NativeGoalCreationRequestError("creation_request_lane_key")
        for field in ("title", "role"):
            _ = _text(lane[field])
        _ = _token(lane["owner_ref"])
        if lane["owner_ref"] != body["owner_ref"]:
            raise NativeGoalCreationRequestError("creation_request_lane_owner")
        lane_keys.append(key)
    if not lane_keys or lane_keys != sorted(set(lane_keys)):
        raise NativeGoalCreationRequestError("creation_request_lane_order")

    raw_definitions = _array(body["definitions"])
    if not raw_definitions:
        raise NativeGoalCreationRequestError("creation_request_definitions_empty")
    definitions = tuple(_decode_definition(item) for item in raw_definitions)
    ordering: list[tuple[str, int, str]] = []
    lane_ordinals: set[tuple[str, int]] = set()
    by_coordinate: dict[GoalPhaseCoordinate, GoalLanePhaseDefinitionV1] = {}
    for raw_definition, definition in zip(raw_definitions, definitions, strict=True):
        _same_wire(raw_definition, _definition_wire(definition))
        if definition.coordinate.goal_tag != goal:
            raise NativeGoalCreationRequestError("creation_request_definition_goal")
        if definition.title is None or definition.intent is None:
            raise NativeGoalCreationRequestError("creation_request_definition_incomplete")
        if definition.ordinal <= 0:
            raise NativeGoalCreationRequestError("creation_request_definition_ordinal")
        ordinal_key = (definition.coordinate.lane_key, definition.ordinal)
        if definition.coordinate in by_coordinate or ordinal_key in lane_ordinals:
            raise NativeGoalCreationRequestError("creation_request_definition_duplicate")
        by_coordinate[definition.coordinate] = definition
        lane_ordinals.add(ordinal_key)
        ordering.append((*ordinal_key, definition.coordinate.phase_key))
    if ordering != sorted(ordering) or sorted({item.coordinate.lane_key for item in definitions}) != lane_keys:
        raise NativeGoalCreationRequestError("creation_request_definition_partition")

    raw_dependencies = _array(body["dependencies"])
    bundle_wire = {"schema_id": GOAL_PHASE_BUNDLE_SCHEMA, "phases": [], "dependencies": raw_dependencies}
    bundle = decode_goal_phase_bundle(_json(bundle_wire).encode("utf-8"))
    _same_wire(bundle_wire, goal_phase_bundle_to_wire(bundle))
    keys: list[str] = []
    for dependency in bundle.dependencies:
        if dependency.owner_goal_tag != goal or dependency.dependent not in by_coordinate:
            raise NativeGoalCreationRequestError("creation_request_dependency_dependent")
        prerequisite = by_coordinate.get(dependency.prerequisite)
        if dependency.prerequisite.goal_tag == goal and prerequisite is None:
            raise NativeGoalCreationRequestError("creation_request_dependency_prerequisite")
        if prerequisite is not None and prerequisite.gate.gate_digest != dependency.required_gate_digest:
            raise NativeGoalCreationRequestError("creation_request_dependency_gate")
        keys.append(dependency.dependency_key)
    if keys != sorted(set(keys)):
        raise NativeGoalCreationRequestError("creation_request_dependency_order")

    unresolved_keys: list[str] = []
    for item in _array(body["unresolved_dependencies"]):
        dependency = _decode_unresolved(item)
        _same_wire(item, _unresolved_wire(dependency))
        if dependency.owner_goal_tag != goal or dependency.dependent not in by_coordinate:
            raise NativeGoalCreationRequestError("creation_request_unresolved_dependent")
        if dependency.prerequisite in by_coordinate or dependency.dependency_key in keys:
            raise NativeGoalCreationRequestError("creation_request_unresolved_conflict")
        unresolved_keys.append(dependency.dependency_key)
    if unresolved_keys != sorted(set(unresolved_keys)):
        raise NativeGoalCreationRequestError("creation_request_unresolved_order")

    expected = "goal-native-creation-request:" + fingerprint({key: value for key, value in body.items() if key != "request_ref"})
    if body["request_ref"] != expected:
        raise NativeGoalCreationRequestError("creation_request_digest")
    return body


def _checked(raw: object) -> dict[str, object]:
    try:
        return _validate(raw)
    except (ValueError, TypeError) as exc:
        raise NativeGoalCreationRequestError(str(exc)) from exc


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    body: dict[str, object] = {}
    for key, value in pairs:
        if key in body:
            raise NativeGoalCreationRequestError("creation_request_duplicate_field")
        body[key] = value
    return body


def _parse(payload: str) -> object:
    if type(payload) is not str:
        raise NativeGoalCreationRequestError("creation_request_payload")
    try:
        return cast(object, json.loads(payload, object_pairs_hook=_pairs))
    except (ValueError, RecursionError) as exc:
        raise NativeGoalCreationRequestError("creation_request_json") from exc


@dataclass(frozen=True, slots=True)
class NativeGoalCreationRequestV1:
    """Authored canonical input storage, not an admitted creation plan."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not NativeGoalCreationRequestV1:
            raise NativeGoalCreationRequestError("creation_request_type")
        return _checked(_parse(self.canonical_body))

    @property
    def request_ref(self) -> str:
        return _token(self.to_wire()["request_ref"])


def make_native_goal_creation_request(fields: dict[str, object]) -> NativeGoalCreationRequestV1:
    """Author exact inputs and their digest, with no provider or mutation."""
    fields = _object(fields, _FIELDS - {"schema_id", "request_ref"})
    body = {"schema_id": REQUEST_SCHEMA, **fields}
    body["request_ref"] = "goal-native-creation-request:" + fingerprint(body)
    return NativeGoalCreationRequestV1(_json(_checked(body)))


def decode_native_goal_creation_request(payload: str) -> NativeGoalCreationRequestV1:
    return NativeGoalCreationRequestV1(_json(_checked(_parse(payload))))


def encode_native_goal_creation_request(request: NativeGoalCreationRequestV1) -> str:
    if type(request) is not NativeGoalCreationRequestV1:
        raise NativeGoalCreationRequestError("creation_request_type")
    return _json(request.to_wire())
