from __future__ import annotations

import json
from dataclasses import replace
from typing import cast

import pytest
from aware_goal_operational_runtime import (
    GoalLanePhase,
    GoalLanePhaseGate,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalLanePhaseTemporalBoundaryV1,
    GoalLanePhaseTemporalGapV1,
    GoalLanePhaseTemporalLedgerV1,
    GoalLanePhaseTemporalOriginV1,
    GoalLanePhaseTransitionOccurrenceV1,
    GoalLanePhaseTransitionSupersessionV1,
    GoalPhaseCoordinate,
    GoalPhaseHistoryCoverage,
    GoalPhaseTemporalCurrentness,
    GoalPhaseTemporalError,
    GoalPhaseTemporalObservationAuthorityKind,
    GoalPhaseTemporalObservationAuthorityV1,
    GoalPhaseTemporalPublicationPlanV1,
    GoalPhaseTemporalPublicationProfile,
    GoalPhaseTemporalPublicationReceiptV1,
    GoalPhaseTemporalPublicationState,
    GoalPhaseTransitionFactAvailability,
    GoalPhaseTransitionSelectorKind,
    GoalPhaseTransitionSelectorV1,
    decode_goal_phase_temporal_ledger,
    decode_goal_phase_temporal_observation,
    decode_goal_phase_temporal_observation_authority,
    decode_goal_phase_temporal_publication_receipt,
    derive_goal_phase_temporal_currentness_receipt_ref,
    derive_goal_phase_temporal_publication_binding,
    derive_goal_phase_temporal_snapshot_receipt_ref,
    encode_goal_phase_temporal_ledger,
    encode_goal_phase_temporal_observation,
    encode_goal_phase_temporal_observation_authority,
    encode_goal_phase_temporal_publication_receipt,
    goal_phase_temporal_phase_binding_digest,
    observe_goal_phase_temporal_facts,
)

_COMMIT = "a" * 40
_COMMIT_RECEIPT = f"repository-commit:{_COMMIT}"


def _phase(state: GoalLanePhaseState) -> GoalLanePhase:
    return GoalLanePhase(
        coordinate=GoalPhaseCoordinate(
            "goal/2026-09-20/temporal-v0", "runtime", "o7"
        ),
        title="Temporal occurrence authority",
        ordinal=7,
        intent="Preserve qualified lifecycle occurrence facts.",
        state=state,
        gate=GoalLanePhaseGate(
            gate_key="temporal-authority",
            promise="Temporal evidence remains explicit.",
            gate_contract_ref="contract:o7",
            evidence_schema_ref="evidence:o7",
        ),
        pursuit_directive="Implement only neutral temporal authority.",
    )


def _origin(phase: GoalLanePhase) -> GoalLanePhaseTemporalOriginV1:
    return GoalLanePhaseTemporalOriginV1(
        coordinate=phase.coordinate,
        initial_state=phase.state,
        phase_admission_receipt_ref="phase-admission:test",
        admitted_at="2026-09-20T01:00:00Z",
        phase_binding_digest=goal_phase_temporal_phase_binding_digest(phase),
        repository_revision_ref="git:origin",
    )


def _boundary(phase: GoalLanePhase, revision: int) -> GoalLanePhaseTemporalBoundaryV1:
    return GoalLanePhaseTemporalBoundaryV1(
        phase_binding_digest=goal_phase_temporal_phase_binding_digest(phase),
        ledger_revision=revision,
        publication_binding_ref=(
            "goal-phase-temporal-publication-binding:sha256:"
            + f"{revision:064x}"
        ),
    )


def _occurrence(
    phase: GoalLanePhase,
    *,
    ordinal: int = 0,
    predecessor: str | None = None,
    from_state: GoalLanePhaseState = GoalLanePhaseState.PLANNED,
    to_state: GoalLanePhaseState = GoalLanePhaseState.ACTIVE,
    effective_at: str = "2026-09-20T02:00:00Z",
    recorded_at: str = "2026-09-20T02:01:00Z",
) -> GoalLanePhaseTransitionOccurrenceV1:
    return GoalLanePhaseTransitionOccurrenceV1(
        coordinate=phase.coordinate,
        slot_ordinal=ordinal,
        predecessor_slot_ref=predecessor,
        from_state=from_state,
        to_state=to_state,
        effective_at=effective_at,
        recorded_at=recorded_at,
        authority_refs=("transition-authority:test",),
        source_refs=("source:test",),
        evidence_refs=("evidence:test",),
    )


def _ledger(
    phase: GoalLanePhase,
    origin: GoalLanePhaseTemporalOriginV1,
    occurrences: tuple[GoalLanePhaseTransitionOccurrenceV1, ...],
    *,
    coverage: GoalPhaseHistoryCoverage = GoalPhaseHistoryCoverage.COMPLETE,
    gaps: tuple[GoalLanePhaseTemporalGapV1, ...] = (),
    revision: int = 1,
    supersessions: tuple[GoalLanePhaseTransitionSupersessionV1, ...] = (),
) -> GoalLanePhaseTemporalLedgerV1:
    return GoalLanePhaseTemporalLedgerV1(
        coordinate=phase.coordinate,
        current_phase_binding_digest=goal_phase_temporal_phase_binding_digest(phase),
        origin=origin,
        occurrences=occurrences,
        supersessions=supersessions,
        history_coverage=coverage,
        coverage_through=_boundary(phase, revision),
        gaps=gaps,
        evidence_refs=("ledger-evidence:test",),
    )


def _authority(
    phase: GoalLanePhase,
    ledger: GoalLanePhaseTemporalLedgerV1,
    *,
    currentness: GoalPhaseTemporalCurrentness = GoalPhaseTemporalCurrentness.UNKNOWN,
    publication_receipt: GoalPhaseTemporalPublicationReceiptV1 | None = None,
) -> GoalPhaseTemporalObservationAuthorityV1:
    authority_kind = GoalPhaseTemporalObservationAuthorityKind.ADMITTED_O7
    phase_binding_digest = goal_phase_temporal_phase_binding_digest(phase)
    coverage_binding = ledger.coverage_through.publication_binding_ref
    source_revision_ref = (
        "b" * 40
        if publication_receipt is None
        else publication_receipt.repository_commit_ref
    )
    snapshot_at = "2026-09-20T04:00:00Z"
    admission_receipt = (
        "goal-temporal-observation-authority-admission:sha256:" + "3" * 64
    )
    snapshot_receipt = derive_goal_phase_temporal_snapshot_receipt_ref(
        authority_kind=authority_kind,
        coordinate=phase.coordinate,
        ledger_digest=ledger.ledger_digest,
        phase_binding_digest=phase_binding_digest,
        coverage_publication_binding_ref=coverage_binding,
        source_revision_ref=source_revision_ref,
        snapshot_at=snapshot_at,
        authority_admission_receipt_ref=admission_receipt,
    )
    currentness_receipt = derive_goal_phase_temporal_currentness_receipt_ref(
        authority_kind=authority_kind,
        coordinate=phase.coordinate,
        ledger_digest=ledger.ledger_digest,
        phase_binding_digest=phase_binding_digest,
        coverage_publication_binding_ref=coverage_binding,
        source_revision_ref=source_revision_ref,
        snapshot_receipt_ref=snapshot_receipt,
        currentness=currentness,
        authority_admission_receipt_ref=admission_receipt,
    )
    return GoalPhaseTemporalObservationAuthorityV1(
        authority_kind=authority_kind,
        coordinate=phase.coordinate,
        ledger_digest=ledger.ledger_digest,
        phase_binding_digest=phase_binding_digest,
        coverage_publication_binding_ref=coverage_binding,
        source_revision_ref=source_revision_ref,
        snapshot_at=snapshot_at,
        snapshot_receipt_ref=snapshot_receipt,
        currentness=currentness,
        currentness_receipt_ref=currentness_receipt,
        authority_admission_receipt_ref=admission_receipt,
        publication_receipt_ref=(
            None if publication_receipt is None else publication_receipt.receipt_ref
        ),
    )


def _transition_plan() -> tuple[
    GoalPhaseTemporalPublicationPlanV1,
    GoalLanePhaseTransitionOccurrenceV1,
]:
    planned = _phase(GoalLanePhaseState.PLANNED)
    active = _phase(GoalLanePhaseState.ACTIVE)
    origin = _origin(planned)
    before = _ledger(planned, origin, (), revision=1)
    occurrence = _occurrence(planned)
    binding = derive_goal_phase_temporal_publication_binding(
        coordinate=active.coordinate,
        publication_profile=GoalPhaseTemporalPublicationProfile.NORMAL_TRANSITION,
        phase_binding_digest=goal_phase_temporal_phase_binding_digest(active),
        prior_ledger_digest=before.ledger_digest,
        ledger_revision=2,
        appended_occurrence_refs=(occurrence.occurrence_ref,),
        appended_supersession_refs=(),
        phase_path="state/phase.json",
        ledger_path="state/phase-temporal.json",
    )
    after = GoalLanePhaseTemporalLedgerV1(
        coordinate=active.coordinate,
        current_phase_binding_digest=goal_phase_temporal_phase_binding_digest(active),
        origin=origin,
        occurrences=(occurrence,),
        supersessions=(),
        history_coverage=GoalPhaseHistoryCoverage.COMPLETE,
        coverage_through=GoalLanePhaseTemporalBoundaryV1(
            phase_binding_digest=goal_phase_temporal_phase_binding_digest(active),
            ledger_revision=2,
            publication_binding_ref=binding,
        ),
        gaps=(),
        evidence_refs=("ledger-evidence:test",),
    )
    return (
        GoalPhaseTemporalPublicationPlanV1(
            publication_profile=GoalPhaseTemporalPublicationProfile.NORMAL_TRANSITION,
            before_phase=planned,
            after_phase=active,
            before_ledger=before,
            after_ledger=after,
            appended_occurrence_refs=(occurrence.occurrence_ref,),
            appended_supersession_refs=(),
            publication_binding_ref=binding,
            expected_repository_revision_ref="git:before",
            phase_path="state/phase.json",
            ledger_path="state/phase-temporal.json",
            evidence_refs=("transition-authority:test",),
        ),
        occurrence,
    )


def _correction_plan() -> GoalPhaseTemporalPublicationPlanV1:
    transition, occurrence = _transition_plan()
    replacement = replace(
        occurrence,
        effective_at="2026-09-20T01:59:00Z",
        recorded_at="2026-09-20T03:00:00Z",
        source_refs=("source:corrected",),
        evidence_refs=("evidence:corrected",),
    )
    supersession = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=occurrence.occurrence_ref,
        replacement=replacement,
        reason="correct-effective-time",
        admitted_at="2026-09-20T03:01:00Z",
        authority_refs=("correction-authority:test",),
    )
    binding = derive_goal_phase_temporal_publication_binding(
        coordinate=transition.after_phase.coordinate,
        publication_profile=GoalPhaseTemporalPublicationProfile.CORRECTION,
        phase_binding_digest=goal_phase_temporal_phase_binding_digest(
            transition.after_phase
        ),
        prior_ledger_digest=transition.after_ledger.ledger_digest,
        ledger_revision=3,
        appended_occurrence_refs=(replacement.occurrence_ref,),
        appended_supersession_refs=(supersession.supersession_ref,),
        phase_path=transition.phase_path,
        ledger_path=transition.ledger_path,
    )
    corrected_ledger = replace(
        transition.after_ledger,
        supersessions=(supersession,),
        coverage_through=GoalLanePhaseTemporalBoundaryV1(
            phase_binding_digest=goal_phase_temporal_phase_binding_digest(
                transition.after_phase
            ),
            ledger_revision=3,
            publication_binding_ref=binding,
        ),
    )
    return GoalPhaseTemporalPublicationPlanV1(
        publication_profile=GoalPhaseTemporalPublicationProfile.CORRECTION,
        before_phase=transition.after_phase,
        after_phase=transition.after_phase,
        before_ledger=transition.after_ledger,
        after_ledger=corrected_ledger,
        appended_occurrence_refs=(replacement.occurrence_ref,),
        appended_supersession_refs=(supersession.supersession_ref,),
        publication_binding_ref=binding,
        expected_repository_revision_ref="git:transition",
        phase_path=transition.phase_path,
        ledger_path=transition.ledger_path,
        evidence_refs=("correction-authority:test",),
    )


def test_occurrence_has_stable_slot_and_content_revision() -> None:
    phase = _phase(GoalLanePhaseState.PLANNED)
    first = _occurrence(phase)
    corrected = _occurrence(
        phase,
        effective_at="2026-09-20T01:59:00Z",
        recorded_at="2026-09-20T03:00:00Z",
    )
    assert first.transition_slot_ref == corrected.transition_slot_ref
    assert first.occurrence_ref != corrected.occurrence_ref
    with pytest.raises(GoalPhaseTemporalError, match="post-publication"):
        _ = replace(
            first,
            authority_refs=(
                "goal-phase-temporal-publication:sha256:" + "1" * 64,
            ),
        )


def test_acceptance_requires_exact_prepublication_acceptance_receipt() -> None:
    phase = _phase(GoalLanePhaseState.ACTIVE)
    with pytest.raises(GoalPhaseTemporalError, match="acceptance receipt"):
        _ = _occurrence(
            phase,
            from_state=GoalLanePhaseState.ACTIVE,
            to_state=GoalLanePhaseState.ACCEPTED,
        )
    accepted = replace(
        _occurrence(
            phase,
            from_state=GoalLanePhaseState.ACTIVE,
            to_state=GoalLanePhaseState.HELD,
        ),
        to_state=GoalLanePhaseState.ACCEPTED,
        authority_refs=("goal-phase-acceptance:sha256:" + "2" * 64,),
    )
    assert accepted.to_state is GoalLanePhaseState.ACCEPTED


def test_complete_ledger_requires_origin_and_unbroken_chain() -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    active = _phase(GoalLanePhaseState.ACTIVE)
    origin = _origin(planned)
    first = _occurrence(planned)
    ledger = _ledger(active, origin, (first,))
    assert ledger.history_coverage is GoalPhaseHistoryCoverage.COMPLETE
    with pytest.raises(GoalPhaseTemporalError, match="contiguous"):
        _ = _ledger(active, origin, (replace(first, slot_ordinal=2),))
    with pytest.raises(GoalPhaseTemporalError, match="gap"):
        _ = _ledger(
            active,
            origin,
            (first,),
            gaps=(GoalLanePhaseTemporalGapV1(0, 0, "gap:test"),),
        )


def test_supersession_preserves_slot_and_rejects_state_change() -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    active = _phase(GoalLanePhaseState.ACTIVE)
    origin = _origin(planned)
    first = _occurrence(planned)
    corrected = _occurrence(
        planned,
        effective_at="2026-09-20T01:59:00Z",
        recorded_at="2026-09-20T03:00:00Z",
    )
    supersession = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=first.occurrence_ref,
        replacement=corrected,
        reason="effective-time-correction",
        admitted_at="2026-09-20T03:01:00Z",
        authority_refs=("correction:test",),
    )
    ledger = _ledger(active, origin, (first,), supersessions=(supersession,))
    assert ledger.supersessions == (supersession,)
    with pytest.raises(GoalPhaseTemporalError, match="cannot claim"):
        _ = _ledger(
            active,
            origin,
            (first,),
            supersessions=(
                replace(
                    supersession,
                    downstream_revalidation_refs=("not-a-replacement",),
                ),
            ),
        )
    with pytest.raises(GoalPhaseTemporalError, match="unsupported in O7 V1"):
        _ = _ledger(
            _phase(GoalLanePhaseState.WITHDRAWN),
            origin,
            (first,),
            supersessions=(
                GoalLanePhaseTransitionSupersessionV1(
                    superseded_occurrence_ref=first.occurrence_ref,
                    replacement=replace(
                        corrected, to_state=GoalLanePhaseState.WITHDRAWN
                    ),
                    reason="state-correction",
                    admitted_at="2026-09-20T03:01:00Z",
                    authority_refs=("correction:test",),
                ),
            ),
        )


def test_partial_history_does_not_forge_first_or_latest() -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    active = _phase(GoalLanePhaseState.ACTIVE)
    first = _occurrence(
        planned,
        ordinal=1,
        predecessor="goal-phase-transition-slot:sha256:" + "9" * 64,
    )
    ledger = _ledger(
        active,
        _origin(planned),
        (first,),
        coverage=GoalPhaseHistoryCoverage.PARTIAL,
        gaps=(
            GoalLanePhaseTemporalGapV1(0, 0, "unresolved-prefix"),
            GoalLanePhaseTemporalGapV1(2, 2, "unresolved-suffix"),
        ),
    )
    observation = observe_goal_phase_temporal_facts(
        phase=active,
        ledger=ledger,
        selectors=(
            GoalPhaseTransitionSelectorV1(
                GoalPhaseTransitionSelectorKind.BY_SLOT,
                transition_slot_ref=first.transition_slot_ref,
            ),
            GoalPhaseTransitionSelectorV1(
                GoalPhaseTransitionSelectorKind.FIRST_ENTRY,
                target_state=GoalLanePhaseState.ACTIVE,
            ),
            GoalPhaseTransitionSelectorV1(
                GoalPhaseTransitionSelectorKind.LATEST_ENTRY,
                target_state=GoalLanePhaseState.ACTIVE,
            ),
        ),
        authority=_authority(active, ledger),
    )
    assert [fact.availability for fact in observation.facts] == [
        GoalPhaseTransitionFactAvailability.PRESENT,
        GoalPhaseTransitionFactAvailability.UNAVAILABLE,
        GoalPhaseTransitionFactAvailability.UNAVAILABLE,
    ]


def test_complete_history_can_prove_not_occurred() -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    active = _phase(GoalLanePhaseState.ACTIVE)
    ledger = _ledger(active, _origin(planned), (_occurrence(planned),))
    observation = observe_goal_phase_temporal_facts(
        phase=active,
        ledger=ledger,
        selectors=(
            GoalPhaseTransitionSelectorV1(
                GoalPhaseTransitionSelectorKind.FIRST_ENTRY,
                target_state=GoalLanePhaseState.HELD,
            ),
        ),
        authority=_authority(active, ledger),
    )
    assert observation.facts[0].availability is GoalPhaseTransitionFactAvailability.NOT_OCCURRED


def test_strict_ledger_and_observation_codecs_reject_type_and_digest_tamper() -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    active = _phase(GoalLanePhaseState.ACTIVE)
    occurrence = _occurrence(planned)
    ledger = _ledger(active, _origin(planned), (occurrence,))
    assert decode_goal_phase_temporal_ledger(
        encode_goal_phase_temporal_ledger(ledger), phase=active
    ) == ledger
    with pytest.raises(GoalPhaseTemporalError, match="detached"):
        _ = decode_goal_phase_temporal_ledger(
            encode_goal_phase_temporal_ledger(ledger), phase=planned
        )
    raw = ledger.to_wire()
    cast(dict[str, object], raw["coverage_through"])["ledger_revision"] = True
    with pytest.raises(GoalPhaseTemporalError):
        _ = decode_goal_phase_temporal_ledger(
            json.dumps(raw).encode(), phase=active
        )

    observation = observe_goal_phase_temporal_facts(
        phase=active,
        ledger=ledger,
        selectors=(GoalPhaseTransitionSelectorV1(GoalPhaseTransitionSelectorKind.BY_SLOT, transition_slot_ref=occurrence.transition_slot_ref),),
        authority=_authority(active, ledger),
    )
    assert decode_goal_phase_temporal_observation(
        encode_goal_phase_temporal_observation(observation),
        phase=active,
        ledger=ledger,
        authority=_authority(active, ledger),
    ) == observation
    raw_observation = observation.to_wire()
    raw_observation["gap_count"] = False
    with pytest.raises(GoalPhaseTemporalError):
        _ = decode_goal_phase_temporal_observation(
            json.dumps(raw_observation).encode(),
            phase=active,
            ledger=ledger,
            authority=_authority(active, ledger),
        )


def test_compound_publication_binds_phase_and_ledger_postimages() -> None:
    plan, _ = _transition_plan()
    receipt = GoalPhaseTemporalPublicationReceiptV1(
        plan=plan,
        repository_commit_receipt_ref=_COMMIT_RECEIPT,
        repository_commit_ref=_COMMIT,
        publication_state=GoalPhaseTemporalPublicationState.REPOSITORY_PUBLISHED,
        reconciliation_reason_codes=(),
    )
    assert receipt.to_wire()["changed_paths"] == [
        "state/phase-temporal.json",
        "state/phase.json",
    ]
    with pytest.raises(GoalPhaseTemporalError, match="transition Phase state"):
        _ = replace(
            plan,
            after_phase=plan.before_phase,
            after_ledger=plan.before_ledger,
            appended_occurrence_refs=(),
        )


def test_reconciliation_failure_retains_publication_receipt() -> None:
    plan, _ = _transition_plan()
    receipt = GoalPhaseTemporalPublicationReceiptV1(
        plan=plan,
        repository_commit_receipt_ref=_COMMIT_RECEIPT,
        repository_commit_ref=_COMMIT,
        publication_state=GoalPhaseTemporalPublicationState.RECONCILIATION_REQUIRED,
        reconciliation_reason_codes=("worktree_projection_advanced",),
    )
    assert receipt.repository_commit_receipt_ref == _COMMIT_RECEIPT
    with pytest.raises(GoalPhaseTemporalError, match="typed reason"):
        _ = replace(receipt, reconciliation_reason_codes=())


def test_terminal_acceptance_is_exact_under_partial_history() -> None:
    active = _phase(GoalLanePhaseState.ACTIVE)
    observation = GoalLanePhaseGateObservation(
        observation_ref="gate-observation:o7",
        gate_digest=active.gate.gate_digest,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
        evaluator_ref="evaluator:o7",
        evidence_refs=("gate-evidence:o7",),
        source_revision_refs=("git:gate",),
        evaluated_at="2026-09-20T02:00:00Z",
        currentness_ref="currentness:gate",
    )
    active = replace(active, gate_observations=(observation,))
    acceptance_ref = "goal-phase-acceptance:sha256:" + "a" * 64
    accepted = replace(
        active,
        state=GoalLanePhaseState.ACCEPTED,
        last_receipt_ref=acceptance_ref,
    )
    origin = _origin(active)
    occurrence = GoalLanePhaseTransitionOccurrenceV1(
        coordinate=active.coordinate,
        slot_ordinal=2,
        predecessor_slot_ref="goal-phase-transition-slot:sha256:" + "b" * 64,
        from_state=GoalLanePhaseState.ACTIVE,
        to_state=GoalLanePhaseState.ACCEPTED,
        effective_at="2026-09-20T03:00:00Z",
        recorded_at="2026-09-20T03:01:00Z",
        authority_refs=(acceptance_ref,),
        source_refs=("source:acceptance",),
        evidence_refs=("evidence:acceptance",),
    )
    ledger = _ledger(
        accepted,
        origin,
        (occurrence,),
        coverage=GoalPhaseHistoryCoverage.PARTIAL,
        gaps=(GoalLanePhaseTemporalGapV1(0, 1, "unknown-prefix"),),
    )
    result = observe_goal_phase_temporal_facts(
        phase=accepted,
        ledger=ledger,
        selectors=(
            GoalPhaseTransitionSelectorV1(
                GoalPhaseTransitionSelectorKind.TERMINAL_ACCEPTANCE
            ),
        ),
        authority=_authority(accepted, ledger),
    )
    assert result.facts[0].availability is GoalPhaseTransitionFactAvailability.PRESENT


@pytest.mark.parametrize(
    ("coverage", "availability"),
    (
        (
            GoalPhaseHistoryCoverage.UNAVAILABLE,
            GoalPhaseTransitionFactAvailability.UNAVAILABLE,
        ),
        (
            GoalPhaseHistoryCoverage.UNSUPPORTED,
            GoalPhaseTransitionFactAvailability.UNSUPPORTED,
        ),
    ),
)
def test_nonrepresentable_history_preserves_independent_availability(
    coverage: GoalPhaseHistoryCoverage,
    availability: GoalPhaseTransitionFactAvailability,
) -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    ledger = _ledger(planned, _origin(planned), (), coverage=coverage)
    result = observe_goal_phase_temporal_facts(
        phase=planned,
        ledger=ledger,
        selectors=(
            GoalPhaseTransitionSelectorV1(
                GoalPhaseTransitionSelectorKind.FIRST_ENTRY,
                target_state=GoalLanePhaseState.ACTIVE,
            ),
        ),
        authority=_authority(planned, ledger),
    )
    assert result.facts[0].availability is availability


def test_bound_observation_decoder_rejects_rederived_fact_tamper() -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    active = _phase(GoalLanePhaseState.ACTIVE)
    occurrence = _occurrence(planned)
    ledger = _ledger(active, _origin(planned), (occurrence,))
    observation = observe_goal_phase_temporal_facts(
        phase=active,
        ledger=ledger,
        selectors=(
            GoalPhaseTransitionSelectorV1(
                GoalPhaseTransitionSelectorKind.BY_SLOT,
                transition_slot_ref=occurrence.transition_slot_ref,
            ),
        ),
        authority=_authority(active, ledger),
    )
    raw = observation.to_wire()
    fact = cast(dict[str, object], cast(list[object], raw["facts"])[0])
    fact["proof_refs"] = [ledger.ledger_digest]
    body = {key: value for key, value in raw.items() if key != "observation_ref"}
    from aware_goal_operational_runtime.identity import fingerprint

    raw["observation_ref"] = "goal-phase-temporal-observation:" + fingerprint(body)
    with pytest.raises(GoalPhaseTemporalError, match="derived"):
        _ = decode_goal_phase_temporal_observation(
            json.dumps(raw).encode(),
            phase=active,
            ledger=ledger,
            authority=_authority(active, ledger),
        )


def test_temporal_public_values_reject_empty_evidence_and_schema_forgery() -> None:
    phase = _phase(GoalLanePhaseState.PLANNED)
    with pytest.raises(GoalPhaseTemporalError, match="must not be empty"):
        _ = replace(_occurrence(phase), evidence_refs=())
    ledger = _ledger(
        _phase(GoalLanePhaseState.ACTIVE),
        _origin(phase),
        (_occurrence(phase),),
    )
    with pytest.raises(GoalPhaseTemporalError, match="unsupported temporal ledger"):
        _ = replace(ledger, schema_id="aware.goal.phase-temporal-ledger.v999")


def test_supersession_only_correction_preserves_final_phase() -> None:
    plan = _correction_plan()
    assert plan.publication_profile is GoalPhaseTemporalPublicationProfile.CORRECTION
    assert plan.before_phase == plan.after_phase
    assert plan.after_ledger.supersessions[-1].replacement.occurrence_ref in (
        plan.appended_occurrence_refs
    )
    assert plan.after_ledger.supersessions[-1].supersession_ref in (
        plan.appended_supersession_refs
    )
    receipt = GoalPhaseTemporalPublicationReceiptV1(
        plan=plan,
        repository_commit_receipt_ref=_COMMIT_RECEIPT,
        repository_commit_ref=_COMMIT,
        publication_state=GoalPhaseTemporalPublicationState.REPOSITORY_PUBLISHED,
        reconciliation_reason_codes=(),
    )
    assert receipt.to_wire()["changed_paths"] == [plan.ledger_path]


def test_supersession_cycles_and_reused_revisions_fail_closed() -> None:
    transition, original = _transition_plan()
    replacement_b = replace(
        original,
        effective_at="2026-09-20T01:59:00Z",
        recorded_at="2026-09-20T03:00:00Z",
    )
    edge_ab = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=original.occurrence_ref,
        replacement=replacement_b,
        reason="a-to-b",
        admitted_at="2026-09-20T03:01:00Z",
        authority_refs=("correction:a-b",),
    )
    with pytest.raises(GoalPhaseTemporalError, match="replacement must differ"):
        _ = GoalLanePhaseTransitionSupersessionV1(
            superseded_occurrence_ref=original.occurrence_ref,
            replacement=original,
            reason="self-cycle",
            admitted_at="2026-09-20T03:01:00Z",
            authority_refs=("correction:self",),
        )
    edge_ba = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=replacement_b.occurrence_ref,
        replacement=original,
        reason="b-to-a",
        admitted_at="2026-09-20T03:02:00Z",
        authority_refs=("correction:b-a",),
    )
    with pytest.raises(GoalPhaseTemporalError, match="reuses"):
        _ = replace(
            transition.after_ledger,
            supersessions=(edge_ab, edge_ba),
        )
    replacement_c = replace(
        original,
        effective_at="2026-09-20T01:58:00Z",
        recorded_at="2026-09-20T03:02:00Z",
    )
    edge_bc = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=replacement_b.occurrence_ref,
        replacement=replacement_c,
        reason="b-to-c",
        admitted_at="2026-09-20T03:03:00Z",
        authority_refs=("correction:b-c",),
    )
    edge_cb = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=replacement_c.occurrence_ref,
        replacement=replacement_b,
        reason="c-to-b",
        admitted_at="2026-09-20T03:04:00Z",
        authority_refs=("correction:c-b",),
    )
    with pytest.raises(GoalPhaseTemporalError, match="reuses"):
        _ = replace(
            transition.after_ledger,
            supersessions=(edge_ab, edge_bc, edge_cb),
        )


@pytest.mark.parametrize(
    ("coverage", "gaps", "downstream_refs"),
    (
        (GoalPhaseHistoryCoverage.COMPLETE, (), ()),
        (
            GoalPhaseHistoryCoverage.PARTIAL,
            (GoalLanePhaseTemporalGapV1(0, 0, "unresolved-prefix"),),
            (),
        ),
        (
            GoalPhaseHistoryCoverage.PARTIAL,
            (GoalLanePhaseTemporalGapV1(2, 2, "unresolved-suffix"),),
            ("not-a-downstream-replacement",),
        ),
    ),
)
def test_state_changing_supersessions_are_unsupported_in_o7_v1(
    coverage: GoalPhaseHistoryCoverage,
    gaps: tuple[GoalLanePhaseTemporalGapV1, ...],
    downstream_refs: tuple[str, ...],
) -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    active = _phase(GoalLanePhaseState.ACTIVE)
    if coverage is GoalPhaseHistoryCoverage.COMPLETE:
        original = _occurrence(planned)
    else:
        predecessor = "goal-phase-transition-slot:sha256:" + "f" * 64
        original = _occurrence(planned, ordinal=1, predecessor=predecessor)
    ledger = _ledger(
        active,
        _origin(planned),
        (original,),
        coverage=coverage,
        gaps=gaps,
    )
    replacement = replace(
        original,
        to_state=GoalLanePhaseState.WITHDRAWN,
        recorded_at="2026-09-20T03:00:00Z",
    )
    supersession = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=original.occurrence_ref,
        replacement=replacement,
        reason="attempt-state-change",
        admitted_at="2026-09-20T03:01:00Z",
        authority_refs=("correction:state-change",),
        downstream_revalidation_refs=downstream_refs,
    )
    with pytest.raises(GoalPhaseTemporalError, match="unsupported in O7 V1"):
        _ = replace(ledger, supersessions=(supersession,))


def test_supersession_admission_time_is_causally_nondecreasing() -> None:
    transition, original = _transition_plan()
    replacement_b = replace(
        original,
        effective_at="2026-09-20T01:59:00Z",
        recorded_at="2026-09-20T03:00:00Z",
    )
    edge_ab = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=original.occurrence_ref,
        replacement=replacement_b,
        reason="a-to-b",
        admitted_at="2026-09-20T05:00:00Z",
        authority_refs=("correction:a-b",),
    )
    replacement_c = replace(
        replacement_b,
        effective_at="2026-09-20T01:58:00Z",
        recorded_at="2026-09-20T03:30:00Z",
    )
    earlier_edge_bc = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=replacement_b.occurrence_ref,
        replacement=replacement_c,
        reason="b-to-c-too-early",
        admitted_at="2026-09-20T04:00:00Z",
        authority_refs=("correction:b-c",),
    )
    with pytest.raises(GoalPhaseTemporalError, match="nondecreasing"):
        _ = replace(
            transition.after_ledger,
            supersessions=(edge_ab, earlier_edge_bc),
        )

    equal_edge_bc = replace(
        earlier_edge_bc,
        admitted_at=edge_ab.admitted_at,
    )
    equal_time = replace(
        transition.after_ledger,
        supersessions=(edge_ab, equal_edge_bc),
    )
    assert equal_time.supersessions[-1].admitted_at == edge_ab.admitted_at

    replacement_d = replace(
        replacement_c,
        effective_at="2026-09-20T01:57:00Z",
        recorded_at="2026-09-20T04:30:00Z",
    )
    edge_cd = GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=replacement_c.occurrence_ref,
        replacement=replacement_d,
        reason="c-to-d",
        admitted_at="2026-09-20T05:01:00Z",
        authority_refs=("correction:c-d",),
    )
    multi_edge = replace(
        transition.after_ledger,
        supersessions=(edge_ab, equal_edge_bc, edge_cd),
    )
    assert len(multi_edge.supersessions) == 3


def test_supersession_admission_order_applies_across_slots() -> None:
    planned = _phase(GoalLanePhaseState.PLANNED)
    held = _phase(GoalLanePhaseState.HELD)
    first = _occurrence(planned)
    second = _occurrence(
        planned,
        ordinal=1,
        predecessor=first.transition_slot_ref,
        from_state=GoalLanePhaseState.ACTIVE,
        to_state=GoalLanePhaseState.HELD,
        effective_at="2026-09-20T03:00:00Z",
        recorded_at="2026-09-20T03:01:00Z",
    )
    ledger = _ledger(held, _origin(planned), (first, second))
    first_replacement = replace(
        first,
        effective_at="2026-09-20T01:59:00Z",
        recorded_at="2026-09-20T03:30:00Z",
    )
    second_replacement = replace(
        second,
        effective_at="2026-09-20T02:59:00Z",
        recorded_at="2026-09-20T03:30:00Z",
    )
    first_edge = GoalLanePhaseTransitionSupersessionV1(
        first.occurrence_ref,
        first_replacement,
        "correct-first-slot",
        "2026-09-20T05:00:00Z",
        ("correction:first",),
    )
    second_edge = GoalLanePhaseTransitionSupersessionV1(
        second.occurrence_ref,
        second_replacement,
        "correct-second-slot",
        "2026-09-20T04:00:00Z",
        ("correction:second",),
    )
    with pytest.raises(GoalPhaseTemporalError, match="nondecreasing"):
        _ = replace(ledger, supersessions=(first_edge, second_edge))


def test_known_effective_slot_cannot_also_be_a_gap() -> None:
    transition, occurrence = _transition_plan()
    with pytest.raises(GoalPhaseTemporalError, match="overlaps"):
        _ = replace(
            transition.after_ledger,
            history_coverage=GoalPhaseHistoryCoverage.PARTIAL,
            gaps=(GoalLanePhaseTemporalGapV1(0, 0, "contradiction"),),
        )
    correction = _correction_plan()
    with pytest.raises(GoalPhaseTemporalError, match="overlaps"):
        _ = replace(
            correction.after_ledger,
            history_coverage=GoalPhaseHistoryCoverage.PARTIAL,
            gaps=(
                GoalLanePhaseTemporalGapV1(
                    occurrence.slot_ordinal,
                    occurrence.slot_ordinal,
                    "effective-tip-contradiction",
                ),
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "replacement_value"),
    (
        ("plan_ref", "goal-phase-temporal-intent:sha256:" + "4" * 64),
        ("repository_commit_receipt_ref", "repository-commit:forged"),
        ("repository_commit_ref", "b" * 40),
        ("changed_paths", ["state/phase.json", "state/foreign.json"]),
        ("phase_postimage_digest", "sha256:" + "5" * 64),
        ("ledger_postimage_digest", "sha256:" + "6" * 64),
    ),
)
def test_publication_receipt_rejects_effect_tampering(
    field_name: str, replacement_value: object
) -> None:
    plan, _ = _transition_plan()
    receipt = GoalPhaseTemporalPublicationReceiptV1(
        plan=plan,
        repository_commit_receipt_ref=_COMMIT_RECEIPT,
        repository_commit_ref=_COMMIT,
        publication_state=GoalPhaseTemporalPublicationState.REPOSITORY_PUBLISHED,
        reconciliation_reason_codes=(),
    )
    raw = cast(
        dict[str, object],
        json.loads(encode_goal_phase_temporal_publication_receipt(receipt)),
    )
    raw[field_name] = replacement_value
    with pytest.raises(
        GoalPhaseTemporalError, match="differs|resolve the exact committed revision"
    ):
        _ = decode_goal_phase_temporal_publication_receipt(
            json.dumps(raw).encode(), plan=plan
        )


def test_observation_currentness_requires_independent_exact_authority() -> None:
    plan, occurrence = _transition_plan()
    receipt = GoalPhaseTemporalPublicationReceiptV1(
        plan=plan,
        repository_commit_receipt_ref=_COMMIT_RECEIPT,
        repository_commit_ref=_COMMIT,
        publication_state=GoalPhaseTemporalPublicationState.REPOSITORY_PUBLISHED,
        reconciliation_reason_codes=(),
    )
    authority = _authority(
        plan.after_phase,
        plan.after_ledger,
        currentness=GoalPhaseTemporalCurrentness.CURRENT,
        publication_receipt=receipt,
    )
    assert decode_goal_phase_temporal_observation_authority(
        encode_goal_phase_temporal_observation_authority(authority)
    ) == authority
    selector = GoalPhaseTransitionSelectorV1(
        GoalPhaseTransitionSelectorKind.BY_SLOT,
        transition_slot_ref=occurrence.transition_slot_ref,
    )
    observation = observe_goal_phase_temporal_facts(
        phase=plan.after_phase,
        ledger=plan.after_ledger,
        selectors=(selector,),
        authority=authority,
        publication_receipt=receipt,
    )
    assert observation.currentness is GoalPhaseTemporalCurrentness.CURRENT
    assert decode_goal_phase_temporal_observation(
        encode_goal_phase_temporal_observation(observation),
        phase=plan.after_phase,
        ledger=plan.after_ledger,
        authority=authority,
        publication_receipt=receipt,
    ) == observation

    with pytest.raises(GoalPhaseTemporalError, match="currentness receipt"):
        _ = replace(
            authority,
            currentness_receipt_ref=(
                "goal-phase-temporal-currentness:sha256:" + "7" * 64
            ),
        )
    with pytest.raises(GoalPhaseTemporalError, match="snapshot receipt"):
        _ = replace(authority, snapshot_at="2026-09-20T05:00:00Z")
    with pytest.raises(GoalPhaseTemporalError, match="snapshot receipt"):
        _ = replace(authority, source_revision_ref="c" * 40)
    with pytest.raises(GoalPhaseTemporalError, match="authority source"):
        _ = observe_goal_phase_temporal_facts(
            phase=plan.after_phase,
            ledger=plan.after_ledger,
            selectors=(selector,),
            authority=replace(
                authority,
                publication_receipt_ref=(
                    "goal-phase-temporal-publication:sha256:" + "8" * 64
                ),
            ),
            publication_receipt=receipt,
        )
    other_ledger = replace(
        plan.after_ledger,
        evidence_refs=("ledger-evidence:other",),
    )
    with pytest.raises(GoalPhaseTemporalError, match="detached"):
        _ = observe_goal_phase_temporal_facts(
            phase=plan.after_phase,
            ledger=other_ledger,
            selectors=(selector,),
            authority=authority,
            publication_receipt=receipt,
        )

    raw = observation.to_wire()
    raw["snapshot_at"] = "2026-09-20T05:00:00Z"
    body = {key: value for key, value in raw.items() if key != "observation_ref"}
    from aware_goal_operational_runtime.identity import fingerprint

    raw["observation_ref"] = "goal-phase-temporal-observation:" + fingerprint(body)
    with pytest.raises(GoalPhaseTemporalError, match="derived"):
        _ = decode_goal_phase_temporal_observation(
            json.dumps(raw).encode(),
            phase=plan.after_phase,
            ledger=plan.after_ledger,
            authority=authority,
            publication_receipt=receipt,
        )
