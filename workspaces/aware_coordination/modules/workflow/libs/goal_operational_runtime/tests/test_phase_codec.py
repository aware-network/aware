import json

import pytest
from aware_goal_operational_runtime import (
    GOAL_PHASE_BUNDLE_SCHEMA,
    GoalLanePhase,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalPhaseContractBundleV1,
    GoalPhaseContractError,
    GoalPhaseCoordinate,
    decode_goal_phase_bundle,
    encode_goal_phase_bundle,
)


def bundle() -> GoalPhaseContractBundleV1:
    phase_gate = GoalLanePhaseGate(
        gate_key="contract-accepted",
        promise="Contract round-trips exactly.",
        gate_contract_ref="contract:goal-phase-gate:v1",
        evidence_schema_ref="schema:goal-phase-evidence:v1",
    )
    return GoalPhaseContractBundleV1(
        phases=(
            GoalLanePhase(
                coordinate=GoalPhaseCoordinate(
                    "goal/2026-09-12/shared", "operational-runtime", "m1"
                ),
                title="M1",
                ordinal=1,
                intent="Add the portable contract.",
                state=GoalLanePhaseState.PLANNED,
                gate=phase_gate,
            ),
        ),
        dependencies=(),
    )


def test_bundle_round_trips_as_deterministic_canonical_json() -> None:
    payload = encode_goal_phase_bundle(bundle())
    assert decode_goal_phase_bundle(payload) == bundle()
    assert encode_goal_phase_bundle(decode_goal_phase_bundle(payload)) == payload
    assert json.loads(payload)["schema_id"] == GOAL_PHASE_BUNDLE_SCHEMA
    assert b'": ' not in payload
    assert b'", "' not in payload


def test_codec_rejects_duplicate_unknown_and_noncanonical_gate_digest() -> None:
    with pytest.raises(GoalPhaseContractError, match="duplicate JSON key"):
        decode_goal_phase_bundle(b'{"schema_id":"a","schema_id":"b"}')
    wire = json.loads(encode_goal_phase_bundle(bundle()))
    wire["unexpected"] = True
    with pytest.raises(GoalPhaseContractError, match="keys differ"):
        decode_goal_phase_bundle(json.dumps(wire).encode())
    wire.pop("unexpected")
    wire["phases"][0]["gate"]["gate_digest"] = "sha256:" + "0" * 64
    with pytest.raises(GoalPhaseContractError, match="freshly derived"):
        decode_goal_phase_bundle(json.dumps(wire).encode())


def test_codec_rejects_wrong_schema_and_invalid_enum() -> None:
    wire = json.loads(encode_goal_phase_bundle(bundle()))
    wire["schema_id"] = "aware.goal.lane-phase.bundle.v2"
    with pytest.raises(GoalPhaseContractError, match="unsupported"):
        decode_goal_phase_bundle(json.dumps(wire).encode())
    wire = json.loads(encode_goal_phase_bundle(bundle()))
    wire["phases"][0]["state"] = "complete"
    with pytest.raises(ValueError, match="complete"):
        decode_goal_phase_bundle(json.dumps(wire).encode())
