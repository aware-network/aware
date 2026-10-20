from __future__ import annotations

from conftest import context

from aware_goal_operational_runtime import (
    AchieveGoalIntent,
    ActivateGoalIntent,
    AppendGoalLaneIssueIntent,
    AppendGoalUpdateIntent,
    BlockGoalIntent,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalLaneIssueTick,
    GoalLaneStatus,
    GoalStatus,
    LinkGoalLaneIssueIntent,
    ParkGoalIntent,
    ResumeGoalIntent,
    SupersedeGoalIntent,
    SyncGoalLaneIssueIntent,
    TransitionOutcome,
    apply_goal_intent,
)


def _ensure_goal(state, actor, *, key: str = "goal"):
    return apply_goal_intent(
        state,
        EnsureGoalIntent(
            context(actor, f"ensure-{key}"),
            tag=f"goal/2026-08-27/{key}-v0",
            title=key.title(),
            definition_of_done_ref="content:dod",
            locks_ref="content:locks",
        ),
    )


def _ensure_lane(state, actor, goal_ref, goal_revision, lane_key, intent_key):
    return apply_goal_intent(
        state,
        EnsureGoalLaneIntent(
            context(actor, intent_key),
            goal_ref=goal_ref,
            expected_goal_revision=goal_revision,
            lane_key=lane_key,
            status=GoalLaneStatus.ACTIVE,
        ),
    )


def test_goal_lifecycle_requires_explicit_achievement_evidence(actor, state) -> None:
    ensured = _ensure_goal(state, actor)
    assert ensured.goal_ref is not None
    active = apply_goal_intent(
        ensured.state,
        ActivateGoalIntent(
            context(actor, "activate"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=0,
        ),
    )
    no_evidence = apply_goal_intent(
        active.state,
        AchieveGoalIntent(
            context(actor, "achieve-no-evidence"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=1,
        ),
    )
    assert no_evidence.outcome is TransitionOutcome.INVALID
    assert no_evidence.blocker_code == "achievement_evidence_required"
    goal = no_evidence.state.goal_by_ref(ensured.goal_ref)
    assert goal is not None and goal.status is GoalStatus.ACTIVE

    achieved = apply_goal_intent(
        active.state,
        AchieveGoalIntent(
            context(actor, "achieve"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=1,
            evidence_ref="goal-evaluation:accepted",
        ),
    )
    goal = achieved.state.goal_by_ref(ensured.goal_ref)
    assert achieved.outcome is TransitionOutcome.APPLIED
    assert goal is not None and goal.status is GoalStatus.ACHIEVED


def test_goal_lifecycle_block_resume_park_and_supersede_are_guarded(
    actor, state
) -> None:
    ensured = _ensure_goal(state, actor)
    assert ensured.goal_ref is not None
    missing_reason = apply_goal_intent(
        ensured.state,
        BlockGoalIntent(
            context(actor, "block-without-reason"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=0,
        ),
    )
    assert missing_reason.blocker_code == "block_reason_required"
    blocked = apply_goal_intent(
        ensured.state,
        BlockGoalIntent(
            context(actor, "block"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=0,
            reason="External gate pending.",
        ),
    )
    resumed = apply_goal_intent(
        blocked.state,
        ResumeGoalIntent(
            context(actor, "resume"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=1,
        ),
    )
    parked = apply_goal_intent(
        resumed.state,
        ParkGoalIntent(
            context(actor, "park"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=2,
        ),
    )
    no_evidence = apply_goal_intent(
        parked.state,
        SupersedeGoalIntent(
            context(actor, "supersede-no-evidence"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=3,
        ),
    )
    assert no_evidence.blocker_code == "supersession_evidence_required"
    superseded = apply_goal_intent(
        parked.state,
        SupersedeGoalIntent(
            context(actor, "supersede"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=3,
            evidence_ref="goal-replacement:next",
        ),
    )
    goal = superseded.state.goal_by_ref(ensured.goal_ref)
    assert goal is not None and goal.status is GoalStatus.SUPERSEDED


def test_same_lane_append_is_expected_head_bound(actor, state) -> None:
    ensured = _ensure_goal(state, actor)
    assert ensured.goal_ref is not None
    lane_result = _ensure_lane(
        ensured.state,
        actor,
        ensured.goal_ref,
        0,
        "runtime",
        "lane-runtime",
    )
    assert lane_result.lane_ref is not None
    first = apply_goal_intent(
        lane_result.state,
        AppendGoalLaneIssueIntent(
            context(actor, "row-first"),
            goal_ref=ensured.goal_ref,
            lane_ref=lane_result.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="first",
            gate="First passes.",
        ),
    )
    conflict = apply_goal_intent(
        first.state,
        AppendGoalLaneIssueIntent(
            context(actor, "row-conflict"),
            goal_ref=ensured.goal_ref,
            lane_ref=lane_result.lane_ref,
            expected_lane_revision=1,
            expected_head_row_ref=None,
            row_key="second",
            gate="Must not append.",
        ),
    )
    assert conflict.outcome is TransitionOutcome.CONFLICT
    assert conflict.blocker_code == "lane_head_mismatch"
    assert conflict.actual_head_row_ref == first.row_ref
    lane = conflict.state.goal_by_ref(ensured.goal_ref).lane_by_ref(
        lane_result.lane_ref
    )  # type: ignore[union-attr]
    assert lane is not None and len(lane.rows) == 1


def test_different_lanes_advance_without_goal_global_sequence_conflict(
    actor, state
) -> None:
    ensured = _ensure_goal(state, actor)
    assert ensured.goal_ref is not None
    first_lane = _ensure_lane(
        ensured.state,
        actor,
        ensured.goal_ref,
        0,
        "runtime",
        "lane-runtime",
    )
    second_lane = _ensure_lane(
        first_lane.state,
        actor,
        ensured.goal_ref,
        1,
        "resident",
        "lane-resident",
    )
    assert first_lane.lane_ref is not None and second_lane.lane_ref is not None
    runtime_row = apply_goal_intent(
        second_lane.state,
        AppendGoalLaneIssueIntent(
            context(actor, "runtime-row"),
            goal_ref=ensured.goal_ref,
            lane_ref=first_lane.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="values",
            gate="Values pass.",
        ),
    )
    resident_row = apply_goal_intent(
        runtime_row.state,
        AppendGoalLaneIssueIntent(
            context(actor, "resident-row"),
            goal_ref=ensured.goal_ref,
            lane_ref=second_lane.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="projection",
            gate="Projection passes.",
            prerequisite_refs=(f"{first_lane.lane_ref}/{runtime_row.row_ref}",),
        ),
    )
    assert runtime_row.outcome is TransitionOutcome.APPLIED
    assert resident_row.outcome is TransitionOutcome.APPLIED
    goal = resident_row.state.goal_by_ref(ensured.goal_ref)
    assert goal is not None
    assert goal.lane_by_ref(first_lane.lane_ref).rows[0].sequence == 1  # type: ignore[union-attr]
    assert goal.lane_by_ref(second_lane.lane_ref).rows[0].sequence == 1  # type: ignore[union-attr]


def test_row_links_and_syncs_issue_without_changing_goal_status(actor, state) -> None:
    ensured = _ensure_goal(state, actor)
    assert ensured.goal_ref is not None
    active = apply_goal_intent(
        ensured.state,
        ActivateGoalIntent(
            context(actor, "activate"),
            goal_ref=ensured.goal_ref,
            expected_goal_revision=0,
        ),
    )
    lane_result = _ensure_lane(
        active.state,
        actor,
        ensured.goal_ref,
        1,
        "runtime",
        "lane-runtime",
    )
    assert lane_result.lane_ref is not None
    appended = apply_goal_intent(
        lane_result.state,
        AppendGoalLaneIssueIntent(
            context(actor, "row"),
            goal_ref=ensured.goal_ref,
            lane_ref=lane_result.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="values",
            gate="Values pass.",
            planned_issue_tag="fb/2026-08-27/values-v0",
        ),
    )
    assert appended.row_ref is not None
    linked = apply_goal_intent(
        appended.state,
        LinkGoalLaneIssueIntent(
            context(actor, "link"),
            goal_ref=ensured.goal_ref,
            lane_ref=lane_result.lane_ref,
            row_ref=appended.row_ref,
            expected_lane_revision=1,
            expected_row_revision=0,
            issue_ref="issue:values",
            issue_authority_receipt_ref="issue-receipt:open",
        ),
    )
    synced = apply_goal_intent(
        linked.state,
        SyncGoalLaneIssueIntent(
            context(actor, "sync"),
            goal_ref=ensured.goal_ref,
            lane_ref=lane_result.lane_ref,
            row_ref=appended.row_ref,
            expected_lane_revision=2,
            expected_row_revision=1,
            issue_ref="issue:values",
            issue_observation_ref="issue-observation:closed",
            status_snapshot="Closed",
            tick=GoalLaneIssueTick.COMPLETE,
            receipt_ref="repository-revision:values",
        ),
    )
    goal = synced.state.goal_by_ref(ensured.goal_ref)
    assert goal is not None and goal.status is GoalStatus.ACTIVE
    row = goal.lane_by_ref(lane_result.lane_ref).row_by_ref(appended.row_ref)  # type: ignore[union-attr]
    assert row is not None
    assert row.tick is GoalLaneIssueTick.COMPLETE
    assert row.issue_observation_ref == "issue-observation:closed"


def test_integrated_updates_have_independent_expected_head(actor, state) -> None:
    ensured = _ensure_goal(state, actor)
    assert ensured.goal_ref is not None
    first = apply_goal_intent(
        ensured.state,
        AppendGoalUpdateIntent(
            context(actor, "update-first"),
            goal_ref=ensured.goal_ref,
            expected_update_head_key=None,
            update_key="update:first",
            kind="goal_opened",
            message="Goal opened.",
        ),
    )
    stale = apply_goal_intent(
        first.state,
        AppendGoalUpdateIntent(
            context(actor, "update-stale"),
            goal_ref=ensured.goal_ref,
            expected_update_head_key=None,
            update_key="update:second",
            kind="goal_moved",
            message="Must not append.",
        ),
    )
    assert stale.outcome is TransitionOutcome.CONFLICT
    assert stale.blocker_code == "goal_update_head_mismatch"


def test_idempotency_replay_and_payload_reuse_are_distinct(actor, state) -> None:
    intent = EnsureGoalIntent(
        context(actor, "same"),
        tag="goal/2026-08-27/demo-v0",
        title="Demo",
    )
    first = apply_goal_intent(state, intent)
    replay = apply_goal_intent(first.state, intent)
    conflict = apply_goal_intent(
        first.state,
        EnsureGoalIntent(
            context(actor, "same"),
            tag="goal/2026-08-27/other-v0",
            title="Other",
        ),
    )
    assert replay.outcome is TransitionOutcome.IDEMPOTENT
    assert replay.goal_ref == first.goal_ref
    assert conflict.outcome is TransitionOutcome.CONFLICT
    assert conflict.blocker_code == "client_intent_id_reused"


def test_authority_generation_and_actor_admission_fail_closed(actor, state) -> None:
    stale = apply_goal_intent(
        state,
        EnsureGoalIntent(
            context(actor, "stale", generation=9),
            tag="goal/2026-08-27/stale-v0",
            title="Stale",
        ),
    )
    denied_actor = type(actor)(actor.actor_ref, actor.evidence_ref, accepted=False)
    denied = apply_goal_intent(
        state,
        EnsureGoalIntent(
            context(denied_actor, "denied"),
            tag="goal/2026-08-27/denied-v0",
            title="Denied",
        ),
    )
    assert stale.outcome is TransitionOutcome.STALE
    assert denied.outcome is TransitionOutcome.UNAUTHORIZED
