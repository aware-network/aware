from copy import deepcopy
from dataclasses import replace

import pytest
from aware_goal_operational_runtime.dependencies import (
    GoalDependency,
    GoalDependencyRelation,
)
from aware_goal_operational_runtime.dependency_evaluation import (
    GoalDependencyEvidence,
    GoalDependencyEvidenceKind,
    GoalDependencySatisfaction,
    GoalRowResolutionOutcome,
    GoalRowSourceObservation,
    dependency_definition_digest,
    evaluate_goal_dependency,
    summarize_goal_dependency_gate,
)
from aware_goal_operational_runtime.dependency_observation_intake import (
    GoalDependencyObservationAvailability,
    compose_goal_dependency_observation_intake,
    decode_goal_dependency_gate_observation,
    decode_goal_dependency_observation,
    decode_goal_dependency_observation_intake,
)

EVALUATOR_REF = "goal-dependency-evaluator:v0"


def declaration(
    *,
    dependency_key: str = "delivery-needs-review",
    prerequisite_row_key: str = "accept",
    reason: str = "The review gate must be completed.",
) -> GoalDependency:
    return GoalDependency(
        owner_goal_tag="goal/actorworld",
        dependency_key=dependency_key,
        dependent_lane_key="delivery",
        dependent_row_key="ship",
        prerequisite_goal_tag="goal/review",
        prerequisite_lane_key="acceptance",
        prerequisite_row_key=prerequisite_row_key,
        relation=GoalDependencyRelation.REQUIRES_COMPLETION,
        reason=reason,
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


def completion_evidence(dependency: GoalDependency) -> GoalDependencyEvidence:
    return GoalDependencyEvidence(
        owner_goal_tag=dependency.owner_goal_tag,
        dependency_key=dependency.dependency_key,
        dependency_digest=dependency_definition_digest(dependency),
        prerequisite=dependency.prerequisite,
        dependent_source_revision_ref="goal-revision:dependent-7",
        prerequisite_source_revision_ref="goal-revision:prerequisite-4",
        prerequisite_gate_digest="sha256:gate-current",
        kind=GoalDependencyEvidenceKind.COMPLETION,
        evidence_ref="goal-gate-evidence:completion",
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


def observations_by_state():
    current = declaration()
    satisfied = evaluate(current, completion_evidence(current))
    pending = evaluate(current)
    revised = replace(current, reason="The accepted review gate must be completed.")
    stale = evaluate(revised, completion_evidence(current))
    dependent, _ = resolved_sources(current)
    unresolved = evaluate_goal_dependency(
        current,
        dependent=dependent,
        prerequisite=GoalRowSourceObservation(
            current.prerequisite,
            GoalRowResolutionOutcome.UNRESOLVED,
        ),
        evaluator_ref=EVALUATOR_REF,
    )
    return (
        (current, pending),
        (current, satisfied),
        (revised, stale),
        (current, unresolved),
    )


@pytest.mark.parametrize("dependency,observation", observations_by_state())
def test_all_evaluated_states_round_trip_without_reconstruction(
    dependency: GoalDependency,
    observation,
) -> None:
    decoded = decode_goal_dependency_observation(
        observation.to_wire(),
        dependency=dependency,
    )

    assert decoded == observation
    assert decoded.to_wire() == observation.to_wire()


def test_absence_is_not_evaluated_and_is_distinct_from_pending() -> None:
    dependency = declaration()
    absent = compose_goal_dependency_observation_intake(dependency)
    pending = compose_goal_dependency_observation_intake(
        dependency,
        evaluate(dependency),
    )

    assert absent.availability is GoalDependencyObservationAvailability.NOT_EVALUATED
    assert absent.observation is None
    assert absent.to_wire()["observation"] is None
    assert pending.availability is GoalDependencyObservationAvailability.EVALUATED
    assert pending.observation is not None
    assert pending.observation.satisfaction is GoalDependencySatisfaction.PENDING
    assert (
        decode_goal_dependency_observation_intake(
            absent.to_wire(), dependency=dependency
        )
        == absent
    )
    assert (
        decode_goal_dependency_observation_intake(
            pending.to_wire(), dependency=dependency
        )
        == pending
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("effect_profile", "dispatch_authorizing", "effect_profile"),
        ("dependency_digest", "sha256:different", "dependency_digest"),
        ("owner_goal_tag", "goal/other", "owner_goal_tag"),
        (
            "observation_ref",
            "goal-dependency-observation:sha256:other",
            "observation_ref",
        ),
        ("satisfaction", "unknown", "unknown"),
    ),
)
def test_observation_intake_rejects_authority_drift_or_reconstruction(
    field: str,
    value: str,
    message: str,
) -> None:
    dependency = declaration()
    payload = evaluate(dependency).to_wire()
    payload[field] = value

    with pytest.raises((TypeError, ValueError), match=message):
        decode_goal_dependency_observation(payload, dependency=dependency)


def test_observation_intake_rejects_unknown_fields_and_non_list_evidence() -> None:
    dependency = declaration()
    unknown = evaluate(dependency).to_wire()
    unknown["document_presence"] = "present"
    malformed = evaluate(dependency).to_wire()
    malformed["evidence_refs"] = ()

    with pytest.raises(ValueError, match="unknown=.*document_presence"):
        decode_goal_dependency_observation(unknown, dependency=dependency)
    with pytest.raises(TypeError, match="evidence_refs must be a list"):
        decode_goal_dependency_observation(malformed, dependency=dependency)


def test_intake_availability_and_observation_must_agree() -> None:
    dependency = declaration()
    absent = compose_goal_dependency_observation_intake(dependency).to_wire()
    absent["availability"] = "evaluated"
    present = compose_goal_dependency_observation_intake(
        dependency,
        evaluate(dependency),
    ).to_wire()
    present["availability"] = "not_evaluated"

    with pytest.raises(ValueError, match="evaluated intake requires"):
        decode_goal_dependency_observation_intake(absent, dependency=dependency)
    with pytest.raises(ValueError, match="not_evaluated intake cannot"):
        decode_goal_dependency_observation_intake(present, dependency=dependency)


def test_gate_intake_requires_exact_canonical_summary() -> None:
    first = declaration()
    second = declaration(
        dependency_key="delivery-needs-security",
        prerequisite_row_key="security",
    )
    satisfied = evaluate(first, completion_evidence(first))
    pending = evaluate(second)
    observations = (pending, satisfied)
    gate = summarize_goal_dependency_gate(
        first.dependent,
        observations,
        evaluator_ref=EVALUATOR_REF,
    )

    assert (
        decode_goal_dependency_gate_observation(
            gate.to_wire(), observations=observations
        )
        == gate
    )

    tampered = deepcopy(gate.to_wire())
    tampered["state"] = "clear"
    with pytest.raises(ValueError, match="canonical observation summary"):
        decode_goal_dependency_gate_observation(
            tampered,
            observations=observations,
        )


def test_gate_intake_rejects_a_different_observation_set() -> None:
    dependency = declaration()
    pending = evaluate(dependency)
    gate = summarize_goal_dependency_gate(
        dependency.dependent,
        (pending,),
        evaluator_ref=EVALUATOR_REF,
    )

    with pytest.raises(ValueError, match="canonical observation summary"):
        decode_goal_dependency_gate_observation(gate.to_wire(), observations=())
