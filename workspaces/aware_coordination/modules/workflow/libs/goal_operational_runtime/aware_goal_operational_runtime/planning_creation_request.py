"""Undecomposed authored Goal intent, not creation permission or a Phase graph.

This V2 request is deliberately separate from nonempty native-creation V1.
Reuse its metadata laws without relaxing its graph or provenance contracts.
"""

from __future__ import annotations

from dataclasses import dataclass

from .identity import fingerprint, normalize_goal_tag
from .native_creation_request import (
    NativeGoalCreationRequestError,
    _array,  # pyright: ignore[reportPrivateUsage]
    _check_json_strings,  # pyright: ignore[reportPrivateUsage]
    _json,  # pyright: ignore[reportPrivateUsage]
    _object,  # pyright: ignore[reportPrivateUsage]
    _parse,  # pyright: ignore[reportPrivateUsage]
    _text,  # pyright: ignore[reportPrivateUsage]
    _token,  # pyright: ignore[reportPrivateUsage]
)

REQUEST_SCHEMA = "aware.goal.native-creation-request.v2"
REQUEST_DOMAIN = "goal-planning-creation-request"
METADATA_FIELDS = frozenset(
    {
        "goal_tag",
        "title",
        "intent",
        "owner_ref",
        "definition_of_done_ref",
        "priority",
        "locks_ref",
    }
)
GRAPH_FIELDS = frozenset(
    {"lanes", "definitions", "dependencies", "unresolved_dependencies"}
)
_FIELDS = {
    *METADATA_FIELDS,
    *GRAPH_FIELDS,
    "schema_id",
    "idempotency_key",
    "request_ref",
}


def validate_planning_metadata(body: dict[str, object]) -> None:
    """The original creation metadata law, without requiring a Phase graph."""
    _check_json_strings(body)
    for field in ("goal_tag", "owner_ref", "priority"):
        _ = _token(body[field])
    _ = normalize_goal_tag(body["goal_tag"])
    for field in ("title", "intent"):
        _ = _text(body[field])
    for field in ("definition_of_done_ref", "locks_ref"):
        if body[field] is not None:
            _ = _token(body[field])


def validate_undecomposed_graph(body: dict[str, object]) -> None:
    for field in GRAPH_FIELDS:
        if _array(body[field]):
            raise NativeGoalCreationRequestError(
                "planning_request_requires_empty_graph"
            )


def _validate(raw: object) -> dict[str, object]:
    body = _object(raw, _FIELDS)
    if body["schema_id"] != REQUEST_SCHEMA:
        raise NativeGoalCreationRequestError("planning_request_schema")
    validate_planning_metadata(body)
    _ = _token(body["idempotency_key"])
    validate_undecomposed_graph(body)
    expected = (
        REQUEST_DOMAIN
        + ":"
        + fingerprint(
            {key: value for key, value in body.items() if key != "request_ref"}
        )
    )
    if type(body["request_ref"]) is not str or body["request_ref"] != expected:
        raise NativeGoalCreationRequestError("planning_request_digest")
    return body


@dataclass(frozen=True, slots=True)
class PlanningGoalCreationRequestV2:
    """Strict detached intention; construction and decoding grant no authority."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not PlanningGoalCreationRequestV2:
            raise NativeGoalCreationRequestError("planning_request_type")
        return _validate(_parse(self.canonical_body))

    @property
    def request_ref(self) -> str:
        return _token(self.to_wire()["request_ref"])


def make_planning_goal_creation_request(
    fields: dict[str, object],
) -> PlanningGoalCreationRequestV2:
    fields = _object(fields, _FIELDS - {"schema_id", "request_ref"})
    body = {"schema_id": REQUEST_SCHEMA, **fields}
    body["request_ref"] = REQUEST_DOMAIN + ":" + fingerprint(body)
    return PlanningGoalCreationRequestV2(_json(_validate(body)))


def decode_planning_goal_creation_request(
    payload: str,
) -> PlanningGoalCreationRequestV2:
    return PlanningGoalCreationRequestV2(_json(_validate(_parse(payload))))


def encode_planning_goal_creation_request(
    request: PlanningGoalCreationRequestV2,
) -> str:
    if type(request) is not PlanningGoalCreationRequestV2:
        raise NativeGoalCreationRequestError("planning_request_type")
    return _json(request.to_wire())
