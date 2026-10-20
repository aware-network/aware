import json

from aware_goal_operational_runtime import (
    GoalDependencyEvidence,
    GoalDependencyEvidenceKind,
    GoalDependencyObservationAvailability,
    GoalDependencySatisfaction,
    GoalRowResolutionOutcome,
    GoalRowSourceObservation,
    compose_goal_dependency_observation_intake,
    decode_goal_dependency_gate_observation,
    decode_goal_dependency_observation_intake,
    dependency_definition_digest,
    evaluate_goal_dependency,
    summarize_goal_dependency_gate,
)
from aware_goal_service_view_compat.dependency_projection import project_goal_dependencies

EVALUATOR_REF = "goal-dependency-evaluator:integration-v0"
SOURCE = """# Goal: Example
- Tag: goal/example
- Status: Active

## Lane Sequences
### delivery
| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ship | [!] | Blocked | Wait for review | TBD:ship | Unassigned | Pending |
"""
DECLARATION = {
    "dependency_key": "shipping-review",
    "dependent_lane_key": "delivery",
    "dependent_row_key": "ship",
    "prerequisite_goal_tag": "goal/external",
    "prerequisite_lane_key": "review",
    "prerequisite_row_key": "accept",
    "relation": "requires_acceptance",
    "reason": "Independent review acceptance is required",
}


def document() -> str:
    return (
        SOURCE
        + "\n## Dependencies\n\n```json\n"
        + json.dumps([DECLARATION])
        + "\n```\n"
    )


def sources(dependency, *, resolved: bool = True):
    dependent = GoalRowSourceObservation(
        dependency.dependent,
        GoalRowResolutionOutcome.RESOLVED,
        source_revision_ref="goal-revision:dependent-7",
    )
    prerequisite = (
        GoalRowSourceObservation(
            dependency.prerequisite,
            GoalRowResolutionOutcome.RESOLVED,
            source_revision_ref="goal-revision:prerequisite-4",
            gate_digest="sha256:gate-current",
        )
        if resolved
        else GoalRowSourceObservation(
            dependency.prerequisite,
            GoalRowResolutionOutcome.UNRESOLVED,
        )
    )
    return dependent, prerequisite


def acceptance_evidence(dependency, *, gate_digest: str = "sha256:gate-current"):
    return GoalDependencyEvidence(
        owner_goal_tag=dependency.owner_goal_tag,
        dependency_key=dependency.dependency_key,
        dependency_digest=dependency_definition_digest(dependency),
        prerequisite=dependency.prerequisite,
        dependent_source_revision_ref="goal-revision:dependent-7",
        prerequisite_source_revision_ref="goal-revision:prerequisite-4",
        prerequisite_gate_digest=gate_digest,
        kind=GoalDependencyEvidenceKind.ACCEPTANCE,
        evidence_ref="goal-gate-evidence:acceptance",
        qualification_ref="evidence-qualification:accepted",
    )


def evaluate(dependency, *, evidence=(), resolved: bool = True):
    dependent, prerequisite = sources(dependency, resolved=resolved)
    return evaluate_goal_dependency(
        dependency,
        dependent=dependent,
        prerequisite=prerequisite,
        evidence=evidence,
        evaluator_ref=EVALUATOR_REF,
    )


def test_installed_projection_and_operational_intake_preserve_all_cases():
    projection = project_goal_dependencies(document())
    projected = projection.to_json()["dependencies"][0]
    dependency = projection.dependencies[0]

    # Document presence is intentionally narrower than operational resolution.
    assert projected["dependent_resolution"] == "present"
    assert projected["prerequisite_resolution"] == "external_unresolved"
    assert projected["satisfaction"] == "unknown"

    unevaluated = compose_goal_dependency_observation_intake(dependency)
    assert (
        unevaluated.availability is GoalDependencyObservationAvailability.NOT_EVALUATED
    )
    assert unevaluated.observation is None

    observations = {
        GoalDependencySatisfaction.PENDING: evaluate(dependency),
        GoalDependencySatisfaction.SATISFIED: evaluate(
            dependency,
            evidence=(acceptance_evidence(dependency),),
        ),
        GoalDependencySatisfaction.STALE: evaluate(
            dependency,
            evidence=(acceptance_evidence(dependency, gate_digest="sha256:gate-old"),),
        ),
        GoalDependencySatisfaction.UNRESOLVED: evaluate(
            dependency,
            resolved=False,
        ),
    }

    assert set(observations) == set(GoalDependencySatisfaction)
    for expected, observation in observations.items():
        assert observation.satisfaction is expected
        intake = compose_goal_dependency_observation_intake(dependency, observation)
        assert (
            decode_goal_dependency_observation_intake(
                intake.to_wire(),
                dependency=dependency,
            )
            == intake
        )

        gate = summarize_goal_dependency_gate(
            dependency.dependent,
            (observation,),
            evaluator_ref=EVALUATOR_REF,
        )
        assert (
            decode_goal_dependency_gate_observation(
                gate.to_wire(),
                observations=(observation,),
            )
            == gate
        )


def test_projection_unknown_cannot_enter_the_operational_observation_slot():
    projection = project_goal_dependencies(document())
    dependency = projection.dependencies[0]
    projection_item = projection.to_json()["dependencies"][0]

    assert projection_item["satisfaction"] == "unknown"
    assert (
        compose_goal_dependency_observation_intake(dependency).to_wire()["observation"]
        is None
    )
