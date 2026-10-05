"""Strict canonical codec for the portable Goal Phase/Gate v1 bundle."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

from .dependencies import GoalDependencyRelation
from .phase_contracts import (
    GoalLanePhase,
    GoalLanePhaseGate,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseContractError,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
)


def encode_goal_phase_bundle(value: GoalPhaseContractBundleV1) -> bytes:
    """Return deterministic UTF-8 JSON for one exact v1 bundle."""

    if type(value) is not GoalPhaseContractBundleV1:
        raise TypeError("value must be GoalPhaseContractBundleV1")
    value.__post_init__()
    return json.dumps(
        goal_phase_bundle_to_wire(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def decode_goal_phase_bundle(payload: bytes) -> GoalPhaseContractBundleV1:
    """Decode strict v1 JSON; duplicate and unknown fields fail closed."""

    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    try:
        raw = cast(
            object,
            json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseContractError(
            "Goal Phase bundle is not canonical JSON"
        ) from error
    root = _mapping(raw, "bundle")
    _keys(root, {"schema_id", "phases", "dependencies"}, "bundle")
    return GoalPhaseContractBundleV1(
        schema_id=_string(root["schema_id"], "schema_id"),
        phases=tuple(_phase(item) for item in _list(root["phases"], "phases")),
        dependencies=tuple(
            _dependency(item) for item in _list(root["dependencies"], "dependencies")
        ),
    )


def goal_phase_bundle_to_wire(
    value: GoalPhaseContractBundleV1,
) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "phases": [_phase_wire(phase) for phase in value.phases],
        "dependencies": [
            _dependency_wire(dependency) for dependency in value.dependencies
        ],
    }


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, object]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


def _gate_wire(value: GoalLanePhaseGate) -> dict[str, object]:
    return {**value.semantic_body(), "gate_digest": value.gate_digest}


def _observation_wire(
    value: GoalLanePhaseGateObservation,
) -> dict[str, object]:
    return {
        "observation_ref": value.observation_ref,
        "gate_digest": value.gate_digest,
        "outcome": value.outcome.value,
        "evaluator_ref": value.evaluator_ref,
        "evidence_refs": list(value.evidence_refs),
        "source_revision_refs": list(value.source_revision_refs),
        "evaluated_at": value.evaluated_at,
        "currentness_ref": value.currentness_ref,
    }


def _work_wire(value: GoalLanePhaseWork) -> dict[str, object]:
    return {
        "association_ref": value.association_ref,
        "issue_ref": value.issue_ref,
        "role": value.role.value,
        "disposition": value.disposition.value,
        "admitted_at": value.admitted_at,
        "retired_at": value.retired_at,
        "receipt_ref": value.receipt_ref,
    }


def _phase_wire(value: GoalLanePhase) -> dict[str, object]:
    return {
        "coordinate": _coordinate_wire(value.coordinate),
        "title": value.title,
        "ordinal": value.ordinal,
        "intent": value.intent,
        "state": value.state.value,
        "gate": _gate_wire(value.gate),
        "gate_observations": [
            _observation_wire(observation) for observation in value.gate_observations
        ],
        "work_associations": [
            _work_wire(association) for association in value.work_associations
        ],
        "pursuit_directive": value.pursuit_directive,
        "last_receipt_ref": value.last_receipt_ref,
    }


def _dependency_wire(value: GoalPhaseDependency) -> dict[str, object]:
    return {
        "owner_goal_tag": value.owner_goal_tag,
        "dependency_key": value.dependency_key,
        "dependent": _coordinate_wire(value.dependent),
        "prerequisite": _coordinate_wire(value.prerequisite),
        "required_gate_digest": value.required_gate_digest,
        "relation": value.relation.value,
        "reason": value.reason,
        "evidence_refs": list(value.evidence_refs),
    }


def _coordinate(raw: object) -> GoalPhaseCoordinate:
    values = _mapping(raw, "coordinate")
    _keys(values, {"goal_tag", "lane_key", "phase_key"}, "coordinate")
    return GoalPhaseCoordinate(
        goal_tag=_string(values["goal_tag"], "goal_tag"),
        lane_key=_string(values["lane_key"], "lane_key"),
        phase_key=_string(values["phase_key"], "phase_key"),
    )


def _gate(raw: object) -> GoalLanePhaseGate:
    values = _mapping(raw, "gate")
    _keys(
        values,
        {
            "gate_key",
            "promise",
            "gate_contract_ref",
            "evidence_schema_ref",
            "invariant_refs",
            "semantic_revision",
            "gate_digest",
        },
        "gate",
    )
    gate = GoalLanePhaseGate(
        gate_key=_string(values["gate_key"], "gate_key"),
        promise=_string(values["promise"], "promise"),
        gate_contract_ref=_string(values["gate_contract_ref"], "gate_contract_ref"),
        evidence_schema_ref=_string(
            values["evidence_schema_ref"], "evidence_schema_ref"
        ),
        invariant_refs=_strings(values["invariant_refs"], "invariant_refs"),
        semantic_revision=_integer(values["semantic_revision"], "semantic_revision"),
    )
    if _string(values["gate_digest"], "gate_digest") != gate.gate_digest:
        raise GoalPhaseContractError("gate digest is not freshly derived")
    return gate


def _observation(raw: object) -> GoalLanePhaseGateObservation:
    values = _mapping(raw, "gate_observation")
    _keys(
        values,
        {
            "observation_ref",
            "gate_digest",
            "outcome",
            "evaluator_ref",
            "evidence_refs",
            "source_revision_refs",
            "evaluated_at",
            "currentness_ref",
        },
        "gate_observation",
    )
    return GoalLanePhaseGateObservation(
        observation_ref=_string(values["observation_ref"], "observation_ref"),
        gate_digest=_string(values["gate_digest"], "gate_digest"),
        outcome=GoalLanePhaseGateOutcome(_string(values["outcome"], "outcome")),
        evaluator_ref=_string(values["evaluator_ref"], "evaluator_ref"),
        evidence_refs=_strings(values["evidence_refs"], "evidence_refs"),
        source_revision_refs=_strings(
            values["source_revision_refs"], "source_revision_refs"
        ),
        evaluated_at=_string(values["evaluated_at"], "evaluated_at"),
        currentness_ref=_string(values["currentness_ref"], "currentness_ref"),
    )


def _work(raw: object) -> GoalLanePhaseWork:
    values = _mapping(raw, "work_association")
    _keys(
        values,
        {
            "association_ref",
            "issue_ref",
            "role",
            "disposition",
            "admitted_at",
            "retired_at",
            "receipt_ref",
        },
        "work_association",
    )
    return GoalLanePhaseWork(
        association_ref=_string(values["association_ref"], "association_ref"),
        issue_ref=_string(values["issue_ref"], "issue_ref"),
        role=GoalLanePhaseWorkRole(_string(values["role"], "role")),
        disposition=GoalLanePhaseWorkDisposition(
            _string(values["disposition"], "disposition")
        ),
        admitted_at=_string(values["admitted_at"], "admitted_at"),
        retired_at=_optional_string(values["retired_at"], "retired_at"),
        receipt_ref=_string(values["receipt_ref"], "receipt_ref"),
    )


def _phase(raw: object) -> GoalLanePhase:
    values = _mapping(raw, "phase")
    _keys(
        values,
        {
            "coordinate",
            "title",
            "ordinal",
            "intent",
            "state",
            "gate",
            "gate_observations",
            "work_associations",
            "pursuit_directive",
            "last_receipt_ref",
        },
        "phase",
    )
    return GoalLanePhase(
        coordinate=_coordinate(values["coordinate"]),
        title=_string(values["title"], "title"),
        ordinal=_integer(values["ordinal"], "ordinal"),
        intent=_string(values["intent"], "intent"),
        state=GoalLanePhaseState(_string(values["state"], "state")),
        gate=_gate(values["gate"]),
        gate_observations=tuple(
            _observation(item)
            for item in _list(values["gate_observations"], "gate_observations")
        ),
        work_associations=tuple(
            _work(item)
            for item in _list(values["work_associations"], "work_associations")
        ),
        pursuit_directive=_optional_string(
            values["pursuit_directive"], "pursuit_directive"
        ),
        last_receipt_ref=_optional_string(
            values["last_receipt_ref"], "last_receipt_ref"
        ),
    )


def _dependency(raw: object) -> GoalPhaseDependency:
    values = _mapping(raw, "dependency")
    _keys(
        values,
        {
            "owner_goal_tag",
            "dependency_key",
            "dependent",
            "prerequisite",
            "required_gate_digest",
            "relation",
            "reason",
            "evidence_refs",
        },
        "dependency",
    )
    return GoalPhaseDependency(
        owner_goal_tag=_string(values["owner_goal_tag"], "owner_goal_tag"),
        dependency_key=_string(values["dependency_key"], "dependency_key"),
        dependent=_coordinate(values["dependent"]),
        prerequisite=_coordinate(values["prerequisite"]),
        required_gate_digest=_string(
            values["required_gate_digest"], "required_gate_digest"
        ),
        relation=GoalDependencyRelation(_string(values["relation"], "relation")),
        reason=_string(values["reason"], "reason"),
        evidence_refs=_strings(values["evidence_refs"], "evidence_refs"),
    )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GoalPhaseContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise GoalPhaseContractError(f"{field_name} must be an object")
    mapping = cast(dict[object, object], value)
    if any(type(key) is not str for key in mapping):
        raise GoalPhaseContractError(f"{field_name} keys must be text")
    return cast(dict[str, object], mapping)


def _keys(value: Mapping[str, object], expected: set[str], field_name: str) -> None:
    if set(value) != expected:
        raise GoalPhaseContractError(f"{field_name} keys differ from contract")


def _list(value: object, field_name: str) -> list[object]:
    if type(value) is not list:
        raise GoalPhaseContractError(f"{field_name} must be an array")
    return cast(list[object], value)


def _strings(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(_string(item, field_name) for item in _list(value, field_name))


def _string(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise GoalPhaseContractError(f"{field_name} must be text")
    return value


def _optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _string(value, field_name)


def _integer(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise GoalPhaseContractError(f"{field_name} must be an integer")
    return value
