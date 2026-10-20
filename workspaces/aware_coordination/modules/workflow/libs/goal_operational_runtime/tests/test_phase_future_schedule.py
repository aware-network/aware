from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from aware_goal_operational_runtime import (
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseFutureScheduleError,
    GoalPhaseNativeDocumentV2,
    assess_goal_phase_future_schedule,
    decode_goal_phase_future_schedule,
    encode_goal_phase_future_schedule,
    make_goal_phase_future_schedule,
    schedule_path,
)
from aware_goal_operational_runtime.phase_future_schedule import (
    GoalPhaseFutureSchedulePublicationReceiptV1,
    GoalPhaseFutureScheduleRepositoryReconciliationV1,
    decode_goal_phase_future_schedule_repository_reconciliation,
    encode_goal_phase_future_schedule_repository_reconciliation,
    goal_phase_future_schedule_definition_closure_ref,
    goal_phase_future_schedule_intent_ref,
)

GOAL = "goal/2026-09-23/schedule-proof"
PATH = "docs/goals/2026/09/23/schedule-proof.md"
ISSUE = "docs/issues/2026/09/23/fb-schedule-proof.md"
LANE = "runtime-authority-retreat"


def _document(*, new_active: bool = False) -> GoalPhaseNativeDocumentV2:
    definitions = tuple(
        GoalLanePhaseDefinitionV1(
            coordinate=GoalPhaseCoordinate(GOAL, LANE, key),
            ordinal=ordinal,
            gate=GoalLanePhaseGate(
                gate_key=key,
                promise=f"{key} accepted independently.",
                gate_contract_ref=f"contract:{key}",
                evidence_schema_ref=f"evidence:{key}",
            ),
            title=key,
            intent=f"Deliver {key}.",
        )
        for ordinal, key in ((7, "old-r4"), (8, "r5"), (9, "r4a"))
    )
    phases = tuple(
        GoalLanePhase(
            coordinate=item.coordinate,
            ordinal=item.ordinal,
            gate=item.gate,
            title=item.title or "",
            intent=item.intent or "",
            state=GoalLanePhaseState.ACTIVE,
        )
        for item in definitions
        if item.coordinate.phase_key == "r4a" or (new_active and item.coordinate.phase_key == "old-r4")
    )
    compatibility = b"# Schedule proof\n"
    return GoalPhaseNativeDocumentV2(
        goal_tag=GOAL,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
        compatibility_projection_byte_count=len(compatibility),
        definitions=definitions,
        operational_bundle=GoalPhaseContractBundleV1(phases=phases, dependencies=()),
        unresolved_dependencies=(),
        source_refs=("repository:path:" + PATH,),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
    )


def _schedule():
    return make_goal_phase_future_schedule(
        document=_document(), goal_doc_path=PATH, lane_key=LANE,
        authored_order=("r4a", "r5"), decision_issue_path=ISSUE,
        decision_issue_blob_oid="a" * 40,
    )


def test_canonical_round_trip_and_fixed_path() -> None:
    schedule = _schedule()
    assert schedule_path(goal_doc_path=PATH, lane_key=LANE) == (
        "docs/goals/2026/09/23/schedules/schedule-proof/runtime-authority-retreat.json"
    )
    assert schedule.retained_unscheduled == ("old-r4",)
    assert decode_goal_phase_future_schedule(encode_goal_phase_future_schedule(schedule)) == schedule
    assert assess_goal_phase_future_schedule(schedule=schedule, document=_document()) == ("current", None)


def test_postpublication_unscheduled_activation_stales_unchanged_record() -> None:
    schedule = _schedule()
    assert assess_goal_phase_future_schedule(schedule=schedule, document=_document(new_active=True)) == (
        "stale", "unscheduled_operational_phase"
    )


def test_empty_order_retains_all_definitions_only_without_active_or_held_phases() -> None:
    document = replace(
        _document(),
        operational_bundle=GoalPhaseContractBundleV1(phases=(), dependencies=()),
    )
    schedule = make_goal_phase_future_schedule(
        document=document, goal_doc_path=PATH, lane_key=LANE,
        authored_order=(), decision_issue_path=ISSUE,
        decision_issue_blob_oid="a" * 40,
    )
    assert schedule.authored_order == ()
    assert schedule.retained_unscheduled == ("old-r4", "r4a", "r5")
    assert decode_goal_phase_future_schedule(encode_goal_phase_future_schedule(schedule)) == schedule
    assert assess_goal_phase_future_schedule(schedule=schedule, document=document) == ("current", None)
    assert assess_goal_phase_future_schedule(schedule=schedule, document=_document()) == (
        "stale", "unscheduled_operational_phase"
    )


def test_noncanonical_and_incomplete_records_refuse() -> None:
    schedule = _schedule()
    with pytest.raises(GoalPhaseFutureScheduleError, match="partition"):
        replace(schedule, retained_unscheduled=())
    with pytest.raises(GoalPhaseFutureScheduleError, match="sorted"):
        replace(schedule, definition_bindings=tuple(reversed(schedule.definition_bindings)))
    payload = encode_goal_phase_future_schedule(schedule)
    variants = (
        payload.replace(b'"schema_id":', b'"unknown":true,"schema_id":'),
        payload.replace(b'"schedule_ref":', b'"schedule_ref":"wrong","schedule_ref":'),
        payload.replace(b'"authored_order":["r4a","r5"]', b'"authored_order":["r5","r4a"]'),
        payload + b" ",
    )
    for bad in variants:
        with pytest.raises(GoalPhaseFutureScheduleError):
            decode_goal_phase_future_schedule(bad)
    raw = json.loads(payload)
    raw["retained_unscheduled"] = ["old-r4", "old-r4"]
    with pytest.raises(GoalPhaseFutureScheduleError):
        decode_goal_phase_future_schedule(json.dumps(raw).encode())


def test_plan_rejects_excluded_active_phase() -> None:
    with pytest.raises(GoalPhaseFutureScheduleError, match="unscheduled_operational_phase"):
        make_goal_phase_future_schedule(
            document=_document(), goal_doc_path=PATH, lane_key=LANE,
            authored_order=("r5",), decision_issue_path=ISSUE,
            decision_issue_blob_oid="a" * 40,
        )


def test_repository_only_reconciliation_codec_is_strict_and_receipt_bound() -> None:
    schedule = _schedule()
    commit = "b" * 40
    publication = GoalPhaseFutureSchedulePublicationReceiptV1(
        before_schedule_ref=None,
        after_schedule_ref=schedule.schedule_ref,
        goal_tag=GOAL,
        goal_doc_path=PATH,
        lane_key=LANE,
        definition_closure_ref=goal_phase_future_schedule_definition_closure_ref(schedule),
        changed_path=schedule_path(goal_doc_path=PATH, lane_key=LANE),
        decision_issue_path=ISSUE,
        decision_issue_blob_oid="a" * 40,
        repository_commit_ref=commit,
        repository_commit_receipt_ref=f"repository-commit:{commit}",
        semantic_intent_ref=goal_phase_future_schedule_intent_ref(
            before_schedule_ref=None, after=schedule
        ),
    )
    receipt = GoalPhaseFutureScheduleRepositoryReconciliationV1(
        publication_receipt=publication,
        observed_head="c" * 40,
        goal_sha256="sha256:" + "1" * 64,
        document_ref="goal-phase-document:sha256:" + "2" * 64,
        schedule_blob_oid="d" * 40,
        index_blob_oid="d" * 40,
    )
    encoded = encode_goal_phase_future_schedule_repository_reconciliation(receipt)
    assert decode_goal_phase_future_schedule_repository_reconciliation(encoded) == receipt
    for key, altered in (
        ("worktree_disposition", "materialized"),
        ("index_blob_oid", "e" * 40),
        ("observed_head", True),
    ):
        payload = json.loads(encoded)
        payload[key] = altered
        with pytest.raises(GoalPhaseFutureScheduleError):
            decode_goal_phase_future_schedule_repository_reconciliation(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode() + b"\n"
            )
    payload = json.loads(encoded)
    payload["publication_receipt"]["receipt_ref"] = "forged"
    with pytest.raises(GoalPhaseFutureScheduleError):
        decode_goal_phase_future_schedule_repository_reconciliation(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        )
