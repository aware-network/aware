"""Portable projection and strict transport proofs, not installed authority."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import pytest
from aware_goal_operational_runtime import (
    GoalDependencyRelation, GoalLanePhase, GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate, GoalLanePhaseGateObservation, GoalLanePhaseGateOutcome,
    GoalLanePhaseState, GoalLanePhaseWork, GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole, GoalPhaseContractBundleV1, GoalPhaseCoordinate,
    GoalPhaseDependency, GoalPhaseExecutionAuthorityV1, GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3, GoalPhaseOperationJournalV1, GoalPhaseOperationJournalEntryV1,
    GoalPhaseUnresolvedDependencyV1, encode_goal_phase_native_document,
)
from aware_goal_operational_runtime.phase_native_view import (
    SOURCE_SCHEMA, canonical_json, decode_goal_native_view_source,
    decode_goal_native_view_state, project_goal_native_view_v2,
)

GOAL = "goal/2026-10-03/native-view-proof"


def source_fixture(*, observations=False, journal=False, outcome=GoalLanePhaseGateOutcome.SATISFIED):
    gate = GoalLanePhaseGate(gate_key="proof", promise="Preserve honest native meaning.",
        gate_contract_ref="contract:proof", evidence_schema_ref="evidence:proof")
    first = GoalLanePhaseDefinitionV1(coordinate=GoalPhaseCoordinate(GOAL, "z-first", "current"),
        ordinal=2, title="Current preparation", intent="Prepare without claiming execution.", gate=gate)
    future = replace(first, coordinate=replace(first.coordinate, phase_key="future"), ordinal=1,
        title="Future definition", intent="Remain non-operational.")
    native = replace(first, coordinate=GoalPhaseCoordinate(GOAL, "a-native-only", "foundation"),
        ordinal=1, title=None, intent=None)
    work = GoalLanePhaseWork(association_ref="work:current", issue_ref="fb/2026-10-03/proof",
        role=GoalLanePhaseWorkRole.IMPLEMENTATION, disposition=GoalLanePhaseWorkDisposition.CURRENT,
        admitted_at="2026-10-03T12:00:00Z", receipt_ref="work-admission:proof")
    old = replace(work, association_ref="work:old", disposition=GoalLanePhaseWorkDisposition.RETIRED,
        role=GoalLanePhaseWorkRole.GOVERNANCE, retired_at="2026-10-03T12:00:00Z")
    claims = tuple(GoalLanePhaseGateObservation(observation_ref="observation:" + outcome.value,
        gate_digest=gate.gate_digest, outcome=outcome, evaluator_ref="evaluator:recorded",
        evidence_refs=("evidence:historical",), source_revision_refs=("source:historical",),
        evaluated_at="2026-10-02T12:00:00Z", currentness_ref="currentness:historical")
        for outcome in (outcome,)) if observations else ()
    phase = GoalLanePhase(coordinate=first.coordinate, title=first.title, intent=first.intent,
        ordinal=first.ordinal, gate=gate, state=GoalLanePhaseState.ACTIVE,
        gate_observations=claims, work_associations=(old, work))
    doc = GoalPhaseNativeDocumentV2(goal_tag=GOAL,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(b"compatibility").hexdigest(),
        compatibility_projection_byte_count=13, definitions=(first, future, native),
        operational_bundle=GoalPhaseContractBundleV1(phases=(phase,), dependencies=(
            GoalPhaseDependency(owner_goal_tag=GOAL, dependency_key="current-requires-future",
                dependent=first.coordinate, prerequisite=future.coordinate,
                required_gate_digest=gate.gate_digest, relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
                reason="Recorded dependency, not evaluated."),)),
        unresolved_dependencies=(GoalPhaseUnresolvedDependencyV1(owner_goal_tag=GOAL,
            dependency_key="external-unresolved", dependent=first.coordinate,
            prerequisite=GoalPhaseCoordinate("goal/2026-10-03/external", "external", "proof"),
            relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE, reason="External Gate unavailable."),),
        source_refs=("source:fixture",), execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64))
    if journal:
        doc = GoalPhaseNativeDocumentV3(goal_tag=doc.goal_tag,
            compatibility_projection_sha256=doc.compatibility_projection_sha256,
            compatibility_projection_byte_count=doc.compatibility_projection_byte_count,
            definitions=doc.definitions, operational_bundle=doc.operational_bundle,
            unresolved_dependencies=doc.unresolved_dependencies, source_refs=doc.source_refs,
            execution_authority=doc.execution_authority, phase_operation_journal=GoalPhaseOperationJournalV1(entries=(
                GoalPhaseOperationJournalEntryV1(operation_kind="approve_pursuit", decision="approve",
                    coordinate=first.coordinate, gate_digest=gate.gate_digest, source_preimage_ref=doc.document_ref,
                    actor_ref="actor:fixture", action_occurrence_ref="action:sha256:" + "4" * 64,
                    policy_ref="policy:sha256:" + "5" * 64, policy_digest="sha256:" + "6" * 64,
                    idempotency_key="fixture-approval", delta_ref="delta:sha256:" + "7" * 64,
                    event_ref="event:sha256:" + "8" * 64),)))
    revision = "object-revision:portable-proof"
    lane = {"lane_key": "z-first", "label": "Authored first lane",
        "authority_availability": "source_recorded", "reason": None, "owner_ref": "actor:owner",
        "operational_state": "active", "state_detail": None, "current_issue_ref": work.issue_ref,
        "authority_ref": "lane-authority:proof", "source_revision": revision}
    absent = {**lane, "lane_key": "a-native-only", "label": "Native foundation",
        "authority_availability": "unavailable", "reason": "lane_authority_absent",
        "owner_ref": None, "operational_state": None, "current_issue_ref": None, "authority_ref": None}
    return {"schema_id": SOURCE_SCHEMA,
        "document": json.loads(encode_goal_phase_native_document(doc)),
        "source": {"profile": "portable-fixture.v2", "provider_ref": "provider:fixture",
            "provider_generation": "generation:fixture", "source_scope_ref": "scope:fixture",
            "source_revision": revision, "document_ref": doc.document_ref,
            "projection_health": "unavailable", "input_refs": ["source:fixture"]},
        "goal": {"goal_tag": GOAL, "title": "Native View proof", "lifecycle_status": "active",
            "owner_ref": "actor:owner", "hold_state": "clear", "authority_ref": "goal-authority:fixture",
            "source_revision": revision}, "lanes": [absent, lane],
        "schedules": [{"lane_key": key, "status": "absent", "reason": "schedule_absent",
            "schedule": None, "source_revision": revision} for key in ("a-native-only", "z-first")],
        "linked_issues": [{"issue_ref": work.issue_ref, "availability": "available", "reason": None,
            "tag": work.issue_ref, "title": "Proof implementation", "status": "closed",
            "owner_execution_id": "codex-fixture", "source_revision": revision, "source_ref": "source:issue",
            "priority": "P1", "acceptance_done": 2, "acceptance_total": 3,
            "updates": [{"activity_ref": work.issue_ref + "#update-1", "activity_at": "2026-10-03T12:00:00Z",
                "time_authority": "source_declared"}], "reading_view_ref": "issue.issue_reading",
            "reading_issue_ref": work.issue_ref, "reading_projection_revision": "issue-reading:fixture"}]}


def test_native_inventory_order_and_meaning_are_preserved():
    source = source_fixture()
    state = project_goal_native_view_v2(source, observation_ref="observation:fixture")
    assert [lane["reading"]["lane_key"] for lane in state["lanes"]] == ["z-first", "a-native-only"]
    first = state["lanes"][0]["phases"][0]
    assert first["operational"]["state"] == "active"
    assert first["execution_posture"] == "unavailable"
    assert first["gate_qualification"] == "not_evaluated"
    assert len(first["operational"]["work_associations"]) == 2
    assert state["definition_count"] == 3 and state["operational_phase_count"] == 1
    assert state["linked_issues"][0]["acceptance_done"] == 2
    assert decode_goal_native_view_state(canonical_json(state)) == state
    assert decode_goal_native_view_source(canonical_json(source)) == source


@pytest.mark.parametrize("outcome", [o for o in GoalLanePhaseGateOutcome if o is not GoalLanePhaseGateOutcome.NOT_EVALUATED])
def test_recorded_outcomes_retain_their_actual_epochs_without_qualification(outcome):
    state = project_goal_native_view_v2(source_fixture(observations=True, outcome=outcome), observation_ref="observation:fixture")
    phase = state["lanes"][0]["phases"][0]
    assert phase["gate_qualification"] == "unavailable"
    assert [o["outcome"] for o in phase["operational"]["gate_observations"]] == [outcome.value]
    assert all(o["source_revision_refs"] == ["source:historical"] for o in phase["operational"]["gate_observations"])


def test_v3_uses_same_reading_law():
    state = project_goal_native_view_v2(source_fixture(journal=True), observation_ref="observation:fixture")
    assert state["operational_phase_count"] == 1


def test_source_provider_kind_does_not_change_native_meaning():
    first = source_fixture()
    alternate = deepcopy(first)
    alternate["source"].update(profile="non-filesystem-test.v2", provider_ref="provider:non-filesystem")
    a = project_goal_native_view_v2(first, observation_ref="observation:fixture")
    b = project_goal_native_view_v2(alternate, observation_ref="observation:alternate")
    a.pop("source")
    b.pop("source")
    assert a == b


@pytest.mark.parametrize("mutate", [
    lambda s: s.update(unknown=True),
    lambda s: s.update(definition_count=True),
    lambda s: s["lanes"][0]["phases"][0].update(execution_posture="running"),
    lambda s: s["lanes"][0]["phases"][0].update(gate_qualification="satisfied"),
    lambda s: s["lanes"][0]["phases"][0]["definition"].update(definition_ref="forged"),
    lambda s: s["linked_issues"].clear(),
    lambda s: s["linked_issues"][0].update(acceptance_done=99),
    lambda s: s["dependencies"][0].update(observation_state="satisfied"),
    lambda s: s["lanes"][1]["reading"].update(owner_ref="invented"),
])
def test_strict_transport_refuses_substitutions(mutate):
    state = project_goal_native_view_v2(source_fixture(), observation_ref="observation:fixture")
    mutate(state)
    with pytest.raises((ValueError, TypeError)):
        decode_goal_native_view_state(canonical_json(state))


def test_duplicate_json_fields_and_source_mutation_refuse():
    state = project_goal_native_view_v2(source_fixture(), observation_ref="observation:fixture")
    with pytest.raises(ValueError):
        decode_goal_native_view_state(canonical_json(state)[:-1] + b',"schema_id":"duplicate"}')
    source = deepcopy(source_fixture())
    source["source"]["document_ref"] = "foreign"
    with pytest.raises(ValueError):
        project_goal_native_view_v2(source, observation_ref="observation:fixture")


@pytest.mark.parametrize("field", ["reading_issue_ref", "tag"])
def test_source_and_state_navigation_identity_substitution_refuse(field):
    source = source_fixture()
    state = project_goal_native_view_v2(source, observation_ref="observation:fixture")
    for payload, decoder in ((source, decode_goal_native_view_source),
                             (state, decode_goal_native_view_state)):
        payload["linked_issues"][0][field] = "fb/2026-10-03/foreign"
        with pytest.raises(ValueError, match="canonical identity"):
            decoder(canonical_json(payload))


def test_path_work_reference_keeps_canonical_issue_navigation():
    source = source_fixture()
    path = "customer/issues/2026/10/03/proof.md"
    # Re-derive carrier refs through its owner codec, not the View decoder.
    from aware_goal_operational_runtime import decode_goal_phase_native_document
    doc = decode_goal_phase_native_document(canonical_json(source["document"]))
    phase = doc.operational_bundle.phases[0]
    phase = replace(phase, work_associations=tuple(
        replace(work, issue_ref=path) for work in phase.work_associations))
    doc = replace(doc, operational_bundle=replace(doc.operational_bundle, phases=(phase,)))
    source["document"] = json.loads(encode_goal_phase_native_document(doc))
    source["source"]["document_ref"] = doc.document_ref
    source["linked_issues"][0]["issue_ref"] = path
    state = project_goal_native_view_v2(source, observation_ref="observation:fixture")
    assert state["linked_issues"][0]["reading_issue_ref"] == "fb/2026-10-03/proof"
    assert decode_goal_native_view_state(canonical_json(state)) == state
