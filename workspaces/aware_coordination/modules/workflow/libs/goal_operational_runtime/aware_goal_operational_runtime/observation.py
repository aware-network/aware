from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .contracts import (
    GoalLaneIssueSnapshot,
    GoalLaneSnapshot,
    GoalOperationalState,
    GoalSnapshot,
)
from .identity import nonnegative, optional_token


class ObservationDepth(StrEnum):
    GOAL = "goal"
    LANE = "lane"
    ROW = "row"


class ObservationOutcome(StrEnum):
    FOUND = "found"
    ABSENT = "absent"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class GoalObservationQuery:
    depth: ObservationDepth
    goal_ref: str | None = None
    goal_tag: str | None = None
    lane_ref: str | None = None
    lane_key: str | None = None
    row_ref: str | None = None
    row_key: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.depth, ObservationDepth):
            raise TypeError("depth must be ObservationDepth")
        for field in (
            "goal_ref",
            "goal_tag",
            "lane_ref",
            "lane_key",
            "row_ref",
            "row_key",
        ):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        if self.goal_ref is not None and self.goal_tag is not None:
            raise ValueError("choose goal_ref or goal_tag")
        if self.lane_ref is not None and self.lane_key is not None:
            raise ValueError("choose lane_ref or lane_key")
        if self.row_ref is not None and self.row_key is not None:
            raise ValueError("choose row_ref or row_key")
        if self.depth is ObservationDepth.GOAL and any(
            value is not None
            for value in (self.lane_ref, self.lane_key, self.row_ref, self.row_key)
        ):
            raise ValueError("goal observation cannot carry lane or row selectors")
        if self.depth is ObservationDepth.LANE and any(
            value is not None for value in (self.row_ref, self.row_key)
        ):
            raise ValueError("lane observation cannot carry row selectors")


@dataclass(frozen=True, slots=True)
class GoalObservation:
    outcome: ObservationOutcome
    authority_ref: str
    authority_generation: int
    store_generation: int
    epoch: str
    journal_cursor: int
    state_digest: str
    goal: GoalSnapshot | None = None
    lane: GoalLaneSnapshot | None = None
    row: GoalLaneIssueSnapshot | None = None
    candidate_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, ObservationOutcome):
            raise TypeError("outcome must be ObservationOutcome")
        nonnegative(self.authority_generation, "authority_generation")
        nonnegative(self.store_generation, "store_generation")
        nonnegative(self.journal_cursor, "journal_cursor")
        if self.row is not None and self.lane is None:
            raise ValueError("row observation requires lane")
        if self.lane is not None and self.goal is None:
            raise ValueError("lane observation requires goal")
        if self.outcome is ObservationOutcome.FOUND and self.goal is None:
            raise ValueError("found observation requires goal")
        if (
            self.outcome is ObservationOutcome.AMBIGUOUS
            and len(self.candidate_refs) < 2
        ):
            raise ValueError("ambiguous observation requires multiple candidates")


def resolve_goal_observation(
    state: GoalOperationalState,
    query: GoalObservationQuery,
    *,
    store_generation: int,
    epoch: str,
    journal_cursor: int,
    state_digest: str,
) -> GoalObservation:
    goals = _select_goals(state, query)
    if not goals:
        return _observation(
            ObservationOutcome.ABSENT,
            state,
            store_generation,
            epoch,
            journal_cursor,
            state_digest,
        )
    if len(goals) > 1:
        return _observation(
            ObservationOutcome.AMBIGUOUS,
            state,
            store_generation,
            epoch,
            journal_cursor,
            state_digest,
            candidate_refs=tuple(goal.goal_ref for goal in goals),
        )
    goal = next(iter(goals))
    if query.depth is ObservationDepth.GOAL:
        return _observation(
            ObservationOutcome.FOUND,
            state,
            store_generation,
            epoch,
            journal_cursor,
            state_digest,
            goal=goal,
        )

    lanes = _select_lanes(goal, query)
    if not lanes:
        return _observation(
            ObservationOutcome.ABSENT,
            state,
            store_generation,
            epoch,
            journal_cursor,
            state_digest,
            goal=goal,
        )
    if len(lanes) > 1:
        return _observation(
            ObservationOutcome.AMBIGUOUS,
            state,
            store_generation,
            epoch,
            journal_cursor,
            state_digest,
            goal=goal,
            candidate_refs=tuple(lane.lane_ref for lane in lanes),
        )
    lane = next(iter(lanes))
    if query.depth is ObservationDepth.LANE:
        return _observation(
            ObservationOutcome.FOUND,
            state,
            store_generation,
            epoch,
            journal_cursor,
            state_digest,
            goal=goal,
            lane=lane,
        )

    rows = _select_rows(lane, query)
    if not rows:
        return _observation(
            ObservationOutcome.ABSENT,
            state,
            store_generation,
            epoch,
            journal_cursor,
            state_digest,
            goal=goal,
            lane=lane,
        )
    if len(rows) > 1:
        return _observation(
            ObservationOutcome.AMBIGUOUS,
            state,
            store_generation,
            epoch,
            journal_cursor,
            state_digest,
            goal=goal,
            lane=lane,
            candidate_refs=tuple(row.row_ref for row in rows),
        )
    return _observation(
        ObservationOutcome.FOUND,
        state,
        store_generation,
        epoch,
        journal_cursor,
        state_digest,
        goal=goal,
        lane=lane,
        row=next(iter(rows)),
    )


def _observation(
    outcome: ObservationOutcome,
    state: GoalOperationalState,
    store_generation: int,
    epoch: str,
    journal_cursor: int,
    state_digest: str,
    *,
    goal: GoalSnapshot | None = None,
    lane: GoalLaneSnapshot | None = None,
    row: GoalLaneIssueSnapshot | None = None,
    candidate_refs: tuple[str, ...] = (),
) -> GoalObservation:
    return GoalObservation(
        outcome=outcome,
        authority_ref=state.authority.authority_ref,
        authority_generation=state.authority.generation,
        store_generation=store_generation,
        epoch=epoch,
        journal_cursor=journal_cursor,
        state_digest=state_digest,
        goal=goal,
        lane=lane,
        row=row,
        candidate_refs=candidate_refs,
    )


def _select_goals(
    state: GoalOperationalState,
    query: GoalObservationQuery,
) -> tuple[GoalSnapshot, ...]:
    if query.goal_ref is not None:
        goal = state.goal_by_ref(query.goal_ref)
        return () if goal is None else (goal,)
    if query.goal_tag is not None:
        goal = state.goal_by_tag(query.goal_tag)
        return () if goal is None else (goal,)
    return state.goals


def _select_lanes(
    goal: GoalSnapshot,
    query: GoalObservationQuery,
) -> tuple[GoalLaneSnapshot, ...]:
    if query.lane_ref is not None:
        lane = goal.lane_by_ref(query.lane_ref)
        return () if lane is None else (lane,)
    if query.lane_key is not None:
        lane = goal.lane_by_key(query.lane_key)
        return () if lane is None else (lane,)
    return goal.lanes


def _select_rows(
    lane: GoalLaneSnapshot,
    query: GoalObservationQuery,
) -> tuple[GoalLaneIssueSnapshot, ...]:
    if query.row_ref is not None:
        row = lane.row_by_ref(query.row_ref)
        return () if row is None else (row,)
    if query.row_key is not None:
        row = lane.row_by_key(query.row_key)
        return () if row is None else (row,)
    return lane.rows
