from __future__ import annotations

from dataclasses import replace

from .contracts import (
    AchieveGoalIntent,
    ActivateGoalIntent,
    AppendGoalLaneIssueIntent,
    AppendGoalUpdateIntent,
    BlockGoalIntent,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalIntegratedUpdate,
    GoalIntent,
    GoalLaneIssueSnapshot,
    GoalLaneSnapshot,
    GoalLifecycleIntent,
    GoalOperationalState,
    GoalSnapshot,
    GoalStatus,
    IntentRecord,
    LinkGoalLaneIssueIntent,
    ParkGoalIntent,
    ResumeGoalIntent,
    SupersedeGoalIntent,
    SyncGoalLaneIssueIntent,
    TransitionOutcome,
    TransitionResult,
)
from .identity import fingerprint, stable_ref

_MAX_INTENT_RECORDS = 256


def apply_goal_intent(
    state: GoalOperationalState,
    intent: GoalIntent,
) -> TransitionResult:
    """Apply one immutable Goal intent without performing I/O."""

    intent_fingerprint = fingerprint(intent.to_wire())
    existing = next(
        (
            item
            for item in state.intent_records
            if item.client_intent_id == intent.context.client_intent_id
        ),
        None,
    )
    if existing is not None:
        if existing.fingerprint != intent_fingerprint:
            return _unchanged(
                state,
                TransitionOutcome.CONFLICT,
                "client_intent_id_reused",
            )
        return _result_for_refs(
            state=state,
            outcome=TransitionOutcome.IDEMPOTENT,
            goal_ref=existing.goal_ref,
            lane_ref=existing.lane_ref,
            row_ref=existing.row_ref,
        )
    if not intent.context.actor_evidence.accepted:
        return _unchanged(state, TransitionOutcome.UNAUTHORIZED, "actor_not_accepted")
    if intent.context.expected_authority_generation != state.authority.generation:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "authority_generation_mismatch",
        )

    if isinstance(intent, EnsureGoalIntent):
        result = _ensure_goal(state, intent)
    elif isinstance(intent, EnsureGoalLaneIntent):
        result = _ensure_lane(state, intent)
    elif isinstance(intent, AppendGoalLaneIssueIntent):
        result = _append_row(state, intent)
    elif isinstance(intent, LinkGoalLaneIssueIntent):
        result = _link_issue(state, intent)
    elif isinstance(intent, SyncGoalLaneIssueIntent):
        result = _sync_issue(state, intent)
    elif isinstance(intent, AppendGoalUpdateIntent):
        result = _append_update(state, intent)
    else:
        result = _transition_goal(state, intent)

    if result.outcome is not TransitionOutcome.APPLIED:
        return result
    record = IntentRecord(
        client_intent_id=intent.context.client_intent_id,
        fingerprint=intent_fingerprint,
        outcome=TransitionOutcome.APPLIED,
        goal_ref=result.goal_ref,
        lane_ref=result.lane_ref,
        row_ref=result.row_ref,
    )
    records = (*result.state.intent_records, record)[-_MAX_INTENT_RECORDS:]
    return replace(result, state=replace(result.state, intent_records=records))


def _ensure_goal(
    state: GoalOperationalState,
    intent: EnsureGoalIntent,
) -> TransitionResult:
    existing = state.goal_by_tag(intent.tag)
    if existing is not None:
        expected = (
            intent.title,
            intent.priority_level,
            intent.definition_of_done_ref,
            intent.locks_ref,
            intent.evidence_ref,
        )
        observed = (
            existing.title,
            existing.priority_level,
            existing.definition_of_done_ref,
            existing.locks_ref,
            existing.evidence_ref,
        )
        if expected != observed:
            return _unchanged(
                state,
                TransitionOutcome.CONFLICT,
                "goal_tag_already_exists",
                goal=existing,
            )
        return _result_for_refs(
            state=state,
            outcome=TransitionOutcome.IDEMPOTENT,
            goal_ref=existing.goal_ref,
        )
    goal_ref = stable_ref(
        kind="goal-operational",
        authority_ref=state.authority.authority_ref,
        coordinates=(intent.tag,),
    )
    goal = GoalSnapshot(
        goal_ref=goal_ref,
        tag=intent.tag,
        title=intent.title,
        priority_level=intent.priority_level,
        definition_of_done_ref=intent.definition_of_done_ref,
        locks_ref=intent.locks_ref,
        evidence_ref=intent.evidence_ref,
    )
    goals = tuple(sorted((*state.goals, goal), key=lambda item: item.goal_ref))
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=replace(state, goals=goals),
        changed=True,
        goal_ref=goal.goal_ref,
        goal_revision=goal.revision,
    )


def _transition_goal(
    state: GoalOperationalState,
    intent: GoalLifecycleIntent,
) -> TransitionResult:
    goal = state.goal_by_ref(intent.goal_ref)
    if goal is None:
        return _unchanged(state, TransitionOutcome.UNRESOLVED, "goal_not_found")
    if intent.expected_goal_revision != goal.revision:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "goal_revision_mismatch",
            goal=goal,
        )
    target = _goal_lifecycle_target(goal.status, intent)
    if target is None:
        return _unchanged(
            state,
            TransitionOutcome.INVALID,
            "invalid_goal_lifecycle_transition",
            goal=goal,
        )
    if isinstance(intent, BlockGoalIntent) and intent.reason is None:
        return _unchanged(
            state,
            TransitionOutcome.INVALID,
            "block_reason_required",
            goal=goal,
        )
    if isinstance(intent, (AchieveGoalIntent, SupersedeGoalIntent)) and (
        intent.evidence_ref is None
    ):
        blocker = (
            "achievement_evidence_required"
            if isinstance(intent, AchieveGoalIntent)
            else "supersession_evidence_required"
        )
        return _unchanged(state, TransitionOutcome.INVALID, blocker, goal=goal)
    updated = replace(goal, status=target, revision=goal.revision + 1)
    next_state = _replace_goal(state, updated)
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=next_state,
        changed=True,
        goal_ref=updated.goal_ref,
        goal_revision=updated.revision,
    )


def _goal_lifecycle_target(
    status: GoalStatus,
    intent: GoalLifecycleIntent,
) -> GoalStatus | None:
    if isinstance(intent, ActivateGoalIntent) and status in {
        GoalStatus.PROPOSED,
        GoalStatus.PARKED,
        GoalStatus.BLOCKED,
    }:
        return GoalStatus.ACTIVE
    if isinstance(intent, BlockGoalIntent) and status in {
        GoalStatus.PROPOSED,
        GoalStatus.ACTIVE,
    }:
        return GoalStatus.BLOCKED
    if isinstance(intent, ResumeGoalIntent) and status in {
        GoalStatus.BLOCKED,
        GoalStatus.PARKED,
    }:
        return GoalStatus.ACTIVE
    if isinstance(intent, ParkGoalIntent) and status in {
        GoalStatus.PROPOSED,
        GoalStatus.ACTIVE,
        GoalStatus.BLOCKED,
    }:
        return GoalStatus.PARKED
    if isinstance(intent, AchieveGoalIntent) and status in {
        GoalStatus.ACTIVE,
        GoalStatus.BLOCKED,
    }:
        return GoalStatus.ACHIEVED
    if isinstance(intent, SupersedeGoalIntent) and status in {
        GoalStatus.PROPOSED,
        GoalStatus.ACTIVE,
        GoalStatus.BLOCKED,
        GoalStatus.PARKED,
    }:
        return GoalStatus.SUPERSEDED
    return None


def _ensure_lane(
    state: GoalOperationalState,
    intent: EnsureGoalLaneIntent,
) -> TransitionResult:
    goal = state.goal_by_ref(intent.goal_ref)
    if goal is None:
        return _unchanged(state, TransitionOutcome.UNRESOLVED, "goal_not_found")
    if intent.expected_goal_revision != goal.revision:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "goal_revision_mismatch",
            goal=goal,
        )
    existing = goal.lane_by_key(intent.lane_key)
    if existing is not None:
        expected = (
            intent.status,
            intent.role_key,
            intent.role_label,
            intent.owner_execution_id,
            intent.scope,
        )
        observed = (
            existing.status,
            existing.role_key,
            existing.role_label,
            existing.owner_execution_id,
            existing.scope,
        )
        if expected != observed:
            return _unchanged(
                state,
                TransitionOutcome.CONFLICT,
                "lane_key_already_exists",
                goal=goal,
                lane=existing,
            )
        return _result_for_refs(
            state=state,
            outcome=TransitionOutcome.IDEMPOTENT,
            goal_ref=goal.goal_ref,
            lane_ref=existing.lane_ref,
        )
    lane_ref = stable_ref(
        kind="goal-lane-operational",
        authority_ref=state.authority.authority_ref,
        coordinates=(goal.goal_ref, intent.lane_key),
    )
    lane = GoalLaneSnapshot(
        lane_ref=lane_ref,
        lane_key=intent.lane_key,
        status=intent.status,
        role_key=intent.role_key,
        role_label=intent.role_label,
        owner_execution_id=intent.owner_execution_id,
        scope=intent.scope,
    )
    updated_goal = replace(
        goal,
        lanes=tuple(sorted((*goal.lanes, lane), key=lambda item: item.lane_ref)),
        revision=goal.revision + 1,
    )
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=_replace_goal(state, updated_goal),
        changed=True,
        goal_ref=goal.goal_ref,
        lane_ref=lane.lane_ref,
        goal_revision=updated_goal.revision,
        lane_revision=lane.revision,
    )


def _append_row(
    state: GoalOperationalState,
    intent: AppendGoalLaneIssueIntent,
) -> TransitionResult:
    resolved = _resolve_lane(state, intent.goal_ref, intent.lane_ref)
    if isinstance(resolved, TransitionResult):
        return resolved
    goal, lane = resolved
    if intent.expected_lane_revision != lane.revision:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "lane_revision_mismatch",
            goal=goal,
            lane=lane,
        )
    if intent.expected_head_row_ref != lane.head_row_ref:
        return TransitionResult(
            outcome=TransitionOutcome.CONFLICT,
            state=state,
            blocker_code="lane_head_mismatch",
            goal_ref=goal.goal_ref,
            lane_ref=lane.lane_ref,
            goal_revision=goal.revision,
            lane_revision=lane.revision,
            actual_head_row_ref=lane.head_row_ref,
        )
    if lane.row_by_key(intent.row_key) is not None:
        return _unchanged(
            state,
            TransitionOutcome.CONFLICT,
            "row_key_already_exists",
            goal=goal,
            lane=lane,
        )
    row_ref = stable_ref(
        kind="goal-lane-issue-operational",
        authority_ref=state.authority.authority_ref,
        coordinates=(lane.lane_ref, intent.row_key),
    )
    row = GoalLaneIssueSnapshot(
        row_ref=row_ref,
        row_key=intent.row_key,
        sequence=len(lane.rows) + 1,
        gate=intent.gate,
        previous_row_ref=lane.head_row_ref,
        prerequisite_refs=intent.prerequisite_refs,
        planned_issue_tag=intent.planned_issue_tag,
        owner_execution_id=intent.owner_execution_id,
    )
    updated_lane = replace(
        lane,
        head_row_ref=row.row_ref,
        rows=(*lane.rows, row),
        revision=lane.revision + 1,
    )
    next_state, updated_goal = _replace_lane(state, goal, updated_lane)
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=next_state,
        changed=True,
        goal_ref=goal.goal_ref,
        lane_ref=lane.lane_ref,
        row_ref=row.row_ref,
        goal_revision=updated_goal.revision,
        lane_revision=updated_lane.revision,
        row_revision=row.revision,
        actual_head_row_ref=row.row_ref,
    )


def _link_issue(
    state: GoalOperationalState,
    intent: LinkGoalLaneIssueIntent,
) -> TransitionResult:
    resolved = _resolve_row(state, intent.goal_ref, intent.lane_ref, intent.row_ref)
    if isinstance(resolved, TransitionResult):
        return resolved
    goal, lane, row = resolved
    stale = _row_revision_failure(state, goal, lane, row, intent)
    if stale is not None:
        return stale
    if row.issue_ref is not None:
        if (
            row.issue_ref == intent.issue_ref
            and row.issue_authority_receipt_ref == intent.issue_authority_receipt_ref
        ):
            return _result_for_refs(
                state=state,
                outcome=TransitionOutcome.IDEMPOTENT,
                goal_ref=goal.goal_ref,
                lane_ref=lane.lane_ref,
                row_ref=row.row_ref,
            )
        return _unchanged(
            state,
            TransitionOutcome.CONFLICT,
            "row_issue_already_linked",
            goal=goal,
            lane=lane,
            row=row,
        )
    updated_row = replace(
        row,
        issue_ref=intent.issue_ref,
        issue_authority_receipt_ref=intent.issue_authority_receipt_ref,
        revision=row.revision + 1,
    )
    return _apply_row_update(state, goal, lane, updated_row)


def _sync_issue(
    state: GoalOperationalState,
    intent: SyncGoalLaneIssueIntent,
) -> TransitionResult:
    resolved = _resolve_row(state, intent.goal_ref, intent.lane_ref, intent.row_ref)
    if isinstance(resolved, TransitionResult):
        return resolved
    goal, lane, row = resolved
    stale = _row_revision_failure(state, goal, lane, row, intent)
    if stale is not None:
        return stale
    if row.issue_ref != intent.issue_ref:
        return _unchanged(
            state,
            TransitionOutcome.CONFLICT,
            "issue_ref_mismatch",
            goal=goal,
            lane=lane,
            row=row,
        )
    updated_row = replace(
        row,
        issue_observation_ref=intent.issue_observation_ref,
        status_snapshot=intent.status_snapshot,
        tick=intent.tick,
        owner_execution_id=intent.owner_execution_id,
        receipt_ref=intent.receipt_ref,
        revision=row.revision + 1,
    )
    return _apply_row_update(state, goal, lane, updated_row)


def _append_update(
    state: GoalOperationalState,
    intent: AppendGoalUpdateIntent,
) -> TransitionResult:
    goal = state.goal_by_ref(intent.goal_ref)
    if goal is None:
        return _unchanged(state, TransitionOutcome.UNRESOLVED, "goal_not_found")
    if intent.expected_update_head_key != goal.update_head_key:
        return _unchanged(
            state,
            TransitionOutcome.CONFLICT,
            "goal_update_head_mismatch",
            goal=goal,
        )
    if any(update.update_key == intent.update_key for update in goal.updates):
        return _unchanged(
            state,
            TransitionOutcome.CONFLICT,
            "goal_update_key_already_exists",
            goal=goal,
        )
    if intent.lane_ref is not None:
        lane = goal.lane_by_ref(intent.lane_ref)
        if lane is None:
            return _unchanged(
                state,
                TransitionOutcome.UNRESOLVED,
                "update_lane_not_found",
                goal=goal,
            )
        if intent.row_ref is not None and lane.row_by_ref(intent.row_ref) is None:
            return _unchanged(
                state,
                TransitionOutcome.UNRESOLVED,
                "update_row_not_found",
                goal=goal,
                lane=lane,
            )
    update = GoalIntegratedUpdate(
        update_key=intent.update_key,
        sequence=len(goal.updates) + 1,
        kind=intent.kind,
        message=intent.message,
        actor_ref=intent.context.actor_evidence.actor_ref,
        actor_evidence_ref=intent.context.actor_evidence.evidence_ref,
        recorded_at=intent.recorded_at,
        lane_ref=intent.lane_ref,
        row_ref=intent.row_ref,
        receipt_ref=intent.receipt_ref,
    )
    updated = replace(
        goal,
        updates=(*goal.updates, update),
        revision=goal.revision + 1,
    )
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=_replace_goal(state, updated),
        changed=True,
        goal_ref=goal.goal_ref,
        lane_ref=intent.lane_ref,
        row_ref=intent.row_ref,
        goal_revision=updated.revision,
    )


def _row_revision_failure(
    state: GoalOperationalState,
    goal: GoalSnapshot,
    lane: GoalLaneSnapshot,
    row: GoalLaneIssueSnapshot,
    intent: LinkGoalLaneIssueIntent | SyncGoalLaneIssueIntent,
) -> TransitionResult | None:
    if intent.expected_lane_revision != lane.revision:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "lane_revision_mismatch",
            goal=goal,
            lane=lane,
            row=row,
        )
    if intent.expected_row_revision != row.revision:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "row_revision_mismatch",
            goal=goal,
            lane=lane,
            row=row,
        )
    return None


def _apply_row_update(
    state: GoalOperationalState,
    goal: GoalSnapshot,
    lane: GoalLaneSnapshot,
    updated_row: GoalLaneIssueSnapshot,
) -> TransitionResult:
    updated_lane = replace(
        lane,
        rows=tuple(
            updated_row if item.row_ref == updated_row.row_ref else item
            for item in lane.rows
        ),
        revision=lane.revision + 1,
    )
    next_state, updated_goal = _replace_lane(state, goal, updated_lane)
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=next_state,
        changed=True,
        goal_ref=goal.goal_ref,
        lane_ref=lane.lane_ref,
        row_ref=updated_row.row_ref,
        goal_revision=updated_goal.revision,
        lane_revision=updated_lane.revision,
        row_revision=updated_row.revision,
        actual_head_row_ref=updated_lane.head_row_ref,
    )


def _resolve_lane(
    state: GoalOperationalState,
    goal_ref: str,
    lane_ref: str,
) -> tuple[GoalSnapshot, GoalLaneSnapshot] | TransitionResult:
    goal = state.goal_by_ref(goal_ref)
    if goal is None:
        return _unchanged(state, TransitionOutcome.UNRESOLVED, "goal_not_found")
    lane = goal.lane_by_ref(lane_ref)
    if lane is None:
        return _unchanged(
            state,
            TransitionOutcome.UNRESOLVED,
            "lane_not_found",
            goal=goal,
        )
    return goal, lane


def _resolve_row(
    state: GoalOperationalState,
    goal_ref: str,
    lane_ref: str,
    row_ref: str,
) -> tuple[GoalSnapshot, GoalLaneSnapshot, GoalLaneIssueSnapshot] | TransitionResult:
    resolved = _resolve_lane(state, goal_ref, lane_ref)
    if isinstance(resolved, TransitionResult):
        return resolved
    goal, lane = resolved
    row = lane.row_by_ref(row_ref)
    if row is None:
        return _unchanged(
            state,
            TransitionOutcome.UNRESOLVED,
            "row_not_found",
            goal=goal,
            lane=lane,
        )
    return goal, lane, row


def _replace_lane(
    state: GoalOperationalState,
    goal: GoalSnapshot,
    updated_lane: GoalLaneSnapshot,
) -> tuple[GoalOperationalState, GoalSnapshot]:
    updated_goal = replace(
        goal,
        lanes=tuple(
            updated_lane if item.lane_ref == updated_lane.lane_ref else item
            for item in goal.lanes
        ),
        revision=goal.revision + 1,
    )
    return _replace_goal(state, updated_goal), updated_goal


def _replace_goal(
    state: GoalOperationalState,
    updated_goal: GoalSnapshot,
) -> GoalOperationalState:
    return replace(
        state,
        goals=tuple(
            updated_goal if item.goal_ref == updated_goal.goal_ref else item
            for item in state.goals
        ),
    )


def _result_for_refs(
    *,
    state: GoalOperationalState,
    outcome: TransitionOutcome,
    goal_ref: str | None,
    lane_ref: str | None = None,
    row_ref: str | None = None,
) -> TransitionResult:
    goal = state.goal_by_ref(goal_ref) if goal_ref is not None else None
    lane = (
        goal.lane_by_ref(lane_ref)
        if goal is not None and lane_ref is not None
        else None
    )
    row = lane.row_by_ref(row_ref) if lane is not None and row_ref is not None else None
    return TransitionResult(
        outcome=outcome,
        state=state,
        goal_ref=goal_ref,
        lane_ref=lane_ref,
        row_ref=row_ref,
        goal_revision=None if goal is None else goal.revision,
        lane_revision=None if lane is None else lane.revision,
        row_revision=None if row is None else row.revision,
        actual_head_row_ref=None if lane is None else lane.head_row_ref,
    )


def _unchanged(
    state: GoalOperationalState,
    outcome: TransitionOutcome,
    blocker_code: str,
    *,
    goal: GoalSnapshot | None = None,
    lane: GoalLaneSnapshot | None = None,
    row: GoalLaneIssueSnapshot | None = None,
) -> TransitionResult:
    return TransitionResult(
        outcome=outcome,
        state=state,
        blocker_code=blocker_code,
        goal_ref=None if goal is None else goal.goal_ref,
        lane_ref=None if lane is None else lane.lane_ref,
        row_ref=None if row is None else row.row_ref,
        goal_revision=None if goal is None else goal.revision,
        lane_revision=None if lane is None else lane.revision,
        row_revision=None if row is None else row.revision,
        actual_head_row_ref=None if lane is None else lane.head_row_ref,
    )
