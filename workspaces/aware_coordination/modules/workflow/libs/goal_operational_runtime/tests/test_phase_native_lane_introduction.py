"""Neutral preservation and public-plan consumption; no authority callbacks."""
import hashlib
from dataclasses import replace

import pytest
from aware_goal_operational_runtime import (
    GoalPhaseCoordinate, GoalLanePhase, GoalLanePhaseState,
    GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4,
    GoalPhaseOperationJournalEntryV1, GoalPhaseOperationJournalV1,
    attach_goal_phase_native_carrier, extract_goal_phase_native_carrier,
)
from aware_goal_operational_runtime.phase_native_lane_introduction import (
    plan_goal_native_lane_introduction, validate_goal_native_lane_introduction_plan,
)
from test_phase_native_lane_authority import _transition


def _fixture(version):
    before, target, _ = _transition()
    compatibility = b"Legacy compatibility stays exact.\n"
    before = replace(before, compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
        compatibility_projection_byte_count=len(compatibility))
    lane = target.native_lane_authorities[0]
    if version == "v3":
        d = before.definitions[0]
        phase = GoalLanePhase(coordinate=d.coordinate, ordinal=d.ordinal,
            title=d.title, intent=d.intent, gate=d.gate, state=GoalLanePhaseState.PLANNED)
        entry = GoalPhaseOperationJournalEntryV1(operation_kind="approve_pursuit", decision="approve",
            coordinate=d.coordinate, gate_digest=d.gate.gate_digest, source_preimage_ref=before.document_ref,
            actor_ref="identity:structural-only", action_occurrence_ref="actor-action-occurrence:sha256:" + "1" * 64,
            policy_ref="goal-phase-approval-policy:sha256:" + "2" * 64, policy_digest="sha256:" + "3" * 64,
            idempotency_key="fixture", delta_ref="goal-phase-delta:sha256:" + "4" * 64,
            event_ref="goal-phase-event:sha256:" + "5" * 64)
        before = GoalPhaseNativeDocumentV3(goal_tag=before.goal_tag,
            compatibility_projection_sha256=before.compatibility_projection_sha256,
            compatibility_projection_byte_count=before.compatibility_projection_byte_count,
            definitions=before.definitions, operational_bundle=replace(before.operational_bundle, phases=(phase,)),
            unresolved_dependencies=before.unresolved_dependencies, source_refs=before.source_refs,
            execution_authority=before.execution_authority, phase_operation_journal=GoalPhaseOperationJournalV1((entry,)))
    elif version == "v4":
        retained = replace(lane, lane_key="retained")
        definition = replace(before.definitions[0], coordinate=GoalPhaseCoordinate(before.goal_tag, "retained", "f1"))
        before = GoalPhaseNativeDocumentV4(goal_tag=before.goal_tag,
            compatibility_projection_sha256=before.compatibility_projection_sha256,
            compatibility_projection_byte_count=before.compatibility_projection_byte_count,
            definitions=(*before.definitions, definition), operational_bundle=before.operational_bundle,
            unresolved_dependencies=before.unresolved_dependencies, source_refs=before.source_refs,
            execution_authority=before.execution_authority, native_lane_authorities=(retained,),
            operation_journal_profile="none")
    return attach_goal_phase_native_carrier(compatibility, before), before, lane


@pytest.mark.parametrize("version", ["v2", "v3", "v4"])
def test_one_lane_preserves_complete_carrier(version):
    candidate, before, lane = _fixture(version)
    plan = plan_goal_native_lane_introduction(candidate=candidate, lane=lane, represented_lane_keys=())
    compatibility, after = extract_goal_phase_native_carrier(plan.after_candidate)
    assert compatibility == extract_goal_phase_native_carrier(candidate)[0]
    for field in ("definitions", "operational_bundle", "unresolved_dependencies", "source_refs", "execution_authority"):
        assert getattr(before, field) == getattr(after, field)
    assert getattr(before, "phase_operation_journal", None) == after.phase_operation_journal
    assert after.native_lane_authorities == tuple(sorted((*getattr(before, "native_lane_authorities", ()), lane), key=lambda l: l.lane_key))
    validate_goal_native_lane_introduction_plan(plan)


@pytest.mark.parametrize("fault", ["duplicate", "shared", "foreign", "hold", "bad_inventory"])
def test_refuse_unqualified_or_nonadditive_lane(fault):
    candidate, _, lane = _fixture("v4")
    keys = ()
    if fault == "duplicate": lane = replace(lane, lane_key="retained")
    elif fault == "shared": keys = (lane.lane_key,)
    elif fault == "foreign": lane = replace(lane, goal_tag="goal/2026-09-29/foreign")
    elif fault == "hold": lane = replace(lane, operational_state="held", state_detail="Explicit hold", hold_authority_refs=("hold:sha256:" + "a" * 64,))
    else: keys = ("z", "a")
    with pytest.raises(ValueError):
        plan_goal_native_lane_introduction(candidate=candidate, lane=lane, represented_lane_keys=keys)


@pytest.mark.parametrize("field", ["after_candidate", "semantic_intent_ref", "after_document"])
def test_actually_valid_plan_mutation_refuses(field):
    candidate, _, lane = _fixture("v2")
    plan = plan_goal_native_lane_introduction(candidate=candidate, lane=lane, represented_lane_keys=())
    validate_goal_native_lane_introduction_plan(plan)
    replacement = b"forged" if field == "after_candidate" else "intent:forged"
    if field == "after_document":
        replacement = replace(plan.after_document, source_refs=("source:changed",))
    object.__setattr__(plan, field, replacement)
    with pytest.raises(ValueError, match="plan_mutated"):
        validate_goal_native_lane_introduction_plan(plan)
