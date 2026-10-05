"""Evidence-qualified structural Goal frontier projection.

The projector composes explicit lane order, authored dependencies, supplied
evaluator observations, and supplied currentness. It does not discover edges,
evaluate evidence, select work, open Issues, or mutate Goal authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .dependencies import GoalDependency, GoalRowCoordinate, validate_dependency_set
from .dependency_observation_intake import (
    GoalDependencyObservationAvailability,
    GoalDependencyObservationIntake,
    decode_goal_dependency_observation_intake,
)
from .identity import normalize_goal_tag, required_text, required_token


class GoalFrontierSequenceState(StrEnum):
    COMPLETE = "complete"
    STRUCTURALLY_NEXT = "structurally_next"
    WAITING_FOR_PREDECESSOR = "waiting_for_predecessor"


class GoalFrontierDependencyGateState(StrEnum):
    NOT_APPLICABLE_YET = "not_applicable_yet"
    HELD = "held"
    SATISFIED = "satisfied"
    STALE = "stale"
    UNRESOLVED = "unresolved"


class GoalFrontierDependencyEvaluationState(StrEnum):
    NOT_APPLICABLE_YET = "not_applicable_yet"
    NOT_EVALUATED = "not_evaluated"
    PENDING = "pending"
    SATISFIED = "satisfied"
    STALE = "stale"
    UNRESOLVED = "unresolved"


class GoalFrontierAdmissionEligibility(StrEnum):
    COMPLETE = "complete"
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


class GoalFrontierCurrentness(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


class GoalFrontierProjectionHealth(StrEnum):
    CLEAN = "clean"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class GoalFrontierRowDefinition:
    coordinate: GoalRowCoordinate
    ordinal: int
    issue_ref: str
    completed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.coordinate, GoalRowCoordinate):
            raise TypeError("coordinate must be GoalRowCoordinate")
        if not isinstance(self.ordinal, int) or self.ordinal < 1:
            raise ValueError("ordinal must be a positive integer")
        _ = required_text(self.issue_ref, "issue_ref")
        if not isinstance(self.completed, bool):
            raise TypeError("completed must be bool")


@dataclass(frozen=True, slots=True)
class GoalFrontierLaneDefinition:
    lane_key: str
    rows: tuple[GoalFrontierRowDefinition, ...]
    projection_health: GoalFrontierProjectionHealth

    def __post_init__(self) -> None:
        _ = required_token(self.lane_key, "lane_key")
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not isinstance(self.projection_health, GoalFrontierProjectionHealth):
            raise TypeError("projection_health must be GoalFrontierProjectionHealth")
        expected = list(range(1, len(self.rows) + 1))
        if [row.ordinal for row in self.rows] != expected:
            raise ValueError("lane row ordinals must be contiguous and ordered")
        if any(row.coordinate.lane_key != self.lane_key for row in self.rows):
            raise ValueError("lane row coordinate differs from lane_key")
        seen_unfinished = False
        for row in self.rows:
            if not row.completed:
                seen_unfinished = True
            elif seen_unfinished:
                raise ValueError("completed row cannot follow an unfinished row")


@dataclass(frozen=True, slots=True)
class GoalFrontierDependencyGateV1:
    state: GoalFrontierDependencyGateState
    evaluation_state: GoalFrontierDependencyEvaluationState
    incoming_count: int
    dependency_keys: tuple[str, ...]
    satisfied_keys: tuple[str, ...]
    pending_keys: tuple[str, ...]
    not_evaluated_keys: tuple[str, ...]
    stale_keys: tuple[str, ...]
    unresolved_keys: tuple[str, ...]

    def to_wire(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "evaluation_state": self.evaluation_state.value,
            "incoming_count": self.incoming_count,
            "dependency_keys": list(self.dependency_keys),
            "satisfied_count": len(self.satisfied_keys),
            "satisfied": list(self.satisfied_keys),
            "pending": list(self.pending_keys),
            "not_evaluated": list(self.not_evaluated_keys),
            "stale": list(self.stale_keys),
            "unresolved": list(self.unresolved_keys),
        }


@dataclass(frozen=True, slots=True)
class GoalFrontierRowProjectionV1:
    coordinate: GoalRowCoordinate
    ordinal: int
    issue_ref: str
    sequence_state: GoalFrontierSequenceState
    predecessor_row_key: str | None
    projection_health: GoalFrontierProjectionHealth
    whole_goal_currentness: GoalFrontierCurrentness
    row_currentness: GoalFrontierCurrentness
    dependency_gate: GoalFrontierDependencyGateV1
    admission_eligibility: GoalFrontierAdmissionEligibility
    suggested_action: str

    def to_wire(self) -> dict[str, object]:
        return {
            "goal_tag": self.coordinate.goal_tag,
            "lane_key": self.coordinate.lane_key,
            "row_key": self.coordinate.row_key,
            "ordinal": self.ordinal,
            "issue_ref": self.issue_ref,
            "sequence_state": self.sequence_state.value,
            "predecessor_row_key": self.predecessor_row_key,
            "projection_health": self.projection_health.value,
            "whole_goal_currentness": self.whole_goal_currentness.value,
            "row_currentness": self.row_currentness.value,
            "dependency_gate": self.dependency_gate.to_wire(),
            "admission_eligibility": self.admission_eligibility.value,
            "suggested_action": self.suggested_action,
        }


@dataclass(frozen=True, slots=True)
class GoalFrontierLaneProjectionV1:
    lane_key: str
    rows: tuple[GoalFrontierRowProjectionV1, ...]

    @property
    def structural_frontier(self) -> GoalFrontierRowProjectionV1 | None:
        return next(
            (
                row
                for row in self.rows
                if row.sequence_state is GoalFrontierSequenceState.STRUCTURALLY_NEXT
            ),
            None,
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "lane_key": self.lane_key,
            "structural_frontier_row_key": (
                None
                if self.structural_frontier is None
                else self.structural_frontier.coordinate.row_key
            ),
            "rows": [row.to_wire() for row in self.rows],
        }


@dataclass(frozen=True, slots=True)
class GoalFrontierProjectionV1:
    goal_tag: str
    source_revision_ref: str | None
    whole_goal_currentness: GoalFrontierCurrentness
    lanes: tuple[GoalFrontierLaneProjectionV1, ...]

    @property
    def structural_frontier(self) -> tuple[GoalFrontierRowProjectionV1, ...]:
        return tuple(
            row for lane in self.lanes if (row := lane.structural_frontier) is not None
        )

    def to_wire(self) -> dict[str, object]:
        frontier = self.structural_frontier
        return {
            "schema_id": "aware.goal.frontier_projection.v1",
            "effect_profile": "read_only_non_authorizing",
            "goal_tag": self.goal_tag,
            "source_revision_ref": self.source_revision_ref,
            "whole_goal_currentness": self.whole_goal_currentness.value,
            "lanes": [lane.to_wire() for lane in self.lanes],
            "frontier": {
                "all": [_coordinate_wire(row.coordinate) for row in frontier],
                "eligible": _partition(frontier, eligibility="eligible"),
                "held": _partition(frontier, gate="held"),
                "stale": _partition(frontier, gate="stale"),
                "unresolved": _partition(frontier, gate="unresolved"),
                "not_evaluated": _partition(frontier, evaluation="not_evaluated"),
            },
        }


def project_goal_frontier(
    *,
    goal_tag: str,
    source_revision_ref: str | None,
    whole_goal_currentness: GoalFrontierCurrentness,
    lanes: tuple[GoalFrontierLaneDefinition, ...],
    dependencies: tuple[GoalDependency, ...],
    observations: Mapping[str, GoalDependencyObservationIntake] | None = None,
    row_currentness: Mapping[GoalRowCoordinate, GoalFrontierCurrentness] | None = None,
    current_revision_by_goal: Mapping[str, str] | None = None,
) -> GoalFrontierProjectionV1:
    """Project structural and dependency eligibility from explicit inputs."""

    normalized_goal_tag = normalize_goal_tag(goal_tag)
    if source_revision_ref is not None:
        source_revision_ref = required_token(source_revision_ref, "source_revision_ref")
    if not isinstance(whole_goal_currentness, GoalFrontierCurrentness):
        raise TypeError("whole_goal_currentness must be GoalFrontierCurrentness")
    if not isinstance(lanes, tuple) or not isinstance(dependencies, tuple):
        raise TypeError("lanes and dependencies must be tuples")
    validate_dependency_set(dependencies)
    lane_keys: set[str] = set()
    rows: dict[GoalRowCoordinate, GoalFrontierRowDefinition] = {}
    for lane in lanes:
        if lane.lane_key in lane_keys:
            raise ValueError("duplicate frontier lane_key")
        lane_keys.add(lane.lane_key)
        for row in lane.rows:
            if row.coordinate.goal_tag != normalized_goal_tag:
                raise ValueError("frontier row belongs to another Goal")
            if row.coordinate in rows:
                raise ValueError("duplicate frontier row coordinate")
            rows[row.coordinate] = row
    for dependency in dependencies:
        if dependency.owner_goal_tag != normalized_goal_tag:
            raise ValueError("dependency is not owned by frontier Goal")
        if dependency.dependent not in rows:
            raise ValueError("dependency dependent row is absent from frontier Goal")
    supplied = {} if observations is None else dict(observations)
    dependency_by_key = {item.dependency_key: item for item in dependencies}
    unknown = sorted(set(supplied) - set(dependency_by_key))
    if unknown:
        raise ValueError(
            "observations name undeclared dependencies: " + ",".join(unknown)
        )
    validated: dict[str, GoalDependencyObservationIntake] = {}
    for key, intake in supplied.items():
        if not isinstance(intake, GoalDependencyObservationIntake):
            raise TypeError("observations must contain typed observation intakes")
        validated[key] = decode_goal_dependency_observation_intake(
            intake.to_wire(), dependency=dependency_by_key[key]
        )
    current_revisions = {
        normalize_goal_tag(tag): required_token(revision, "current_revision")
        for tag, revision in (current_revision_by_goal or {}).items()
    }
    currentness = {} if row_currentness is None else dict(row_currentness)
    unknown_rows = sorted(
        (coordinate for coordinate in currentness if coordinate not in rows),
        key=lambda item: (item.goal_tag, item.lane_key, item.row_key),
    )
    if unknown_rows:
        raise ValueError("row currentness names a row outside the frontier Goal")
    incoming_by_row: dict[GoalRowCoordinate, list[GoalDependency]] = {}
    for dependency in dependencies:
        incoming_by_row.setdefault(dependency.dependent, []).append(dependency)

    lane_results = tuple(
        _project_lane(
            lane=lane,
            source_revision_ref=source_revision_ref,
            whole_goal_currentness=whole_goal_currentness,
            incoming_by_row=incoming_by_row,
            observations=validated,
            row_currentness=currentness,
            current_revision_by_goal=current_revisions,
        )
        for lane in sorted(lanes, key=lambda item: item.lane_key)
    )
    return GoalFrontierProjectionV1(
        goal_tag=normalized_goal_tag,
        source_revision_ref=source_revision_ref,
        whole_goal_currentness=whole_goal_currentness,
        lanes=lane_results,
    )


def _project_lane(
    *,
    lane: GoalFrontierLaneDefinition,
    source_revision_ref: str | None,
    whole_goal_currentness: GoalFrontierCurrentness,
    incoming_by_row: Mapping[GoalRowCoordinate, list[GoalDependency]],
    observations: Mapping[str, GoalDependencyObservationIntake],
    row_currentness: Mapping[GoalRowCoordinate, GoalFrontierCurrentness],
    current_revision_by_goal: Mapping[str, str],
) -> GoalFrontierLaneProjectionV1:
    frontier_index = next(
        (index for index, row in enumerate(lane.rows) if not row.completed),
        None,
    )
    projected: list[GoalFrontierRowProjectionV1] = []
    for index, row in enumerate(lane.rows):
        if row.completed:
            sequence_state = GoalFrontierSequenceState.COMPLETE
        elif index == frontier_index:
            sequence_state = GoalFrontierSequenceState.STRUCTURALLY_NEXT
        else:
            sequence_state = GoalFrontierSequenceState.WAITING_FOR_PREDECESSOR
        scoped_currentness = row_currentness.get(
            row.coordinate, GoalFrontierCurrentness.UNKNOWN
        )
        gate = _dependency_gate(
            sequence_state=sequence_state,
            dependencies=tuple(incoming_by_row.get(row.coordinate, ())),
            observations=observations,
            source_revision_ref=source_revision_ref,
            current_revision_by_goal=current_revision_by_goal,
        )
        eligible = (
            sequence_state is GoalFrontierSequenceState.STRUCTURALLY_NEXT
            and lane.projection_health is GoalFrontierProjectionHealth.CLEAN
            and whole_goal_currentness is GoalFrontierCurrentness.CURRENT
            and scoped_currentness is GoalFrontierCurrentness.CURRENT
            and gate.state is GoalFrontierDependencyGateState.SATISFIED
        )
        if sequence_state is GoalFrontierSequenceState.COMPLETE:
            admission = GoalFrontierAdmissionEligibility.COMPLETE
        elif eligible:
            admission = GoalFrontierAdmissionEligibility.ELIGIBLE
        else:
            admission = GoalFrontierAdmissionEligibility.INELIGIBLE
        if eligible:
            suggested_action = (
                "open_issue" if row.issue_ref.startswith("TBD:") else "continue_issue"
            )
        elif lane.projection_health is GoalFrontierProjectionHealth.AMBIGUOUS:
            suggested_action = "reconcile_goal_projection"
        elif sequence_state is GoalFrontierSequenceState.STRUCTURALLY_NEXT and (
            whole_goal_currentness is not GoalFrontierCurrentness.CURRENT
            or scoped_currentness is not GoalFrontierCurrentness.CURRENT
        ):
            suggested_action = "verify_currentness"
        else:
            suggested_action = "none"
        predecessor = None if index == 0 else lane.rows[index - 1].coordinate.row_key
        projected.append(
            GoalFrontierRowProjectionV1(
                coordinate=row.coordinate,
                ordinal=row.ordinal,
                issue_ref=row.issue_ref,
                sequence_state=sequence_state,
                predecessor_row_key=(
                    predecessor
                    if sequence_state
                    is GoalFrontierSequenceState.WAITING_FOR_PREDECESSOR
                    else None
                ),
                projection_health=lane.projection_health,
                whole_goal_currentness=whole_goal_currentness,
                row_currentness=scoped_currentness,
                dependency_gate=gate,
                admission_eligibility=admission,
                suggested_action=suggested_action,
            )
        )
    return GoalFrontierLaneProjectionV1(lane_key=lane.lane_key, rows=tuple(projected))


def _dependency_gate(
    *,
    sequence_state: GoalFrontierSequenceState,
    dependencies: tuple[GoalDependency, ...],
    observations: Mapping[str, GoalDependencyObservationIntake],
    source_revision_ref: str | None,
    current_revision_by_goal: Mapping[str, str],
) -> GoalFrontierDependencyGateV1:
    if sequence_state is not GoalFrontierSequenceState.STRUCTURALLY_NEXT:
        return GoalFrontierDependencyGateV1(
            state=GoalFrontierDependencyGateState.NOT_APPLICABLE_YET,
            evaluation_state=(GoalFrontierDependencyEvaluationState.NOT_APPLICABLE_YET),
            incoming_count=len(dependencies),
            dependency_keys=tuple(
                sorted(dependency.dependency_key for dependency in dependencies)
            ),
            satisfied_keys=(),
            pending_keys=(),
            not_evaluated_keys=(),
            stale_keys=(),
            unresolved_keys=(),
        )
    states: dict[str, list[str]] = {
        "satisfied": [],
        "pending": [],
        "not_evaluated": [],
        "stale": [],
        "unresolved": [],
    }
    for dependency in sorted(dependencies, key=lambda item: item.dependency_key):
        intake = observations.get(dependency.dependency_key)
        if (
            intake is None
            or intake.availability
            is GoalDependencyObservationAvailability.NOT_EVALUATED
        ):
            states["not_evaluated"].append(dependency.dependency_key)
            continue
        observation = intake.observation
        assert observation is not None
        if observation.satisfaction.value == "unresolved":
            states["unresolved"].append(dependency.dependency_key)
            continue
        if observation.satisfaction.value == "stale":
            states["stale"].append(dependency.dependency_key)
            continue
        dependent_revision = current_revision_by_goal.get(dependency.dependent.goal_tag)
        prerequisite_revision = current_revision_by_goal.get(
            dependency.prerequisite.goal_tag
        )
        if (
            source_revision_ref is None
            or dependent_revision != source_revision_ref
            or observation.dependent_source_revision_ref != dependent_revision
            or prerequisite_revision is None
            or observation.prerequisite_source_revision_ref != prerequisite_revision
        ):
            states["stale"].append(dependency.dependency_key)
            continue
        states[observation.satisfaction.value].append(dependency.dependency_key)
    if states["unresolved"]:
        gate_state = GoalFrontierDependencyGateState.UNRESOLVED
        evaluation_state = GoalFrontierDependencyEvaluationState.UNRESOLVED
    elif states["stale"]:
        gate_state = GoalFrontierDependencyGateState.STALE
        evaluation_state = GoalFrontierDependencyEvaluationState.STALE
    elif states["not_evaluated"]:
        gate_state = GoalFrontierDependencyGateState.HELD
        evaluation_state = GoalFrontierDependencyEvaluationState.NOT_EVALUATED
    elif states["pending"]:
        gate_state = GoalFrontierDependencyGateState.HELD
        evaluation_state = GoalFrontierDependencyEvaluationState.PENDING
    else:
        gate_state = GoalFrontierDependencyGateState.SATISFIED
        evaluation_state = GoalFrontierDependencyEvaluationState.SATISFIED
    return GoalFrontierDependencyGateV1(
        state=gate_state,
        evaluation_state=evaluation_state,
        incoming_count=len(dependencies),
        dependency_keys=tuple(
            sorted(dependency.dependency_key for dependency in dependencies)
        ),
        satisfied_keys=tuple(states["satisfied"]),
        pending_keys=tuple(states["pending"]),
        not_evaluated_keys=tuple(states["not_evaluated"]),
        stale_keys=tuple(states["stale"]),
        unresolved_keys=tuple(states["unresolved"]),
    )


def _partition(
    rows: tuple[GoalFrontierRowProjectionV1, ...],
    *,
    gate: str | None = None,
    evaluation: str | None = None,
    eligibility: str | None = None,
) -> list[dict[str, str]]:
    return [
        _coordinate_wire(row.coordinate)
        for row in rows
        if (gate is None or row.dependency_gate.state.value == gate)
        and (
            evaluation is None
            or row.dependency_gate.evaluation_state.value == evaluation
        )
        and (eligibility is None or row.admission_eligibility.value == eligibility)
    ]


def _coordinate_wire(coordinate: GoalRowCoordinate) -> dict[str, str]:
    return {
        "goal_tag": coordinate.goal_tag,
        "lane_key": coordinate.lane_key,
        "row_key": coordinate.row_key,
    }
