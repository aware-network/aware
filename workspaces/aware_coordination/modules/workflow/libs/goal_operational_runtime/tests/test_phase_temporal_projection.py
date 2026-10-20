from __future__ import annotations

import json
from dataclasses import replace
from typing import Literal

import pytest
from aware_goal_operational_runtime import (
    GoalLanePhaseState,
    GoalLanePhaseTemporalGapV1,
    GoalPhaseHistoryCoverage,
    GoalPhaseTemporalCurrentness,
    GoalPhaseTemporalObservationAuthorityKind,
    GoalPhaseTemporalObservationAuthorityV1,
    GoalPhaseTemporalPublicationReceiptV1,
    GoalPhaseTemporalPublicationState,
    GoalPhaseTransitionSelectorKind,
    GoalPhaseTransitionSelectorV1,
    derive_goal_phase_temporal_publication_binding,
    derive_goal_phase_temporal_currentness_receipt_ref,
    derive_goal_phase_temporal_snapshot_receipt_ref,
    goal_phase_temporal_phase_binding_digest,
    observe_goal_phase_temporal_facts,
)
from aware_goal_operational_runtime.phase_temporal_projection import (
    GoalPhaseTemporalNotSuppliedV1,
    GoalPhaseTemporalProjectionError,
    VerifiedGoalPhaseTemporalWorkflowSourceV1,
    _seal_goal_phase_temporal_workflow_source,
    decode_goal_phase_temporal_projection_result,
    goal_phase_temporal_projection_ref,
    project_goal_phase_temporal_workflow,
)
from aware_goal_operational_runtime.phase_contracts import GoalPhaseCoordinate

from test_phase_temporal_occurrence import (
    _authority,
    _correction_plan,
    _transition_plan,
)


def _qualified_source(
    target_state: GoalLanePhaseState = GoalLanePhaseState.ACTIVE,
    snapshot_at: str = "2026-09-20T04:00:00Z",
    *,
    gap_side: Literal["before", "after"] | None = None,
    corrected: bool = False,
) -> VerifiedGoalPhaseTemporalWorkflowSourceV1:
    if corrected:
        plan = _correction_plan()
    else:
        plan, _ = _transition_plan()
    if gap_side == "before":
        occurrence = replace(
            plan.after_ledger.occurrences[0],
            slot_ordinal=1,
            predecessor_slot_ref="goal-phase-transition-slot:sha256:" + "9" * 64,
        )
        binding = derive_goal_phase_temporal_publication_binding(
            coordinate=plan.after_phase.coordinate,
            publication_profile=plan.publication_profile,
            phase_binding_digest=goal_phase_temporal_phase_binding_digest(
                plan.after_phase
            ),
            prior_ledger_digest=plan.before_ledger.ledger_digest,
            ledger_revision=plan.after_ledger.coverage_through.ledger_revision,
            appended_occurrence_refs=(occurrence.occurrence_ref,),
            appended_supersession_refs=(),
            phase_path=plan.phase_path,
            ledger_path=plan.ledger_path,
        )
        ledger = replace(
            plan.after_ledger,
            occurrences=(occurrence,),
            history_coverage=GoalPhaseHistoryCoverage.PARTIAL,
            gaps=(GoalLanePhaseTemporalGapV1(0, 0, "unresolved-prefix"),),
            coverage_through=replace(
                plan.after_ledger.coverage_through,
                publication_binding_ref=binding,
            ),
        )
        plan = replace(
            plan,
            after_ledger=ledger,
            appended_occurrence_refs=(occurrence.occurrence_ref,),
            publication_binding_ref=binding,
        )
    elif gap_side == "after":
        ledger = replace(
            plan.after_ledger,
            history_coverage=GoalPhaseHistoryCoverage.PARTIAL,
            gaps=(GoalLanePhaseTemporalGapV1(1, 1, "unresolved-suffix"),),
        )
        plan = replace(plan, after_ledger=ledger)
    phase, ledger = plan.after_phase, plan.after_ledger
    publication = GoalPhaseTemporalPublicationReceiptV1(
        plan=plan,
        repository_commit_receipt_ref="repository-commit:" + "a" * 40,
        repository_commit_ref="a" * 40,
        publication_state=GoalPhaseTemporalPublicationState.REPOSITORY_PUBLISHED,
        reconciliation_reason_codes=(),
    )
    kind = GoalPhaseTemporalObservationAuthorityKind.H4
    admission = "goal-temporal-observation-authority-admission:sha256:" + "1" * 64
    binding = goal_phase_temporal_phase_binding_digest(phase)
    boundary = ledger.coverage_through.publication_binding_ref
    snapshot = snapshot_at
    snapshot_ref = derive_goal_phase_temporal_snapshot_receipt_ref(
        authority_kind=kind,
        coordinate=phase.coordinate,
        ledger_digest=ledger.ledger_digest,
        phase_binding_digest=binding,
        coverage_publication_binding_ref=boundary,
        source_revision_ref=publication.repository_commit_ref,
        snapshot_at=snapshot,
        authority_admission_receipt_ref=admission,
    )
    currentness_ref = derive_goal_phase_temporal_currentness_receipt_ref(
        authority_kind=kind,
        coordinate=phase.coordinate,
        ledger_digest=ledger.ledger_digest,
        phase_binding_digest=binding,
        coverage_publication_binding_ref=boundary,
        source_revision_ref=publication.repository_commit_ref,
        snapshot_receipt_ref=snapshot_ref,
        currentness=GoalPhaseTemporalCurrentness.CURRENT,
        authority_admission_receipt_ref=admission,
    )
    authority = GoalPhaseTemporalObservationAuthorityV1(
        authority_kind=kind,
        coordinate=phase.coordinate,
        ledger_digest=ledger.ledger_digest,
        phase_binding_digest=binding,
        coverage_publication_binding_ref=boundary,
        source_revision_ref=publication.repository_commit_ref,
        snapshot_at=snapshot,
        snapshot_receipt_ref=snapshot_ref,
        currentness=GoalPhaseTemporalCurrentness.CURRENT,
        currentness_receipt_ref=currentness_ref,
        authority_admission_receipt_ref=admission,
        publication_receipt_ref=publication.receipt_ref,
    )
    selectors = (
        GoalPhaseTransitionSelectorV1(
            kind=GoalPhaseTransitionSelectorKind.FIRST_ENTRY,
            target_state=target_state,
        ),
    )
    if gap_side is not None or corrected:
        selectors = (
            GoalPhaseTransitionSelectorV1(
                kind=GoalPhaseTransitionSelectorKind.BY_SLOT,
                transition_slot_ref=ledger.occurrences[0].transition_slot_ref,
            ),
            *selectors,
            GoalPhaseTransitionSelectorV1(
                kind=GoalPhaseTransitionSelectorKind.LATEST_ENTRY,
                target_state=target_state,
            ),
        )
    observation = observe_goal_phase_temporal_facts(
        phase=phase,
        ledger=ledger,
        selectors=selectors,
        authority=authority,
        publication_receipt=publication,
    )
    return _seal_goal_phase_temporal_workflow_source(
        phase=phase,
        ledger=ledger,
        publication_receipt=publication,
        authority=authority,
        observation=observation,
        goal_source_revision="b" * 40,
        goal_source_path="docs/goals/actorworld.md",
        goal_source_sha256="c" * 64,
        source_verification_receipt_ref="goal-source-verification:sha256:" + "d" * 64,
        source_envelope_digest="sha256:" + "e" * 64,
        h4_payload_digest="sha256:" + "f" * 64,
        committed_blob_oid="0" * 40,
    )


def test_not_supplied_has_no_qualified_root_or_time() -> None:
    source = _qualified_source()
    result = GoalPhaseTemporalNotSuppliedV1(
        source.phase.coordinate, "legacy_h4_source_evidence_absent"
    )
    assert result.to_wire() == {
        "schema_id": "aware.goal.phase-temporal-projection-result.v1",
        "kind": "not_supplied",
        "coordinate": {
            "goal_tag": source.phase.coordinate.goal_tag,
            "lane_key": source.phase.coordinate.lane_key,
            "phase_key": source.phase.coordinate.phase_key,
        },
        "reason": "legacy_h4_source_evidence_absent",
    }


def test_qualified_preserves_only_selected_o7_fact_and_three_times() -> None:
    result = project_goal_phase_temporal_workflow(_qualified_source()).to_wire()
    root = result["root"]
    assert isinstance(root, dict)
    assert root["snapshot_at"] == "2026-09-20T04:00:00Z"
    assert root["coverage"]["kind"] == "complete"
    assert len(root["facts"]) == 1
    fact = root["facts"][0]
    assert fact["availability"] == "present"
    assert fact["effective_at"] == "2026-09-20T02:00:00Z"
    assert fact["recorded_at"] == "2026-09-20T02:01:00Z"
    assert "sequence" not in root


def test_complete_history_not_occurred_never_invents_time() -> None:
    result = project_goal_phase_temporal_workflow(
        _qualified_source(GoalLanePhaseState.HELD)
    ).to_wire()
    root = result["root"]
    assert isinstance(root, dict)
    fact = root["facts"][0]
    assert fact["availability"] == "not_occurred"
    assert fact["effective_at"] is None
    assert fact["recorded_at"] is None


@pytest.mark.parametrize(
    ("gap_side", "expected_availability"),
    (
        ("before", ("present", "unavailable", "present")),
        ("after", ("present", "present", "unavailable")),
    ),
)
def test_partial_history_preserves_gap_and_selector_availability(
    gap_side: Literal["before", "after"],
    expected_availability: tuple[str, str, str],
) -> None:
    result = project_goal_phase_temporal_workflow(
        _qualified_source(gap_side=gap_side)
    ).to_wire()
    root = result["root"]
    assert root["coverage"]["kind"] == "partial"
    assert root["coverage"]["gaps"][0]["reason"].startswith("unresolved-")
    assert tuple(fact["availability"] for fact in root["facts"]) == (
        expected_availability
    )
    for fact in root["facts"]:
        if fact["availability"] == "unavailable":
            assert fact["effective_at"] is None
            assert fact["recorded_at"] is None


def test_corrected_slot_carries_only_o7_effective_tip() -> None:
    result = project_goal_phase_temporal_workflow(
        _qualified_source(corrected=True)
    ).to_wire()
    root = result["root"]
    assert len(root["facts"]) == 3
    assert {fact["occurrence_ref"] for fact in root["facts"]} == {
        root["facts"][0]["occurrence_ref"]
    }
    assert root["facts"][0]["effective_at"] == "2026-09-20T01:59:00Z"
    assert root["facts"][0]["recorded_at"] == "2026-09-20T03:00:00Z"
    assert "supersessions" not in root


def test_projection_identity_distinguishes_phases_under_one_goal() -> None:
    source = _qualified_source()
    first = project_goal_phase_temporal_workflow(source).root["projection_ref"]
    second_coordinate = GoalPhaseCoordinate(
        source.phase.coordinate.goal_tag, "other-lane", "other-phase"
    )
    second = goal_phase_temporal_projection_ref(
        coordinate=second_coordinate,
        source_envelope_digest=source.source_envelope_digest,
        h4_payload_digest=source.h4_payload_digest,
        observation_ref=source.observation.observation_ref,
        snapshot_receipt_ref=source.authority.snapshot_receipt_ref,
    )
    assert first != second


def test_projection_identity_distinguishes_snapshots_of_one_phase() -> None:
    first = project_goal_phase_temporal_workflow(_qualified_source()).root[
        "projection_ref"
    ]
    second = project_goal_phase_temporal_workflow(
        _qualified_source(snapshot_at="2026-09-20T05:00:00Z")
    ).root["projection_ref"]
    assert first != second


def test_forged_and_mutated_provider_result_refuse() -> None:
    source = _qualified_source()
    with pytest.raises(GoalPhaseTemporalProjectionError, match="provider-sealed"):
        project_goal_phase_temporal_workflow(
            object.__new__(VerifiedGoalPhaseTemporalWorkflowSourceV1)
        )
    object.__setattr__(source, "goal_source_path", "docs/goals/substitute.md")
    with pytest.raises(GoalPhaseTemporalProjectionError, match="mutated"):
        project_goal_phase_temporal_workflow(source)


def test_non_h4_authority_refuses_even_when_other_bindings_match() -> None:
    source = _qualified_source()
    wrong = _authority(
        source.phase, source.ledger, publication_receipt=source.publication_receipt
    )
    forged = _seal_goal_phase_temporal_workflow_source(
        phase=source.phase,
        ledger=source.ledger,
        publication_receipt=source.publication_receipt,
        authority=wrong,
        observation=source.observation,
        goal_source_revision=source.goal_source_revision,
        goal_source_path=source.goal_source_path,
        goal_source_sha256=source.goal_source_sha256,
        source_verification_receipt_ref=source.source_verification_receipt_ref,
        source_envelope_digest=source.source_envelope_digest,
        h4_payload_digest=source.h4_payload_digest,
        committed_blob_oid=source.committed_blob_oid,
    )
    with pytest.raises(GoalPhaseTemporalProjectionError, match="binding differs"):
        project_goal_phase_temporal_workflow(forged)


def test_result_decoder_recomputes_qualified_projection() -> None:
    source = _qualified_source()
    payload = json.dumps(project_goal_phase_temporal_workflow(source).to_wire()).encode()
    assert decode_goal_phase_temporal_projection_result(
        payload, source=source
    ).to_wire() == project_goal_phase_temporal_workflow(source).to_wire()
    with pytest.raises(GoalPhaseTemporalProjectionError, match="verified source"):
        decode_goal_phase_temporal_projection_result(payload)
    altered = json.loads(payload)
    altered["root"]["o7_ledger_revision"] = True
    with pytest.raises(GoalPhaseTemporalProjectionError, match="differs"):
        decode_goal_phase_temporal_projection_result(
            json.dumps(altered).encode(), source=source
        )
    altered = json.loads(payload)
    altered["root"]["facts"][0]["effective_at"] = "2026-09-20T01:00:00Z"
    with pytest.raises(GoalPhaseTemporalProjectionError, match="differs"):
        decode_goal_phase_temporal_projection_result(
            json.dumps(altered).encode(), source=source
        )


def test_not_supplied_decoder_rejects_added_authority() -> None:
    source = _qualified_source()
    result = GoalPhaseTemporalNotSuppliedV1(
        source.phase.coordinate, "no_h4_observation"
    )
    payload = json.dumps(result.to_wire()).encode()
    assert decode_goal_phase_temporal_projection_result(payload) == result
    altered = result.to_wire()
    altered["snapshot_at"] = "2026-09-20T04:00:00Z"
    with pytest.raises(GoalPhaseTemporalProjectionError, match="fields differ"):
        decode_goal_phase_temporal_projection_result(json.dumps(altered).encode())
    duplicate = payload.replace(
        b'"kind": "not_supplied"',
        b'"kind": "qualified", "kind": "not_supplied"',
    )
    with pytest.raises(GoalPhaseTemporalProjectionError, match="duplicate"):
        decode_goal_phase_temporal_projection_result(duplicate)
