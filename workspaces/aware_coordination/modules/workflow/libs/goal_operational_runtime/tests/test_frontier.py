from __future__ import annotations

from aware_goal_operational_runtime import (
    GoalDependency,
    GoalDependencyEvidence,
    GoalDependencyEvidenceKind,
    GoalDependencyRelation,
    GoalFrontierAdmissionEligibility,
    GoalFrontierCurrentness,
    GoalFrontierDependencyEvaluationState,
    GoalFrontierDependencyGateState,
    GoalFrontierLaneDefinition,
    GoalFrontierProjectionHealth,
    GoalFrontierRowDefinition,
    GoalFrontierSequenceState,
    GoalRowCoordinate,
    GoalRowResolutionOutcome,
    GoalRowSourceObservation,
    compose_goal_dependency_observation_intake,
    dependency_definition_digest,
    evaluate_goal_dependency,
    project_goal_frontier,
)

GOAL = "goal/actorworld"
REVISION = "git:actorworld-current"
CURRENT_REVISIONS = {
    GOAL: REVISION,
    "goal/external": "git:external-current",
}


def _row(lane: str, key: str, ordinal: int, *, complete: bool = False):
    return GoalFrontierRowDefinition(
        coordinate=GoalRowCoordinate(GOAL, lane, key),
        ordinal=ordinal,
        issue_ref=f"TBD:{key}",
        completed=complete,
    )


def _dependency(dependent_lane: str, dependent_row: str, key: str):
    return GoalDependency(
        owner_goal_tag=GOAL,
        dependency_key=key,
        dependent_lane_key=dependent_lane,
        dependent_row_key=dependent_row,
        prerequisite_goal_tag="goal/external",
        prerequisite_lane_key="product",
        prerequisite_row_key=key,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        reason="Exact external acceptance is required.",
    )


def _intake(dependency: GoalDependency, *, satisfaction: str, revision=REVISION):
    evidence = ()
    prerequisite = (
        GoalRowSourceObservation(
            dependency.prerequisite,
            GoalRowResolutionOutcome.UNRESOLVED,
        )
        if satisfaction == "unresolved"
        else GoalRowSourceObservation(
            dependency.prerequisite,
            GoalRowResolutionOutcome.RESOLVED,
            source_revision_ref="git:external-current",
            gate_digest="sha256:gate",
        )
    )
    if satisfaction == "satisfied":
        evidence = (
            GoalDependencyEvidence(
                owner_goal_tag=dependency.owner_goal_tag,
                dependency_key=dependency.dependency_key,
                dependency_digest=dependency_definition_digest(dependency),
                prerequisite=dependency.prerequisite,
                dependent_source_revision_ref=revision,
                prerequisite_source_revision_ref="git:external-current",
                prerequisite_gate_digest="sha256:gate",
                kind=GoalDependencyEvidenceKind.ACCEPTANCE,
                evidence_ref=f"acceptance:{dependency.dependency_key}",
                qualification_ref=f"qualification:{dependency.dependency_key}",
            ),
        )
    observation = evaluate_goal_dependency(
        dependency,
        dependent=GoalRowSourceObservation(
            dependency.dependent,
            GoalRowResolutionOutcome.RESOLVED,
            source_revision_ref=revision,
        ),
        prerequisite=prerequisite,
        evidence=evidence,
        evaluator_ref="goal-dependency-evaluator:test",
    )
    return compose_goal_dependency_observation_intake(dependency, observation)


def test_frontier_separates_sequence_dependency_and_eligibility() -> None:
    baseline = _dependency("agent", "a2", "product-baseline")
    i2 = _dependency("runtime", "r3", "i2")
    a3 = _dependency("runtime", "r3", "a3")
    g5 = _dependency("runtime", "r3", "g5")
    lanes = (
        GoalFrontierLaneDefinition(
            "agent",
            (
                _row("agent", "a1", 1, complete=True),
                _row("agent", "a2", 2),
                _row("agent", "a3", 3),
            ),
            GoalFrontierProjectionHealth.CLEAN,
        ),
        GoalFrontierLaneDefinition(
            "runtime",
            (_row("runtime", "i2", 1, complete=True), _row("runtime", "r3", 2)),
            GoalFrontierProjectionHealth.CLEAN,
        ),
    )
    row_currentness = {
        row.coordinate: GoalFrontierCurrentness.CURRENT
        for lane in lanes
        for row in lane.rows
    }
    projection = project_goal_frontier(
        goal_tag=GOAL,
        source_revision_ref=REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        lanes=lanes,
        dependencies=(baseline, i2, a3, g5),
        observations={"i2": _intake(i2, satisfaction="satisfied")},
        row_currentness=row_currentness,
        current_revision_by_goal=CURRENT_REVISIONS,
    )
    agent_rows = projection.lanes[0].rows
    assert agent_rows[1].sequence_state is GoalFrontierSequenceState.STRUCTURALLY_NEXT
    assert agent_rows[1].dependency_gate.state is GoalFrontierDependencyGateState.HELD
    assert (
        agent_rows[1].dependency_gate.evaluation_state
        is GoalFrontierDependencyEvaluationState.NOT_EVALUATED
    )
    assert agent_rows[1].suggested_action == "none"
    assert (
        agent_rows[2].sequence_state
        is GoalFrontierSequenceState.WAITING_FOR_PREDECESSOR
    )
    assert agent_rows[2].predecessor_row_key == "a2"
    assert (
        agent_rows[2].dependency_gate.state
        is GoalFrontierDependencyGateState.NOT_APPLICABLE_YET
    )
    runtime_frontier = projection.lanes[1].structural_frontier
    assert runtime_frontier is not None
    assert runtime_frontier.coordinate.row_key == "r3"
    assert (
        runtime_frontier.dependency_gate.state is GoalFrontierDependencyGateState.HELD
    )
    assert (
        runtime_frontier.dependency_gate.evaluation_state
        is GoalFrontierDependencyEvaluationState.NOT_EVALUATED
    )
    assert runtime_frontier.dependency_gate.satisfied_keys == ("i2",)
    assert runtime_frontier.dependency_gate.not_evaluated_keys == ("a3", "g5")
    assert (
        runtime_frontier.admission_eligibility
        is GoalFrontierAdmissionEligibility.INELIGIBLE
    )


def test_only_current_satisfied_frontier_is_eligible() -> None:
    dependency = _dependency("agent", "a2", "product-baseline")
    lane = GoalFrontierLaneDefinition(
        "agent",
        (_row("agent", "a2", 1),),
        GoalFrontierProjectionHealth.CLEAN,
    )
    coordinate = lane.rows[0].coordinate
    current = project_goal_frontier(
        goal_tag=GOAL,
        source_revision_ref=REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        lanes=(lane,),
        dependencies=(dependency,),
        observations={
            dependency.dependency_key: _intake(dependency, satisfaction="satisfied")
        },
        row_currentness={coordinate: GoalFrontierCurrentness.CURRENT},
        current_revision_by_goal=CURRENT_REVISIONS,
    ).structural_frontier[0]
    assert current.dependency_gate.state is GoalFrontierDependencyGateState.SATISFIED
    assert current.admission_eligibility is GoalFrontierAdmissionEligibility.ELIGIBLE
    assert current.suggested_action == "open_issue"

    stale = project_goal_frontier(
        goal_tag=GOAL,
        source_revision_ref="git:new",
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        lanes=(lane,),
        dependencies=(dependency,),
        observations={
            dependency.dependency_key: _intake(dependency, satisfaction="satisfied")
        },
        row_currentness={coordinate: GoalFrontierCurrentness.CURRENT},
        current_revision_by_goal={
            **CURRENT_REVISIONS,
            GOAL: "git:new",
        },
    ).structural_frontier[0]
    assert stale.dependency_gate.state is GoalFrontierDependencyGateState.STALE
    assert stale.admission_eligibility is GoalFrontierAdmissionEligibility.INELIGIBLE


def test_projection_health_and_currentness_are_independent() -> None:
    lane = GoalFrontierLaneDefinition(
        "agent",
        (_row("agent", "a2", 1),),
        GoalFrontierProjectionHealth.AMBIGUOUS,
    )
    row = project_goal_frontier(
        goal_tag=GOAL,
        source_revision_ref=REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        lanes=(lane,),
        dependencies=(),
        row_currentness={lane.rows[0].coordinate: GoalFrontierCurrentness.CURRENT},
        current_revision_by_goal=CURRENT_REVISIONS,
    ).structural_frontier[0]
    assert row.dependency_gate.state is GoalFrontierDependencyGateState.SATISFIED
    assert row.admission_eligibility is GoalFrontierAdmissionEligibility.INELIGIBLE
    assert row.suggested_action == "reconcile_goal_projection"


def test_pending_and_unresolved_observations_remain_distinct() -> None:
    pending = _dependency("agent", "a2", "pending-input")
    unresolved = _dependency("agent", "a2", "unresolved-input")
    lane = GoalFrontierLaneDefinition(
        "agent",
        (_row("agent", "a2", 1),),
        GoalFrontierProjectionHealth.CLEAN,
    )
    row = project_goal_frontier(
        goal_tag=GOAL,
        source_revision_ref=REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        lanes=(lane,),
        dependencies=(pending, unresolved),
        observations={
            pending.dependency_key: _intake(pending, satisfaction="pending"),
            unresolved.dependency_key: _intake(unresolved, satisfaction="unresolved"),
        },
        row_currentness={lane.rows[0].coordinate: GoalFrontierCurrentness.CURRENT},
        current_revision_by_goal=CURRENT_REVISIONS,
    ).structural_frontier[0]
    assert row.dependency_gate.state is GoalFrontierDependencyGateState.UNRESOLVED
    assert row.dependency_gate.pending_keys == ("pending-input",)
    assert row.dependency_gate.unresolved_keys == ("unresolved-input",)


def test_cross_goal_advance_stales_old_satisfaction_with_unchanged_dependent() -> None:
    dependency = _dependency("agent", "a2", "product-baseline")
    lane = GoalFrontierLaneDefinition(
        "agent",
        (_row("agent", "a2", 1),),
        GoalFrontierProjectionHealth.CLEAN,
    )
    row = project_goal_frontier(
        goal_tag=GOAL,
        source_revision_ref=REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        lanes=(lane,),
        dependencies=(dependency,),
        observations={
            dependency.dependency_key: _intake(dependency, satisfaction="satisfied")
        },
        row_currentness={lane.rows[0].coordinate: GoalFrontierCurrentness.CURRENT},
        current_revision_by_goal={
            GOAL: REVISION,
            "goal/external": "git:external-advanced",
        },
    ).structural_frontier[0]
    assert row.dependency_gate.state is GoalFrontierDependencyGateState.STALE
    assert row.dependency_gate.stale_keys == ("product-baseline",)
    assert row.admission_eligibility is GoalFrontierAdmissionEligibility.INELIGIBLE
    assert row.suggested_action == "none"
