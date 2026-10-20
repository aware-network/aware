from dataclasses import replace

import pytest
from aware_goal_operational_runtime.dependencies import (
    GoalDependency,
    GoalDependencyRelation,
    GoalRowCoordinate,
)
from aware_goal_operational_runtime.dependency_evaluation import (
    GoalDependencyEvidence,
    GoalDependencyEvidenceKind,
    GoalDependencyGateState,
    GoalDependencySatisfaction,
    GoalRowResolutionOutcome,
    GoalRowSourceObservation,
    dependency_definition_digest,
    evaluate_goal_dependency,
    summarize_goal_dependency_gate,
)

EVALUATOR_REF = "goal-dependency-evaluator:v0"


def declaration(
    relation: GoalDependencyRelation = GoalDependencyRelation.REQUIRES_COMPLETION,
    *,
    dependency_key: str = "delivery-needs-review",
    prerequisite_row_key: str = "accept",
) -> GoalDependency:
    return GoalDependency(
        owner_goal_tag="goal/actorworld",
        dependency_key=dependency_key,
        dependent_lane_key="delivery",
        dependent_row_key="ship",
        prerequisite_goal_tag="goal/review",
        prerequisite_lane_key="acceptance",
        prerequisite_row_key=prerequisite_row_key,
        relation=relation,
        reason="The prerequisite gate requires explicit evidence.",
    )


def resolved_sources(
    dependency: GoalDependency,
) -> tuple[GoalRowSourceObservation, GoalRowSourceObservation]:
    return (
        GoalRowSourceObservation(
            dependency.dependent,
            GoalRowResolutionOutcome.RESOLVED,
            source_revision_ref="goal-revision:dependent-7",
        ),
        GoalRowSourceObservation(
            dependency.prerequisite,
            GoalRowResolutionOutcome.RESOLVED,
            source_revision_ref="goal-revision:prerequisite-4",
            gate_digest="sha256:gate-current",
        ),
    )


def admitted_evidence(
    dependency: GoalDependency,
    *,
    kind: GoalDependencyEvidenceKind,
) -> GoalDependencyEvidence:
    return GoalDependencyEvidence(
        owner_goal_tag=dependency.owner_goal_tag,
        dependency_key=dependency.dependency_key,
        dependency_digest=dependency_definition_digest(dependency),
        prerequisite=dependency.prerequisite,
        dependent_source_revision_ref="goal-revision:dependent-7",
        prerequisite_source_revision_ref="goal-revision:prerequisite-4",
        prerequisite_gate_digest="sha256:gate-current",
        kind=kind,
        evidence_ref=f"goal-gate-evidence:{kind.value}",
        qualification_ref="evidence-qualification:accepted",
    )


def evaluate(
    dependency: GoalDependency,
    *evidence: GoalDependencyEvidence,
):
    dependent, prerequisite = resolved_sources(dependency)
    return evaluate_goal_dependency(
        dependency,
        dependent=dependent,
        prerequisite=prerequisite,
        evidence=tuple(evidence),
        evaluator_ref=EVALUATOR_REF,
    )


def test_exact_completion_evidence_is_deterministically_satisfied() -> None:
    dependency = declaration()
    evidence = admitted_evidence(
        dependency,
        kind=GoalDependencyEvidenceKind.COMPLETION,
    )

    first = evaluate(dependency, evidence)
    second = evaluate(dependency, evidence)

    assert first == second
    assert first.satisfaction is GoalDependencySatisfaction.SATISFIED
    assert first.dependency_digest == dependency_definition_digest(dependency)
    assert first.evidence_refs == ("goal-gate-evidence:completion",)
    assert first.qualification_refs == ("evidence-qualification:accepted",)
    assert first.reasons == ()
    assert first.observation_ref.startswith("goal-dependency-observation:sha256:")
    wire = first.to_wire()
    assert wire["effect_profile"] == "read_only_non_authorizing"
    assert "dispatch" not in wire
    assert "authorized" not in wire


def test_acceptance_requires_acceptance_not_completion_evidence() -> None:
    dependency = declaration(GoalDependencyRelation.REQUIRES_ACCEPTANCE)
    completion = admitted_evidence(
        dependency,
        kind=GoalDependencyEvidenceKind.COMPLETION,
    )

    pending = evaluate(dependency, completion)
    accepted = evaluate(
        dependency,
        admitted_evidence(
            dependency,
            kind=GoalDependencyEvidenceKind.ACCEPTANCE,
        ),
    )

    assert pending.satisfaction is GoalDependencySatisfaction.PENDING
    assert pending.reasons == ("acceptance_evidence_missing",)
    assert pending.evidence_refs == ()
    assert accepted.satisfaction is GoalDependencySatisfaction.SATISFIED


@pytest.mark.parametrize(
    ("change", "reason"),
    (
        ("definition", "dependency_definition_changed"),
        ("dependent", "dependent_source_revision_changed"),
        ("prerequisite", "prerequisite_source_revision_changed"),
        ("gate", "prerequisite_gate_changed"),
    ),
)
def test_changed_definition_or_source_binding_makes_evidence_stale(
    change: str,
    reason: str,
) -> None:
    dependency = declaration()
    evidence = admitted_evidence(
        dependency,
        kind=GoalDependencyEvidenceKind.COMPLETION,
    )
    evaluated_dependency = dependency
    if change == "definition":
        evaluated_dependency = replace(
            dependency,
            reason="Independent review now requires a stronger gate.",
        )
    dependent, prerequisite = resolved_sources(evaluated_dependency)
    if change == "dependent":
        dependent = replace(
            dependent,
            source_revision_ref="goal-revision:dependent-8",
        )
    elif change == "prerequisite":
        prerequisite = replace(
            prerequisite,
            source_revision_ref="goal-revision:prerequisite-5",
        )
    elif change == "gate":
        prerequisite = replace(prerequisite, gate_digest="sha256:gate-revised")

    observation = evaluate_goal_dependency(
        evaluated_dependency,
        dependent=dependent,
        prerequisite=prerequisite,
        evidence=(evidence,),
        evaluator_ref=EVALUATOR_REF,
    )

    assert observation.satisfaction is GoalDependencySatisfaction.STALE
    assert reason in observation.reasons


def test_unresolved_and_ambiguous_endpoints_never_consume_evidence() -> None:
    dependency = declaration()
    dependent, _ = resolved_sources(dependency)
    evidence = admitted_evidence(
        dependency,
        kind=GoalDependencyEvidenceKind.COMPLETION,
    )
    unresolved = GoalRowSourceObservation(
        dependency.prerequisite,
        GoalRowResolutionOutcome.UNRESOLVED,
    )
    ambiguous = GoalRowSourceObservation(
        dependency.prerequisite,
        GoalRowResolutionOutcome.AMBIGUOUS,
        candidate_refs=("goal-row:first", "goal-row:second"),
    )

    missing = evaluate_goal_dependency(
        dependency,
        dependent=dependent,
        prerequisite=unresolved,
        evidence=(evidence,),
        evaluator_ref=EVALUATOR_REF,
    )
    multiple = evaluate_goal_dependency(
        dependency,
        dependent=dependent,
        prerequisite=ambiguous,
        evidence=(evidence,),
        evaluator_ref=EVALUATOR_REF,
    )

    assert missing.satisfaction is GoalDependencySatisfaction.UNRESOLVED
    assert missing.reasons == ("prerequisite_unresolved",)
    assert missing.evidence_refs == ()
    assert multiple.satisfaction is GoalDependencySatisfaction.UNRESOLVED
    assert multiple.reasons == ("prerequisite_ambiguous",)


def test_dependency_gate_is_conjunctive_and_non_authorizing() -> None:
    first = declaration()
    second = declaration(
        dependency_key="delivery-needs-security",
        prerequisite_row_key="security",
    )
    satisfied = evaluate(
        first,
        admitted_evidence(first, kind=GoalDependencyEvidenceKind.COMPLETION),
    )
    pending = evaluate(second)

    blocked = summarize_goal_dependency_gate(
        first.dependent,
        (pending, satisfied),
        evaluator_ref=EVALUATOR_REF,
    )
    empty = summarize_goal_dependency_gate(
        first.dependent,
        (),
        evaluator_ref=EVALUATOR_REF,
    )

    assert blocked.state is GoalDependencyGateState.BLOCKED
    assert blocked.blocking_dependency_keys == ("delivery-needs-security",)
    assert blocked.reasons == ("delivery-needs-security:pending",)
    assert blocked.effect_profile == "read_only_non_authorizing"
    assert empty.state is GoalDependencyGateState.CLEAR
    assert empty.reasons == ("no_declared_dependencies",)


def test_dependency_gate_rejects_duplicate_or_foreign_observations() -> None:
    dependency = declaration()
    observation = evaluate(dependency)

    with pytest.raises(ValueError, match="duplicate"):
        summarize_goal_dependency_gate(
            dependency.dependent,
            (observation, observation),
            evaluator_ref=EVALUATOR_REF,
        )
    with pytest.raises(ValueError, match="another dependent"):
        summarize_goal_dependency_gate(
            GoalRowCoordinate("goal/other", "delivery", "ship"),
            (observation,),
            evaluator_ref=EVALUATOR_REF,
        )
