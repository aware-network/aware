from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from conftest import context

from aware_goal_operational_runtime import (
    AppendGoalLaneIssueIntent,
    CancellationToken,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalLaneStatus,
    GoalOperationalRuntimeHost,
    HostOutcome,
    InMemoryGoalStateStore,
    PersistenceWriteResult,
    TransitionOutcome,
)


class _ConflictOnceStore(InMemoryGoalStateStore):
    def __init__(self) -> None:
        super().__init__()
        self.fail_next_cas = True

    def compare_and_set(
        self,
        authority_ref: str,
        *,
        expected_generation: int,
        payload: str,
    ) -> PersistenceWriteResult:
        if self.fail_next_cas:
            self.fail_next_cas = False
            current = self.read(authority_ref)
            assert current is not None
            return PersistenceWriteResult(False, current)
        return super().compare_and_set(
            authority_ref,
            expected_generation=expected_generation,
            payload=payload,
        )


def test_host_persists_then_restarts_with_exact_idempotent_receipt(
    actor, state
) -> None:
    store = InMemoryGoalStateStore()
    first_host = GoalOperationalRuntimeHost(store)
    authority_ref = state.authority.authority_ref
    assert first_host.admit_authority(authority_ref, state, epoch="epoch-1")
    intent = EnsureGoalIntent(
        context(actor, "restart-goal"),
        tag="goal/2026-08-27/restart-v0",
        title="Restart",
    )
    first = first_host.submit(authority_ref, intent)
    restarted = GoalOperationalRuntimeHost(store)
    replayed = restarted.submit(authority_ref, intent)

    assert first.outcome is HostOutcome.COMPLETED
    assert first.receipt is not None
    assert replayed.transition is not None
    assert replayed.transition.outcome is TransitionOutcome.IDEMPOTENT
    assert replayed.receipt == first.receipt
    assert restarted.replay(authority_ref, epoch="epoch-1", after_cursor=0).events


def test_cancelled_and_rejected_intents_never_persist(actor, state) -> None:
    store = InMemoryGoalStateStore()
    host = GoalOperationalRuntimeHost(store)
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-1")
    token = CancellationToken()
    token.cancel()
    cancelled = host.submit(
        authority_ref,
        EnsureGoalIntent(
            context(actor, "cancelled"),
            tag="goal/2026-08-27/cancelled-v0",
            title="Cancelled",
        ),
        cancellation=token,
    )
    rejected = host.submit(
        authority_ref,
        EnsureGoalIntent(
            context(actor, "wrong-generation", generation=9),
            tag="goal/2026-08-27/rejected-v0",
            title="Rejected",
        ),
    )
    current = host.read(authority_ref)
    assert cancelled.outcome is HostOutcome.CANCELLED
    assert rejected.transition is not None
    assert rejected.transition.outcome is TransitionOutcome.STALE
    assert current is not None and current.state.goals == ()
    assert current.journal.events == ()


def test_persistence_conflict_returns_no_receipt_or_claimed_event(actor, state) -> None:
    store = _ConflictOnceStore()
    host = GoalOperationalRuntimeHost(store)
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-1")
    result = host.submit(
        authority_ref,
        EnsureGoalIntent(
            context(actor, "conflict"),
            tag="goal/2026-08-27/conflict-v0",
            title="Conflict",
        ),
    )
    current = host.read(authority_ref)
    assert result.outcome is HostOutcome.PERSISTENCE_CONFLICT
    assert result.receipt is None
    assert current is not None and current.state.goals == ()
    assert current.journal.events == ()


def test_parallel_lanes_persist_independently_under_one_authority(actor, state) -> None:
    store = InMemoryGoalStateStore()
    host = GoalOperationalRuntimeHost(store)
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-1")
    goal = host.submit(
        authority_ref,
        EnsureGoalIntent(
            context(actor, "parallel-goal"),
            tag="goal/2026-08-27/parallel-v0",
            title="Parallel",
        ),
    )
    assert goal.transition is not None and goal.transition.goal_ref is not None
    goal_ref = goal.transition.goal_ref
    first_lane = host.submit(
        authority_ref,
        EnsureGoalLaneIntent(
            context(actor, "lane-one"),
            goal_ref=goal_ref,
            expected_goal_revision=0,
            lane_key="one",
            status=GoalLaneStatus.ACTIVE,
        ),
    )
    second_lane = host.submit(
        authority_ref,
        EnsureGoalLaneIntent(
            context(actor, "lane-two"),
            goal_ref=goal_ref,
            expected_goal_revision=1,
            lane_key="two",
            status=GoalLaneStatus.ACTIVE,
        ),
    )
    assert first_lane.transition is not None and first_lane.transition.lane_ref
    assert second_lane.transition is not None and second_lane.transition.lane_ref

    intents = (
        AppendGoalLaneIssueIntent(
            context(actor, "row-one"),
            goal_ref=goal_ref,
            lane_ref=first_lane.transition.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="row-one",
            gate="One passes.",
        ),
        AppendGoalLaneIssueIntent(
            context(actor, "row-two"),
            goal_ref=goal_ref,
            lane_ref=second_lane.transition.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="row-two",
            gate="Two passes.",
        ),
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(
            executor.map(lambda item: host.submit(authority_ref, item), intents)
        )
    assert all(
        result.transition is not None
        and result.transition.outcome is TransitionOutcome.APPLIED
        for result in results
    )
    current = host.read(authority_ref)
    assert current is not None
    stored_goal = current.state.goal_by_ref(goal_ref)
    assert stored_goal is not None
    assert tuple(len(lane.rows) for lane in stored_goal.lanes) == (1, 1)
