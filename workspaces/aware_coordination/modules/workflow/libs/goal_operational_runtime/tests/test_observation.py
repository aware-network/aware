from __future__ import annotations

from conftest import context

from aware_goal_operational_runtime import (
    AppendGoalLaneIssueIntent,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalLaneStatus,
    GoalObservationQuery,
    GoalOperationalRuntimeHost,
    InMemoryGoalStateStore,
    ObservationDepth,
    ObservationOutcome,
)


def test_observation_is_exact_absent_or_ambiguous(actor, state) -> None:
    store = InMemoryGoalStateStore()
    host = GoalOperationalRuntimeHost(store)
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-1")
    for key in ("first", "second"):
        host.submit(
            authority_ref,
            EnsureGoalIntent(
                context(actor, key),
                tag=f"goal/2026-08-27/{key}-v0",
                title=key.title(),
            ),
        )

    ambiguous = host.observe(
        authority_ref,
        GoalObservationQuery(ObservationDepth.GOAL),
    )
    found = host.observe(
        authority_ref,
        GoalObservationQuery(
            ObservationDepth.GOAL,
            goal_tag="goal/2026-08-27/first-v0",
        ),
    )
    absent = host.observe(
        authority_ref,
        GoalObservationQuery(
            ObservationDepth.GOAL,
            goal_ref="goal-operational:missing",
        ),
    )
    assert ambiguous is not None
    assert ambiguous.outcome is ObservationOutcome.AMBIGUOUS
    assert len(ambiguous.candidate_refs) == 2
    assert found is not None and found.outcome is ObservationOutcome.FOUND
    assert found.goal is not None and found.goal.title == "First"
    assert found.store_generation == 2 and found.journal_cursor == 2
    assert absent is not None and absent.outcome is ObservationOutcome.ABSENT


def test_observation_resolves_exact_lane_and_row_coordinates(actor, state) -> None:
    store = InMemoryGoalStateStore()
    host = GoalOperationalRuntimeHost(store)
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-1")
    goal = host.submit(
        authority_ref,
        EnsureGoalIntent(
            context(actor, "coordinate-goal"),
            tag="goal/2026-08-27/coordinates-v0",
            title="Coordinates",
        ),
    )
    assert goal.transition is not None and goal.transition.goal_ref
    lane = host.submit(
        authority_ref,
        EnsureGoalLaneIntent(
            context(actor, "coordinate-lane"),
            goal_ref=goal.transition.goal_ref,
            expected_goal_revision=0,
            lane_key="runtime",
            status=GoalLaneStatus.ACTIVE,
        ),
    )
    assert lane.transition is not None and lane.transition.lane_ref
    host.submit(
        authority_ref,
        AppendGoalLaneIssueIntent(
            context(actor, "coordinate-row"),
            goal_ref=goal.transition.goal_ref,
            lane_ref=lane.transition.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="durable-host",
            gate="Host passes.",
        ),
    )
    observed = host.observe(
        authority_ref,
        GoalObservationQuery(
            ObservationDepth.ROW,
            goal_ref=goal.transition.goal_ref,
            lane_key="runtime",
            row_key="durable-host",
        ),
    )
    assert observed is not None and observed.outcome is ObservationOutcome.FOUND
    assert (
        observed.goal is not None and observed.goal.goal_ref == goal.transition.goal_ref
    )
    assert (
        observed.lane is not None and observed.lane.lane_ref == lane.transition.lane_ref
    )
    assert observed.row is not None and observed.row.row_key == "durable-host"
