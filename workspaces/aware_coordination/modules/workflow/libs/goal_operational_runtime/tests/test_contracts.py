from __future__ import annotations

import pytest

from aware_goal_operational_runtime import (
    GoalIntegratedUpdate,
    GoalLaneIssueSnapshot,
    GoalLaneSnapshot,
    GoalSnapshot,
)


def test_goal_tags_are_canonical() -> None:
    with pytest.raises(ValueError, match="start with 'goal/'"):
        GoalSnapshot(goal_ref="goal:1", tag="not-a-goal", title="No")


def test_lane_head_must_match_final_row() -> None:
    row = GoalLaneIssueSnapshot(
        row_ref="row:1",
        row_key="first",
        sequence=1,
        gate="Contract passes.",
    )
    with pytest.raises(ValueError, match="final lane row"):
        GoalLaneSnapshot(
            lane_ref="lane:1",
            lane_key="runtime",
            rows=(row,),
            head_row_ref=None,
        )


def test_lane_sequence_is_contiguous_and_local() -> None:
    row = GoalLaneIssueSnapshot(
        row_ref="row:2",
        row_key="second",
        sequence=2,
        gate="Cannot skip one.",
    )
    with pytest.raises(ValueError, match="contiguous"):
        GoalLaneSnapshot(
            lane_ref="lane:1",
            lane_key="runtime",
            rows=(row,),
            head_row_ref=row.row_ref,
        )


def test_integrated_update_row_requires_lane() -> None:
    with pytest.raises(ValueError, match="row_ref requires lane_ref"):
        GoalIntegratedUpdate(
            update_key="update:1",
            sequence=1,
            kind="row_moved",
            message="Moved.",
            actor_ref="actor:1",
            actor_evidence_ref="identity:1",
            row_ref="row:1",
        )


def test_issue_ref_requires_issue_authority_receipt() -> None:
    with pytest.raises(ValueError, match="issue_ref requires"):
        GoalLaneIssueSnapshot(
            row_ref="row:1",
            row_key="first",
            sequence=1,
            gate="Link exactly.",
            issue_ref="issue:1",
        )
