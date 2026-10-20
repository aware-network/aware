from __future__ import annotations

import json

import pytest
from conftest import context

from aware_goal_operational_runtime import (
    AppendGoalLaneIssueIntent,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalLaneStatus,
    apply_goal_intent,
    decode_goal_operational_state,
    encode_goal_operational_state,
)


def test_codec_round_trips_nested_goal_state(actor, state) -> None:
    ensured = apply_goal_intent(
        state,
        EnsureGoalIntent(
            context(actor, "goal"),
            tag="goal/2026-08-27/codec-v0",
            title="Codec",
        ),
    )
    assert ensured.goal_ref is not None
    lane = apply_goal_intent(
        ensured.state,
        EnsureGoalLaneIntent(
            context(actor, "lane"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=0,
            lane_key="runtime",
            status=GoalLaneStatus.ACTIVE,
        ),
    )
    assert lane.lane_ref is not None
    row = apply_goal_intent(
        lane.state,
        AppendGoalLaneIssueIntent(
            context(actor, "row"),
            goal_ref=ensured.goal_ref,
            lane_ref=lane.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="values",
            gate="Codec passes.",
        ),
    )
    encoded = encode_goal_operational_state(row.state)
    assert decode_goal_operational_state(encoded) == row.state
    assert (
        encode_goal_operational_state(decode_goal_operational_state(encoded)) == encoded
    )


def test_codec_rejects_unknown_fields_and_versions(state) -> None:
    encoded = encode_goal_operational_state(state)
    payload = json.loads(encoded)
    payload["unexpected"] = True
    with pytest.raises(ValueError, match="keys differ"):
        decode_goal_operational_state(json.dumps(payload))

    payload = json.loads(encoded)
    payload["version"] = 99
    with pytest.raises(ValueError, match="unsupported"):
        decode_goal_operational_state(json.dumps(payload))


def test_codec_rejects_unknown_status(actor, state) -> None:
    ensured = apply_goal_intent(
        state,
        EnsureGoalIntent(
            context(actor, "goal"),
            tag="goal/2026-08-27/status-v0",
            title="Status",
        ),
    )
    payload = json.loads(encode_goal_operational_state(ensured.state))
    payload["state"]["goals"][0]["status"] = "invented"
    with pytest.raises(ValueError, match="invented"):
        decode_goal_operational_state(json.dumps(payload))
