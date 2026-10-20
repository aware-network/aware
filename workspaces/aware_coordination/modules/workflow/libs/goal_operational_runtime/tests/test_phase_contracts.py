from dataclasses import replace

import pytest
from aware_goal_operational_runtime import (
    GoalDependencyRelation,
    GoalLaneIssueSnapshot,
    GoalLanePhase,
    GoalLanePhaseGate,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseContractError,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
    validate_goal_phase_dependencies,
)

GOAL = "goal/2026-09-12/shared"
OTHER_GOAL = "goal/2026-09-10/actorworld"


def gate(*, promise: str = "Portable contract accepted") -> GoalLanePhaseGate:
    return GoalLanePhaseGate(
        gate_key="portable-contract-accepted",
        promise=promise,
        gate_contract_ref="contract:goal-phase-gate:v1",
        evidence_schema_ref="schema:goal-phase-evidence:v1",
        invariant_refs=("invariant:issue-closure-independent",),
    )


def coordinate(phase_key: str = "m1-portable-contract") -> GoalPhaseCoordinate:
    return GoalPhaseCoordinate(GOAL, "operational-runtime", phase_key)


def observation(
    phase_gate: GoalLanePhaseGate,
    outcome: GoalLanePhaseGateOutcome = GoalLanePhaseGateOutcome.SATISFIED,
) -> GoalLanePhaseGateObservation:
    return GoalLanePhaseGateObservation(
        observation_ref="observation:phase-gate:1",
        gate_digest=phase_gate.gate_digest,
        outcome=outcome,
        evaluator_ref="evaluator:independent-review",
        evidence_refs=("commit:abc123",),
        source_revision_refs=("repository:main@abc123",),
        evaluated_at="2026-09-19T16:00:00Z",
        currentness_ref="currentness:repository-head:abc123",
    )


def phase(
    *,
    phase_key: str = "m1-portable-contract",
    state: GoalLanePhaseState = GoalLanePhaseState.ACTIVE,
    phase_gate: GoalLanePhaseGate | None = None,
    observations: tuple[GoalLanePhaseGateObservation, ...] = (),
    last_receipt_ref: str | None = None,
) -> GoalLanePhase:
    return GoalLanePhase(
        coordinate=coordinate(phase_key),
        title="Portable Phase/Gate contract",
        ordinal=2,
        intent="Add the neutral contract without migrating v1 consumers.",
        state=state,
        gate=phase_gate or gate(),
        gate_observations=observations,
        pursuit_directive="Implement only the bounded M1 contract.",
        last_receipt_ref=last_receipt_ref,
    )


def dependency(
    dependent: GoalPhaseCoordinate,
    prerequisite: GoalPhaseCoordinate,
    required_gate_digest: str,
    *,
    key: str = "m1-requires-m0",
) -> GoalPhaseDependency:
    return GoalPhaseDependency(
        owner_goal_tag=dependent.goal_tag,
        dependency_key=key,
        dependent=dependent,
        prerequisite=prerequisite,
        required_gate_digest=required_gate_digest,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        reason="M1 requires the accepted design gate.",
    )


def test_gate_digest_covers_semantics_but_not_phase_ordinal() -> None:
    first = gate()
    assert first.gate_digest == gate().gate_digest
    assert first.gate_digest != gate(promise="Different promise").gate_digest
    assert (
        phase(phase_gate=first).gate.gate_digest
        == replace(phase(phase_gate=first), ordinal=99).gate.gate_digest
    )


def test_not_evaluated_is_absence_and_acceptance_requires_evidence() -> None:
    phase_gate = gate()
    with pytest.raises(GoalPhaseContractError, match="represented by absence"):
        observation(phase_gate, GoalLanePhaseGateOutcome.NOT_EVALUATED)
    with pytest.raises(GoalPhaseContractError, match="accepted Phase"):
        phase(state=GoalLanePhaseState.ACCEPTED, phase_gate=phase_gate)
    accepted = phase(
        state=GoalLanePhaseState.ACCEPTED,
        phase_gate=phase_gate,
        observations=(observation(phase_gate),),
        last_receipt_ref="goal-phase-acceptance:sha256:" + "a" * 64,
    )
    assert accepted.state is GoalLanePhaseState.ACCEPTED
    with pytest.raises(GoalPhaseContractError, match="publication receipt"):
        phase(
            state=GoalLanePhaseState.ACCEPTED,
            phase_gate=phase_gate,
            observations=(observation(phase_gate),),
        )
    with pytest.raises(GoalPhaseContractError, match="goal-phase-acceptance"):
        phase(
            state=GoalLanePhaseState.ACCEPTED,
            phase_gate=phase_gate,
            observations=(observation(phase_gate),),
            last_receipt_ref="issue-close:sha256:" + "a" * 64,
        )


def test_phase_rejects_conflicting_non_stale_gate_observations() -> None:
    phase_gate = gate()
    satisfied = observation(phase_gate)
    rejected = replace(
        satisfied,
        observation_ref="observation:phase-gate:2",
        outcome=GoalLanePhaseGateOutcome.REJECTED,
    )
    with pytest.raises(GoalPhaseContractError, match="at most one non-stale"):
        phase(phase_gate=phase_gate, observations=(satisfied, rejected))


def test_changed_gate_only_accepts_old_observation_as_stale() -> None:
    previous = gate()
    current = gate(promise="Corrected promise")
    retained = observation(previous)
    with pytest.raises(GoalPhaseContractError, match="current gate digest"):
        phase(phase_gate=current, observations=(retained,))
    stale = replace(retained, outcome=GoalLanePhaseGateOutcome.STALE)
    assert phase(phase_gate=current, observations=(stale,)).gate_observations == (
        stale,
    )


def test_one_phase_accumulates_independent_issue_associations() -> None:
    implementation = GoalLanePhaseWork(
        association_ref="phase-work:implementation:1",
        issue_ref="docs/issues/implementation.md",
        role=GoalLanePhaseWorkRole.IMPLEMENTATION,
        disposition=GoalLanePhaseWorkDisposition.RETIRED,
        admitted_at="2026-09-19T10:00:00Z",
        retired_at="2026-09-19T11:00:00Z",
        receipt_ref="receipt:phase-work:1",
    )
    review = GoalLanePhaseWork(
        association_ref="phase-work:review:1",
        issue_ref="docs/issues/review.md",
        role=GoalLanePhaseWorkRole.REVIEW,
        disposition=GoalLanePhaseWorkDisposition.CURRENT,
        admitted_at="2026-09-19T11:05:00Z",
        receipt_ref="receipt:phase-work:2",
    )
    value = replace(phase(), work_associations=(implementation, review))
    assert value.coordinate.phase_key == "m1-portable-contract"
    assert len(value.work_associations) == 2
    with pytest.raises(GoalPhaseContractError, match="current work"):
        replace(review, retired_at="2026-09-19T12:00:00Z")
    with pytest.raises(GoalPhaseContractError, match="cannot precede"):
        replace(implementation, retired_at="2026-09-19T09:59:59Z")


@pytest.mark.parametrize(
    ("field", "value"),
    (("lane", " operational-runtime"), ("title", "M1 "), ("promise", " gate")),
)
def test_portable_text_rejects_normalizing_whitespace(field: str, value: str) -> None:
    with pytest.raises(GoalPhaseContractError, match="canonical"):
        if field == "lane":
            GoalPhaseCoordinate(GOAL, value, "m1")
        elif field == "title":
            replace(phase(), title=value)
        else:
            gate(promise=value)


def test_work_timestamps_require_real_canonical_utc_dates() -> None:
    with pytest.raises(GoalPhaseContractError, match="real UTC calendar date"):
        GoalLanePhaseWork(
            association_ref="phase-work:invalid-date",
            issue_ref="docs/issues/invalid.md",
            role=GoalLanePhaseWorkRole.CORRECTION,
            disposition=GoalLanePhaseWorkDisposition.CURRENT,
            admitted_at="2026-02-31T00:00:00Z",
            receipt_ref="receipt:invalid-date",
        )


def test_rejected_observation_requires_evidence() -> None:
    phase_gate = gate()
    with pytest.raises(GoalPhaseContractError, match="rejected.*evidence"):
        replace(
            observation(phase_gate, GoalLanePhaseGateOutcome.REJECTED),
            evidence_refs=(),
        )


def test_dependencies_are_gate_bound_cycle_checked_and_cross_goal_portable() -> None:
    prerequisite_phase = phase(phase_key="m0-design")
    dependent_phase = phase()
    edge = dependency(
        dependent_phase.coordinate,
        prerequisite_phase.coordinate,
        prerequisite_phase.gate.gate_digest,
    )
    GoalPhaseContractBundleV1(
        phases=(prerequisite_phase, dependent_phase), dependencies=(edge,)
    )
    external = GoalPhaseCoordinate(OTHER_GOAL, "representation-runtime", "r2")
    cross_goal = dependency(
        dependent_phase.coordinate,
        external,
        "sha256:" + "a" * 64,
        key="m1-requires-external-r2",
    )
    GoalPhaseContractBundleV1(phases=(dependent_phase,), dependencies=(cross_goal,))
    GoalPhaseContractBundleV1(phases=(), dependencies=(cross_goal,))
    reverse = dependency(
        prerequisite_phase.coordinate,
        dependent_phase.coordinate,
        dependent_phase.gate.gate_digest,
        key="m0-requires-m1",
    )
    with pytest.raises(GoalPhaseContractError, match="cycle"):
        validate_goal_phase_dependencies((edge, reverse))
    with pytest.raises(GoalPhaseContractError, match="digest is stale"):
        GoalPhaseContractBundleV1(
            phases=(prerequisite_phase, dependent_phase),
            dependencies=(replace(edge, required_gate_digest="sha256:" + "b" * 64),),
        )


def test_dependency_identity_preserves_existing_portable_goal_key_domain() -> None:
    prerequisite_phase = phase(phase_key="m0-design")
    dependent_phase = phase()
    legacy_identity = "baseline4_delivery_run_requires_a3"
    edge = dependency(
        dependent_phase.coordinate,
        prerequisite_phase.coordinate,
        prerequisite_phase.gate.gate_digest,
        key=legacy_identity,
    )
    assert edge.dependency_key == legacy_identity
    with pytest.raises(GoalPhaseContractError, match="portable token"):
        replace(edge, dependency_key="invalid dependency key")
    with pytest.raises(GoalPhaseContractError, match="portable token"):
        replace(edge, dependency_key="invalid|dependency")


def test_v1_goal_lane_issue_contract_remains_exported() -> None:
    assert GoalLaneIssueSnapshot.__name__ == "GoalLaneIssueSnapshot"
