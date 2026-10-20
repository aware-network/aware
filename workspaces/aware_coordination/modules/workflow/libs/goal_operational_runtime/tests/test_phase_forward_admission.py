from dataclasses import replace

import pytest

from aware_goal_operational_runtime import (
    GoalLanePhase, GoalLanePhaseState, GoalLanePhaseWorkRole, GoalPhaseCoordinate, GoalPhaseNativeDocumentV3,
    GoalPhaseOperationJournalEntryV1, GoalPhaseOperationJournalV1,
)
from aware_goal_operational_runtime.phase_forward_admission import (
    GoalPhaseOperationalAdmissionRequestV2, decode_forward_admission_request,
    forward_plan_wire, plan_existing_definition_admission,
)
from test_phase_native_admission import _operational_document
from aware_goal_operational_runtime.phase_forward_admission import decode_pending_projection_authority
from aware_goal_operational_runtime.phase_migrated_definition_qualification import GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1
from aware_goal_operational_runtime.identity import fingerprint
from copy import deepcopy


def pending_projection_wire():
    """Transport specimen only: fake digests never confer provider authority."""
    receipt = GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1(
        semantic_intent_ref="intent:qualification", before_document_ref="document:before", after_document_ref="document:after",
        before_definition_ref="definition:before", after_definition_ref="definition:after",
        proposal_publication_authority_ref="proposal:published", acceptance_publication_authority_ref="acceptance:published",
        publication_issue_authority_ref="issue:published", repository_parent_ref="1" * 40, repository_commit_ref="2" * 40,
        repository_commit_receipt_ref="repository-commit:" + "2" * 40,
        changed_path="customer/goals/goal.md", reconciliation_disposition="reconciliation_required")
    body = {"schema_id": "aware.goal.pending-projection-authority.v1", "profile": "migrated_definition_publication_v1",
        "goal_path": "customer/goals/goal.md", "publication_issue_path": "customer/issues/publication.md",
        "proposal_publication_path": "records/proposal.json", "acceptance_publication_path": "records/acceptance.json",
        "publication_receipt": receipt.to_wire(), "before_goal_sha256": "sha256:" + "3" * 64,
        "after_goal_sha256": "sha256:" + "4" * 64,
        "authority_paths": ["customer/issues/publication.md", "records/acceptance.json", "records/proposal.json"],
        "authority_issue_paths": ["customer/issues/publication.md"]}
    body["authority_ref"] = "goal-pending-projection-authority:" + fingerprint(body)
    return body


def test_pending_projection_transport_is_strict_detached_and_non_authorizing():
    wire = pending_projection_wire()
    decoded = decode_pending_projection_authority(wire)
    assert decoded == wire and decoded is not wire
    wire["publication_receipt"]["repository_commit_receipt_ref"] = "foreign"
    assert decoded == pending_projection_wire()


@pytest.mark.parametrize("fault", ["unknown", "profile", "path", "goal", "digest", "boolean", "omitted", "duplicate", "nested_unknown", "nested_ref"])
def test_redigested_pending_projection_substitutions_refuse(fault):
    wire = deepcopy(pending_projection_wire())
    if fault == "unknown": wire["caller_current"] = True
    elif fault == "profile": wire["profile"] = "caller_verified_v1"
    elif fault == "path": wire["proposal_publication_path"] = "../foreign.json"
    elif fault == "goal": wire["goal_path"] = "foreign/goal.md"
    elif fault == "digest": wire["after_goal_sha256"] = "sha256:not-a-digest"
    elif fault == "boolean": wire["authority_paths"] = [True]
    elif fault == "omitted": wire["authority_paths"] = ["customer/issues/publication.md"]
    elif fault == "duplicate": wire["authority_issue_paths"] *= 2
    elif fault == "nested_unknown": wire["publication_receipt"]["caller_accepted"] = True
    else: wire["publication_receipt"]["receipt_ref"] = "forged"
    wire["authority_ref"] = "goal-pending-projection-authority:" + fingerprint({k: v for k, v in wire.items() if k != "authority_ref"})
    with pytest.raises((ValueError, TypeError)):
        decode_pending_projection_authority(wire)


def source_and_request(*, journal=False):
    document = _operational_document()
    definition = document.definitions[0]
    if journal:
        other = replace(definition, coordinate=GoalPhaseCoordinate(document.goal_tag, "other", "existing"))
        document = replace(document, definitions=document.definitions + (other,),
            operational_bundle=replace(document.operational_bundle, phases=(GoalLanePhase(
                coordinate=other.coordinate, title=other.title, intent=other.intent,
                ordinal=other.ordinal, state=GoalLanePhaseState.ACTIVE, gate=other.gate),)))
        entry = GoalPhaseOperationJournalEntryV1(operation_kind="approve_pursuit", decision="approve",
            coordinate=other.coordinate, gate_digest=other.gate.gate_digest,
            source_preimage_ref=document.document_ref, actor_ref="identity:human-one",
            action_occurrence_ref="actor-action-occurrence:sha256:" + "1" * 64,
            policy_ref="goal-phase-approval-policy:sha256:" + "2" * 64, policy_digest="sha256:" + "3" * 64,
            idempotency_key="approval-one", delta_ref="goal-phase-delta:sha256:" + "4" * 64,
            event_ref="goal-phase-event:sha256:" + "5" * 64)
        document = GoalPhaseNativeDocumentV3(goal_tag=document.goal_tag,
            compatibility_projection_sha256=document.compatibility_projection_sha256,
            compatibility_projection_byte_count=document.compatibility_projection_byte_count,
            definitions=document.definitions, operational_bundle=document.operational_bundle,
            unresolved_dependencies=document.unresolved_dependencies, source_refs=document.source_refs,
            execution_authority=document.execution_authority,
            phase_operation_journal=GoalPhaseOperationJournalV1((entry,)))
    request = GoalPhaseOperationalAdmissionRequestV2(coordinate=definition.coordinate,
        expected_document_ref=document.document_ref, expected_source_revision_ref="object-revision:one",
        expected_definition_ref=definition.definition_ref, expected_gate_digest=definition.gate.gate_digest,
        initial_state=GoalLanePhaseState.PLANNED, issue_ref="issue:implementation-one",
        work_role=GoalLanePhaseWorkRole.IMPLEMENTATION, admitted_at="2026-10-01T12:00:00Z",
        evidence_refs=("evidence:explicit-preparation",), idempotency_key="admit-one")
    return document, request


@pytest.mark.parametrize("journal", [False, True])
@pytest.mark.parametrize("state", [GoalLanePhaseState.PLANNED, GoalLanePhaseState.ACTIVE])
def test_plan_preserves_carrier_and_admits_only_canonical_preparation(journal, state):
    document, request = source_and_request(journal=journal)
    request = replace(request, initial_state=state)
    plan = plan_existing_definition_admission(document=document, request=request)
    after = plan.after_document
    assert type(after) is type(document)
    assert replace(after, operational_bundle=document.operational_bundle) == document
    assert after.definitions == document.definitions
    assert plan.phase.state is state and plan.phase.gate_observations == ()
    assert plan.phase.last_receipt_ref is None
    assert len(plan.phase.work_associations) == 1
    assert plan.phase.work_associations[0].issue_ref == request.issue_ref
    assert forward_plan_wire(plan)["effect_profile"] == "plan_only_non_authorizing"
    if journal:
        assert after.phase_operation_journal == document.phase_operation_journal


@pytest.mark.parametrize("state", [GoalLanePhaseState.HELD, GoalLanePhaseState.ACCEPTED, GoalLanePhaseState.WITHDRAWN, "active"])
def test_initial_states_do_not_claim_hold_or_acceptance(state):
    _, request = source_and_request()
    with pytest.raises((ValueError, TypeError)):
        replace(request, initial_state=state)


@pytest.mark.parametrize("fault", ["unknown", "number", "boolean", "duplicate", "gate", "ref", "date"])
def test_strict_request_wire(fault):
    _, request = source_and_request()
    wire = request.to_wire()
    if fault == "unknown": wire["desired_phase"] = {}
    elif fault == "number": wire["issue_ref"] = 5
    elif fault == "boolean": wire["evidence_refs"] = [True]
    elif fault == "duplicate": wire["evidence_refs"] = ["evidence:one", "evidence:one"]
    elif fault == "gate": wire["expected_gate_digest"] = "sha256:invalid"
    elif fault == "ref": wire["request_ref"] = "goal-phase-operational-admission-request:sha256:" + "e" * 64
    else: wire["admitted_at"] = "2026-02-31T12:00:00Z"
    with pytest.raises((ValueError, TypeError)):
        decode_forward_admission_request(wire)


@pytest.mark.parametrize("fault", ["incomplete", "wrong_gate", "wrong_definition", "already_operational", "mutation"])
def test_invalid_postimages_and_existing_authority_refuse(fault):
    document, request = source_and_request()
    if fault == "incomplete":
        document = replace(document, definitions=(replace(document.definitions[0], title=None),))
        request = replace(request, expected_document_ref=document.document_ref,
            expected_definition_ref=document.definitions[0].definition_ref)
    elif fault == "wrong_gate": request = replace(request, expected_gate_digest="sha256:" + "e" * 64)
    elif fault == "wrong_definition": request = replace(request, expected_definition_ref="goal-phase-definition:sha256:" + "e" * 64)
    elif fault == "already_operational":
        plan = plan_existing_definition_admission(document=document, request=request)
        document = plan.after_document
        request = replace(request, expected_document_ref=document.document_ref)
    else:
        plan = plan_existing_definition_admission(document=document, request=request)
        object.__setattr__(plan.phase, "state", GoalLanePhaseState.ACCEPTED)
        with pytest.raises(ValueError):
            forward_plan_wire(plan)
        return
    with pytest.raises(ValueError):
        plan_existing_definition_admission(document=document, request=request)


def test_plan_detaches_caller_request_and_accepts_object_revision_coordinates():
    document, request = source_and_request()
    plan = plan_existing_definition_admission(document=document, request=request)
    object.__setattr__(request, "issue_ref", "issue:foreign")
    assert plan.request.issue_ref == "issue:implementation-one"
    assert plan.request.expected_source_revision_ref == "object-revision:one"
    assert forward_plan_wire(plan)["semantic_intent_ref"] == plan.semantic_intent_ref


@pytest.mark.parametrize("field", ["issue_ref", "expected_source_revision_ref", "idempotency_key", "evidence_refs"])
def test_request_constructor_does_not_normalize_noncanonical_text(field):
    _, request = source_and_request()
    value = (" evidence:one ",) if field == "evidence_refs" else " token:one "
    with pytest.raises(ValueError, match="canonical text"):
        replace(request, **{field: value})


@pytest.mark.parametrize("journal", [False, True])
def test_forward_plan_wire_rejects_mutated_request_ref_without_repair(journal):
    document, request = source_and_request(journal=journal)
    plan = plan_existing_definition_admission(document=document, request=request)
    original_intent = plan.semantic_intent_ref
    mutated_ref = "goal-phase-operational-admission-request:sha256:" + "e" * 64
    object.__setattr__(plan.request, "request_ref", mutated_ref)
    for _ in range(2):
        with pytest.raises(ValueError, match="forward_admission_request_reference_invalid"):
            forward_plan_wire(plan)
        assert plan.request.request_ref == mutated_ref
        assert plan.semantic_intent_ref == original_intent
