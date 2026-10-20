from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import cast

import pytest
from aware_goal_operational_runtime import (
    GoalDependencyRelation,
    GoalFrontierCurrentness,
    GoalLanePhase,
    GoalLanePhaseGate,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
    GoalPhaseFrontierDependencyGateState,
    GoalPhaseFrontierEligibility,
    decode_goal_phase_dependency_observation,
    decode_goal_phase_frontier_projection,
    observe_goal_phase_dependency,
    observe_unresolved_goal_phase_dependency,
    project_goal_phase_frontier,
)

GOAL = "goal/test-phase-frontier"
GOAL_REVISION = "git:goal-current"


def _gate(key: str) -> GoalLanePhaseGate:
    return GoalLanePhaseGate(
        gate_key=f"{key}-gate",
        promise=f"Accept {key} evidence.",
        gate_contract_ref="contract:test-v1",
        evidence_schema_ref="evidence:test-v1",
    )


def _phase(
    *,
    goal: str,
    lane: str,
    key: str,
    ordinal: int,
    state: GoalLanePhaseState = GoalLanePhaseState.ACTIVE,
    outcome: GoalLanePhaseGateOutcome | None = None,
    source_revision: str | None = None,
) -> GoalLanePhase:
    gate = _gate(key)
    observation = ()
    if outcome is not None:
        evidence = (
            (f"evidence:{key}",)
            if outcome
            in (
                GoalLanePhaseGateOutcome.SATISFIED,
                GoalLanePhaseGateOutcome.REJECTED,
            )
            else ()
        )
        observation = (
            GoalLanePhaseGateObservation(
                observation_ref=f"gate-observation:{key}:{outcome.value}",
                gate_digest=gate.gate_digest,
                outcome=outcome,
                evaluator_ref="evaluator:test",
                evidence_refs=evidence,
                source_revision_refs=(source_revision or f"git:{key}",),
                evaluated_at="2026-09-19T17:00:00Z",
                currentness_ref=f"currentness:{key}",
            ),
        )
    return GoalLanePhase(
        coordinate=GoalPhaseCoordinate(goal, lane, key),
        title=key,
        ordinal=ordinal,
        intent=f"Deliver {key}.",
        state=state,
        gate=gate,
        gate_observations=observation,
        last_receipt_ref=(
            "goal-phase-acceptance:sha256:" + "a" * 64
            if state is GoalLanePhaseState.ACCEPTED
            else None
        ),
    )


def _dependency(
    target: GoalLanePhase,
    prerequisite: GoalLanePhase,
    *,
    key: str,
    relation: GoalDependencyRelation = GoalDependencyRelation.REQUIRES_COMPLETION,
) -> GoalPhaseDependency:
    return GoalPhaseDependency(
        owner_goal_tag=target.coordinate.goal_tag,
        dependency_key=key,
        dependent=target.coordinate,
        prerequisite=prerequisite.coordinate,
        required_gate_digest=prerequisite.gate.gate_digest,
        relation=relation,
        reason=f"{key} is explicitly required.",
    )


def _currentness(*phases: GoalLanePhase):
    return {
        phase.coordinate: GoalFrontierCurrentness.CURRENT for phase in phases
    }


def test_all_six_dependency_states_remain_distinct() -> None:
    target = _phase(goal=GOAL, lane="runtime", key="target", ordinal=1)
    outcomes = {
        "satisfied": GoalLanePhaseGateOutcome.SATISFIED,
        "pending": GoalLanePhaseGateOutcome.PENDING,
        "stale": GoalLanePhaseGateOutcome.STALE,
        "rejected": GoalLanePhaseGateOutcome.REJECTED,
    }
    prerequisites = {
        key: _phase(
            goal=f"goal/external-{key}",
            lane="source",
            key=key,
            ordinal=1,
            outcome=outcome,
        )
        for key, outcome in outcomes.items()
    }
    unresolved = _phase(
        goal="goal/external-unresolved",
        lane="source",
        key="unresolved",
        ordinal=1,
    )
    not_evaluated = _phase(
        goal="goal/external-not-evaluated",
        lane="source",
        key="not-evaluated",
        ordinal=1,
    )
    all_prerequisites = {**prerequisites, "unresolved": unresolved, "not-evaluated": not_evaluated}
    dependencies = tuple(
        _dependency(target, prerequisite, key=f"requires-{key}")
        for key, prerequisite in sorted(all_prerequisites.items())
    )
    by_key = {dependency.dependency_key: dependency for dependency in dependencies}
    observations = {
        f"requires-{key}": observe_goal_phase_dependency(
            by_key[f"requires-{key}"],
            dependent_source_revision_ref=GOAL_REVISION,
            prerequisite_source_revision_ref=f"git:{key}",
            prerequisite_phase=prerequisite,
            evaluator_ref="evaluator:test",
            currentness_ref="currentness:test",
        )
        for key, prerequisite in prerequisites.items()
    }
    observations["requires-unresolved"] = observe_unresolved_goal_phase_dependency(
        by_key["requires-unresolved"],
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:test",
    )
    revisions = {GOAL: GOAL_REVISION}
    revisions.update(
        {
            prerequisite.coordinate.goal_tag: f"git:{key}"
            for key, prerequisite in all_prerequisites.items()
        }
    )
    result = project_goal_phase_frontier(
        goal_tag=GOAL,
        source_revision_ref=GOAL_REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        bundle=GoalPhaseContractBundleV1((target,), dependencies),
        observations=observations,
        phase_currentness=_currentness(target),
        current_revision_by_goal=revisions,
    ).lanes[0].phases[0]
    assert result.dependency_gate.state is GoalPhaseFrontierDependencyGateState.REJECTED
    assert result.dependency_gate.satisfied_keys == ("requires-satisfied",)
    assert result.dependency_gate.pending_keys == ("requires-pending",)
    assert result.dependency_gate.stale_keys == ("requires-stale",)
    assert result.dependency_gate.unresolved_keys == ("requires-unresolved",)
    assert result.dependency_gate.rejected_keys == ("requires-rejected",)
    assert result.dependency_gate.not_evaluated_keys == ("requires-not-evaluated",)
    assert result.admission_eligibility is GoalPhaseFrontierEligibility.INELIGIBLE


def test_ordinal_does_not_create_predecessor_authority() -> None:
    first = _phase(goal=GOAL, lane="product", key="first", ordinal=1)
    second = _phase(goal=GOAL, lane="product", key="second", ordinal=2)
    prerequisite = _phase(
        goal="goal/external",
        lane="source",
        key="input",
        ordinal=1,
        outcome=GoalLanePhaseGateOutcome.PENDING,
    )
    dependency = _dependency(first, prerequisite, key="first-requires-input")
    observation = observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=GOAL_REVISION,
        prerequisite_source_revision_ref="git:input",
        prerequisite_phase=prerequisite,
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:test",
    )
    lane = project_goal_phase_frontier(
        goal_tag=GOAL,
        source_revision_ref=GOAL_REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        bundle=GoalPhaseContractBundleV1((first, second), (dependency,)),
        observations={dependency.dependency_key: observation},
        phase_currentness=_currentness(first, second),
        current_revision_by_goal={
            GOAL: GOAL_REVISION,
            "goal/external": "git:input",
        },
    ).lanes[0]
    assert lane.phases[0].admission_eligibility is GoalPhaseFrontierEligibility.INELIGIBLE
    assert lane.phases[1].admission_eligibility is GoalPhaseFrontierEligibility.ELIGIBLE
    assert lane.default_candidate is lane.phases[1]
    assert lane.phases[1].suggested_action == "open_issue"


def test_requires_acceptance_needs_phase_acceptance_receipt() -> None:
    target = _phase(goal=GOAL, lane="api", key="view", ordinal=1)
    active = _phase(
        goal="goal/external",
        lane="delivery",
        key="product",
        ordinal=1,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
    )
    dependency = _dependency(
        target,
        active,
        key="view-requires-product-acceptance",
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
    )
    pending = observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=GOAL_REVISION,
        prerequisite_source_revision_ref="git:product",
        prerequisite_phase=active,
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:test",
    )
    assert pending.outcome is GoalLanePhaseGateOutcome.PENDING

    accepted = replace(
        active,
        state=GoalLanePhaseState.ACCEPTED,
        last_receipt_ref="goal-phase-acceptance:sha256:" + "b" * 64,
    )
    satisfied = observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=GOAL_REVISION,
        prerequisite_source_revision_ref="git:product",
        prerequisite_phase=accepted,
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:test",
    )
    assert satisfied.outcome is GoalLanePhaseGateOutcome.SATISFIED
    assert satisfied.prerequisite_acceptance_receipt_ref == accepted.last_receipt_ref


def test_cross_goal_advance_stales_retained_satisfaction() -> None:
    target = _phase(goal=GOAL, lane="api", key="view", ordinal=1)
    prerequisite = _phase(
        goal="goal/external",
        lane="delivery",
        key="product",
        ordinal=1,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
        source_revision="git:external-old",
    )
    dependency = _dependency(target, prerequisite, key="view-requires-product")
    observation = observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=GOAL_REVISION,
        prerequisite_source_revision_ref="git:external-old",
        prerequisite_phase=prerequisite,
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:old",
    )
    result = project_goal_phase_frontier(
        goal_tag=GOAL,
        source_revision_ref=GOAL_REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        bundle=GoalPhaseContractBundleV1((target,), (dependency,)),
        observations={dependency.dependency_key: observation},
        phase_currentness=_currentness(target),
        current_revision_by_goal={
            GOAL: GOAL_REVISION,
            "goal/external": "git:external-new",
        },
    ).lanes[0].phases[0]
    assert result.dependency_gate.state is GoalPhaseFrontierDependencyGateState.STALE
    assert result.dependency_gate.stale_keys == (dependency.dependency_key,)
    assert result.admission_eligibility is GoalPhaseFrontierEligibility.INELIGIBLE


def test_terminal_phase_state_and_event_silence_are_explicit() -> None:
    accepted = _phase(
        goal=GOAL,
        lane="runtime",
        key="accepted",
        ordinal=1,
        state=GoalLanePhaseState.ACCEPTED,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
    )
    withdrawn = _phase(
        goal=GOAL,
        lane="runtime",
        key="withdrawn",
        ordinal=2,
        state=GoalLanePhaseState.WITHDRAWN,
    )
    projection = project_goal_phase_frontier(
        goal_tag=GOAL,
        source_revision_ref=GOAL_REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        bundle=GoalPhaseContractBundleV1((accepted, withdrawn), ()),
        phase_currentness=_currentness(accepted, withdrawn),
        current_revision_by_goal={GOAL: GOAL_REVISION},
    )
    assert projection.lanes[0].phases[0].admission_eligibility is GoalPhaseFrontierEligibility.ACCEPTED
    assert projection.lanes[0].phases[1].admission_eligibility is GoalPhaseFrontierEligibility.WITHDRAWN
    assert projection.to_wire()["event_effect"] == "none"
    assert projection.to_wire()["ordinal_semantics"] == "presentation_only"


def test_observation_cannot_be_replayed_for_another_declaration() -> None:
    target = _phase(goal=GOAL, lane="runtime", key="target", ordinal=1)
    prerequisite = _phase(
        goal="goal/external",
        lane="source",
        key="input",
        ordinal=1,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
    )
    dependency = _dependency(target, prerequisite, key="target-requires-input")
    observation = observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=GOAL_REVISION,
        prerequisite_source_revision_ref="git:input",
        prerequisite_phase=prerequisite,
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:test",
    )
    forged = replace(observation, required_gate_digest="sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="differs from exact Phase dependency"):
        _ = project_goal_phase_frontier(
            goal_tag=GOAL,
            source_revision_ref=GOAL_REVISION,
            whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
            bundle=GoalPhaseContractBundleV1((target,), (dependency,)),
            observations={dependency.dependency_key: forged},
            phase_currentness=_currentness(target),
            current_revision_by_goal={
                GOAL: GOAL_REVISION,
                "goal/external": "git:input",
            },
        )


def test_direct_observation_rejects_withdrawn_satisfaction() -> None:
    target = _phase(goal=GOAL, lane="runtime", key="target", ordinal=1)
    prerequisite = _phase(
        goal="goal/external",
        lane="source",
        key="input",
        ordinal=1,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
    )
    dependency = _dependency(target, prerequisite, key="target-requires-input")
    observation = observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=GOAL_REVISION,
        prerequisite_source_revision_ref="git:input",
        prerequisite_phase=prerequisite,
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:test",
    )
    with pytest.raises(ValueError, match="withdrawn prerequisite"):
        _ = replace(
            observation,
            prerequisite_phase_state=GoalLanePhaseState.WITHDRAWN,
        )


def test_direct_observation_qualifies_acceptance_receipt_exactly() -> None:
    target = _phase(goal=GOAL, lane="runtime", key="target", ordinal=1)
    prerequisite = _phase(
        goal="goal/external",
        lane="source",
        key="input",
        ordinal=1,
        state=GoalLanePhaseState.ACCEPTED,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
    )
    dependency = _dependency(
        target,
        prerequisite,
        key="target-requires-input",
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
    )
    observation = observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=GOAL_REVISION,
        prerequisite_source_revision_ref="git:input",
        prerequisite_phase=prerequisite,
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:test",
    )
    with pytest.raises(ValueError, match="not qualified"):
        _ = replace(
            observation,
            prerequisite_acceptance_receipt_ref="not-an-acceptance-receipt",
        )
    with pytest.raises(ValueError, match="requires acceptance receipt"):
        _ = replace(observation, prerequisite_acceptance_receipt_ref=None)
    with pytest.raises(ValueError, match="non-accepted prerequisite"):
        _ = replace(
            observation,
            prerequisite_phase_state=GoalLanePhaseState.ACTIVE,
        )


def test_observation_decoder_round_trips_and_rejects_tampering() -> None:
    target = _phase(goal=GOAL, lane="runtime", key="target", ordinal=1)
    prerequisite = _phase(
        goal="goal/external",
        lane="source",
        key="input",
        ordinal=1,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
    )
    dependency = _dependency(target, prerequisite, key="target-requires-input")
    observation = observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=GOAL_REVISION,
        prerequisite_source_revision_ref="git:input",
        prerequisite_phase=prerequisite,
        evaluator_ref="evaluator:test",
        currentness_ref="currentness:test",
    )
    wire = observation.to_wire()
    assert (
        decode_goal_phase_dependency_observation(wire, dependency=dependency)
        == observation
    )
    unknown = {**wire, "unknown": True}
    with pytest.raises(ValueError, match="fields differ"):
        _ = decode_goal_phase_dependency_observation(
            unknown, dependency=dependency
        )
    changed_ref = {**wire, "observation_ref": "forged:observation"}
    with pytest.raises(ValueError, match="canonical observation"):
        _ = decode_goal_phase_dependency_observation(
            changed_ref, dependency=dependency
        )
    changed_effect = {**wire, "effect_profile": "authorizing"}
    with pytest.raises(ValueError, match="effect profile"):
        _ = decode_goal_phase_dependency_observation(
            changed_effect, dependency=dependency
        )


def test_frontier_decoder_requires_canonical_derived_projection() -> None:
    phase = _phase(goal=GOAL, lane="runtime", key="target", ordinal=1)
    bundle = GoalPhaseContractBundleV1((phase,), ())
    currentness = _currentness(phase)
    revisions = {GOAL: GOAL_REVISION}
    projection = project_goal_phase_frontier(
        goal_tag=GOAL,
        source_revision_ref=GOAL_REVISION,
        whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
        bundle=bundle,
        phase_currentness=currentness,
        current_revision_by_goal=revisions,
    )
    wire = projection.to_wire()
    assert (
        decode_goal_phase_frontier_projection(
            wire,
            goal_tag=GOAL,
            source_revision_ref=GOAL_REVISION,
            whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
            bundle=bundle,
            phase_currentness=currentness,
            current_revision_by_goal=revisions,
        )
        == projection
    )
    altered = deepcopy(wire)
    lanes = cast(list[dict[str, object]], altered["lanes"])
    phases = cast(list[dict[str, object]], lanes[0]["phases"])
    phases[0]["admission_eligibility"] = "ineligible"
    with pytest.raises(ValueError, match="canonical projection"):
        _ = decode_goal_phase_frontier_projection(
            altered,
            goal_tag=GOAL,
            source_revision_ref=GOAL_REVISION,
            whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
            bundle=bundle,
            phase_currentness=currentness,
            current_revision_by_goal=revisions,
        )
    ordinal_bool = deepcopy(wire)
    ordinal_lanes = cast(list[dict[str, object]], ordinal_bool["lanes"])
    ordinal_phases = cast(list[dict[str, object]], ordinal_lanes[0]["phases"])
    ordinal_phases[0]["ordinal"] = True
    with pytest.raises(ValueError, match="canonical projection"):
        _ = decode_goal_phase_frontier_projection(
            ordinal_bool,
            goal_tag=GOAL,
            source_revision_ref=GOAL_REVISION,
            whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
            bundle=bundle,
            phase_currentness=currentness,
            current_revision_by_goal=revisions,
        )
    incoming_count_bool = deepcopy(wire)
    count_lanes = cast(list[dict[str, object]], incoming_count_bool["lanes"])
    count_phases = cast(list[dict[str, object]], count_lanes[0]["phases"])
    dependency_gate = cast(dict[str, object], count_phases[0]["dependency_gate"])
    dependency_gate["incoming_count"] = False
    with pytest.raises(ValueError, match="canonical projection"):
        _ = decode_goal_phase_frontier_projection(
            incoming_count_bool,
            goal_tag=GOAL,
            source_revision_ref=GOAL_REVISION,
            whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
            bundle=bundle,
            phase_currentness=currentness,
            current_revision_by_goal=revisions,
        )
    changed_effect = {**wire, "effect_profile": "authorizing"}
    with pytest.raises(ValueError, match="canonical projection"):
        _ = decode_goal_phase_frontier_projection(
            changed_effect,
            goal_tag=GOAL,
            source_revision_ref=GOAL_REVISION,
            whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
            bundle=bundle,
            phase_currentness=currentness,
            current_revision_by_goal=revisions,
        )
    unknown = {**wire, "unknown": True}
    with pytest.raises(ValueError, match="fields differ"):
        _ = decode_goal_phase_frontier_projection(
            unknown,
            goal_tag=GOAL,
            source_revision_ref=GOAL_REVISION,
            whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
            bundle=bundle,
            phase_currentness=currentness,
            current_revision_by_goal=revisions,
        )
