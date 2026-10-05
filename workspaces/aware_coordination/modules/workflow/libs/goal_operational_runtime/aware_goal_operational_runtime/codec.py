from __future__ import annotations

import json
from collections.abc import Mapping

from .contracts import (
    GoalAuthorityEvidence,
    GoalAuthorityKind,
    GoalIntegratedUpdate,
    GoalLaneIssueSnapshot,
    GoalLaneIssueTick,
    GoalLaneSnapshot,
    GoalLaneStatus,
    GoalOperationalState,
    GoalSnapshot,
    GoalStatus,
    IntentRecord,
    TransitionOutcome,
)

CODEC_NAME = "aware.workflow.goal-operational-state"
CODEC_VERSION = 1


def encode_goal_operational_state(state: GoalOperationalState) -> str:
    payload = {
        "codec": CODEC_NAME,
        "version": CODEC_VERSION,
        "state": state.to_wire(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def decode_goal_operational_state(payload: str) -> GoalOperationalState:
    if not isinstance(payload, str) or not payload:
        raise ValueError("payload must be non-empty JSON text")
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid Goal operational JSON") from exc
    root = _object(raw, "record")
    _keys(root, {"codec", "version", "state"}, "record")
    if root["codec"] != CODEC_NAME or root["version"] != CODEC_VERSION:
        raise ValueError("unsupported Goal operational codec")
    return _state(_object(root["state"], "state"))


def _state(raw: Mapping[str, object]) -> GoalOperationalState:
    _keys(raw, {"authority", "goals", "intent_records"}, "state")
    return GoalOperationalState(
        authority=_authority(_object(raw["authority"], "authority")),
        goals=tuple(
            _goal(_object(item, "goal")) for item in _list(raw["goals"], "goals")
        ),
        intent_records=tuple(
            _intent_record(_object(item, "intent_record"))
            for item in _list(raw["intent_records"], "intent_records")
        ),
    )


def _authority(raw: Mapping[str, object]) -> GoalAuthorityEvidence:
    _keys(
        raw,
        {"kind", "provider_key", "authority_ref", "generation", "receipt_ref"},
        "authority",
    )
    return GoalAuthorityEvidence(
        kind=GoalAuthorityKind(_string(raw["kind"], "kind")),
        provider_key=_string(raw["provider_key"], "provider_key"),
        authority_ref=_string(raw["authority_ref"], "authority_ref"),
        generation=_integer(raw["generation"], "generation"),
        receipt_ref=_nullable_string(raw["receipt_ref"], "receipt_ref"),
    )


def _goal(raw: Mapping[str, object]) -> GoalSnapshot:
    _keys(
        raw,
        {
            "goal_ref",
            "tag",
            "title",
            "status",
            "priority_level",
            "definition_of_done_ref",
            "locks_ref",
            "evidence_ref",
            "lanes",
            "updates",
            "revision",
        },
        "goal",
    )
    return GoalSnapshot(
        goal_ref=_string(raw["goal_ref"], "goal_ref"),
        tag=_string(raw["tag"], "tag"),
        title=_string(raw["title"], "title"),
        status=GoalStatus(_string(raw["status"], "status")),
        priority_level=_string(raw["priority_level"], "priority_level"),
        definition_of_done_ref=_nullable_string(
            raw["definition_of_done_ref"], "definition_of_done_ref"
        ),
        locks_ref=_nullable_string(raw["locks_ref"], "locks_ref"),
        evidence_ref=_nullable_string(raw["evidence_ref"], "evidence_ref"),
        lanes=tuple(
            _lane(_object(item, "lane")) for item in _list(raw["lanes"], "lanes")
        ),
        updates=tuple(
            _update(_object(item, "update"))
            for item in _list(raw["updates"], "updates")
        ),
        revision=_integer(raw["revision"], "revision"),
    )


def _lane(raw: Mapping[str, object]) -> GoalLaneSnapshot:
    _keys(
        raw,
        {
            "lane_ref",
            "lane_key",
            "status",
            "role_key",
            "role_label",
            "owner_execution_id",
            "scope",
            "head_row_ref",
            "rows",
            "revision",
        },
        "lane",
    )
    return GoalLaneSnapshot(
        lane_ref=_string(raw["lane_ref"], "lane_ref"),
        lane_key=_string(raw["lane_key"], "lane_key"),
        status=GoalLaneStatus(_string(raw["status"], "status")),
        role_key=_nullable_string(raw["role_key"], "role_key"),
        role_label=_nullable_string(raw["role_label"], "role_label"),
        owner_execution_id=_nullable_string(
            raw["owner_execution_id"], "owner_execution_id"
        ),
        scope=_nullable_string(raw["scope"], "scope"),
        head_row_ref=_nullable_string(raw["head_row_ref"], "head_row_ref"),
        rows=tuple(_row(_object(item, "row")) for item in _list(raw["rows"], "rows")),
        revision=_integer(raw["revision"], "revision"),
    )


def _row(raw: Mapping[str, object]) -> GoalLaneIssueSnapshot:
    _keys(
        raw,
        {
            "row_ref",
            "row_key",
            "sequence",
            "gate",
            "tick",
            "status_snapshot",
            "previous_row_ref",
            "prerequisite_refs",
            "planned_issue_tag",
            "issue_ref",
            "issue_authority_receipt_ref",
            "issue_observation_ref",
            "owner_execution_id",
            "receipt_ref",
            "revision",
        },
        "row",
    )
    return GoalLaneIssueSnapshot(
        row_ref=_string(raw["row_ref"], "row_ref"),
        row_key=_string(raw["row_key"], "row_key"),
        sequence=_integer(raw["sequence"], "sequence"),
        gate=_string(raw["gate"], "gate"),
        tick=GoalLaneIssueTick(_string(raw["tick"], "tick")),
        status_snapshot=_string(raw["status_snapshot"], "status_snapshot"),
        previous_row_ref=_nullable_string(raw["previous_row_ref"], "previous_row_ref"),
        prerequisite_refs=tuple(
            _string(item, "prerequisite_ref")
            for item in _list(raw["prerequisite_refs"], "prerequisite_refs")
        ),
        planned_issue_tag=_nullable_string(
            raw["planned_issue_tag"], "planned_issue_tag"
        ),
        issue_ref=_nullable_string(raw["issue_ref"], "issue_ref"),
        issue_authority_receipt_ref=_nullable_string(
            raw["issue_authority_receipt_ref"], "issue_authority_receipt_ref"
        ),
        issue_observation_ref=_nullable_string(
            raw["issue_observation_ref"], "issue_observation_ref"
        ),
        owner_execution_id=_nullable_string(
            raw["owner_execution_id"], "owner_execution_id"
        ),
        receipt_ref=_nullable_string(raw["receipt_ref"], "receipt_ref"),
        revision=_integer(raw["revision"], "revision"),
    )


def _update(raw: Mapping[str, object]) -> GoalIntegratedUpdate:
    _keys(
        raw,
        {
            "update_key",
            "sequence",
            "kind",
            "message",
            "actor_ref",
            "actor_evidence_ref",
            "recorded_at",
            "lane_ref",
            "row_ref",
            "receipt_ref",
        },
        "update",
    )
    return GoalIntegratedUpdate(
        update_key=_string(raw["update_key"], "update_key"),
        sequence=_integer(raw["sequence"], "sequence"),
        kind=_string(raw["kind"], "kind"),
        message=_string(raw["message"], "message"),
        actor_ref=_string(raw["actor_ref"], "actor_ref"),
        actor_evidence_ref=_string(raw["actor_evidence_ref"], "actor_evidence_ref"),
        recorded_at=_nullable_string(raw["recorded_at"], "recorded_at"),
        lane_ref=_nullable_string(raw["lane_ref"], "lane_ref"),
        row_ref=_nullable_string(raw["row_ref"], "row_ref"),
        receipt_ref=_nullable_string(raw["receipt_ref"], "receipt_ref"),
    )


def _intent_record(raw: Mapping[str, object]) -> IntentRecord:
    _keys(
        raw,
        {
            "client_intent_id",
            "fingerprint",
            "outcome",
            "goal_ref",
            "lane_ref",
            "row_ref",
        },
        "intent_record",
    )
    return IntentRecord(
        client_intent_id=_string(raw["client_intent_id"], "client_intent_id"),
        fingerprint=_string(raw["fingerprint"], "fingerprint"),
        outcome=TransitionOutcome(_string(raw["outcome"], "outcome")),
        goal_ref=_nullable_string(raw["goal_ref"], "goal_ref"),
        lane_ref=_nullable_string(raw["lane_ref"], "lane_ref"),
        row_ref=_nullable_string(raw["row_ref"], "row_ref"),
    )


def _keys(raw: Mapping[str, object], expected: set[str], field: str) -> None:
    observed = set(raw)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ValueError(f"{field} keys differ; missing={missing}, extra={extra}")


def _object(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field} must be a JSON object")
    return value


def _list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a JSON array")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    return value


def _nullable_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    return value
