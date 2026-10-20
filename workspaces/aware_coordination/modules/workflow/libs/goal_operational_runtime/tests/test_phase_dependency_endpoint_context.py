from dataclasses import replace
from copy import deepcopy

import pytest

from aware_goal_operational_runtime import GoalGlobalDirectionAuthorityV1, GoalLaneDirectionAuthorityV1
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_dependency_endpoint_context import (
    derive_dependency_endpoint_context, derive_absent_lane_endpoint_context, decode_dependency_endpoint_context,
    dependency_endpoint_scope_profile,
)
from aware_goal_operational_runtime.phase_forward_admission import plan_existing_definition_admission
from test_phase_forward_admission import source_and_request


def context_inputs(*, journal=False, operational=False):
    document, request = source_and_request(journal=journal)
    if operational:
        document = plan_existing_definition_admission(document=document, request=request).after_document
    coordinate = request.coordinate
    issue = {"path": request.issue_ref, "tag": "issue-tag:one", "blob_oid": "a" * 40,
        "owner": "codex-one", "status": "in_progress", "scope": ("source/one.py",),
        "scope_digest": fingerprint({"ownership_scope": ["source/one.py"]})}
    global_authority = GoalGlobalDirectionAuthorityV1(goal_tag=document.goal_tag, lifecycle_status="active",
        owner_ref="codex-one", governance_authority_refs=("governance:one",), hold_state="clear",
        hold_authority_refs=(), execution_authority_ref=document.execution_authority.authority_ref,
        compatibility_guard_ref="guard:one", source_revision_ref="object-revision:one",
        projector_ref="projector:fixture", projection_receipt_ref="projection:fixture")
    lane = GoalLaneDirectionAuthorityV1(goal_tag=document.goal_tag, lane_key=coordinate.lane_key,
        role="Runtime", owner_ref="codex-one", operational_state="active", state_detail=None,
        blocker_authority_refs=(), current_issue_ref=request.issue_ref, current_issue_authority_ref="issue-authority:one",
        compatibility_guard_ref="guard:one", source_revision_ref="object-revision:one",
        projector_ref="projector:fixture", projection_receipt_ref="projection:fixture")
    return dict(document=document, coordinate=coordinate, global_authority=global_authority,
        lane_authority=lane, issues=(issue,), source_revision_ref="object-revision:one")


@pytest.mark.parametrize("journal", [False, True])
def test_definition_only_issue_is_context_not_phase_work(journal):
    inputs = context_inputs(journal=journal)
    context = derive_dependency_endpoint_context(**inputs)
    assert context["endpoint_profile"] == "definition_only_v1"
    assert context["phase"] is None
    assert context["gate_authority_profile"] == "not_evaluated"
    assert context["lane_issue_context"][0]["status"] == "in_progress"
    assert context["effect_profile"] == "source_context_only_non_authorizing"
    assert context["phase_operation_entries"] == []  # unrelated-lane journal is excluded


def test_operational_endpoint_keeps_exact_phase_and_current_work():
    context = derive_dependency_endpoint_context(**context_inputs(operational=True))
    assert context["endpoint_profile"] == "operational_v1"
    assert len(context["phase"]["work_associations"]) == 1


@pytest.mark.parametrize("fault", ["omitted", "extra", "foreign_owner", "source", "scope", "closed_work"])
def test_context_inputs_are_complete_and_consistent(fault):
    inputs = context_inputs(operational=(fault == "closed_work"))
    issue = inputs["issues"][0]
    if fault == "omitted": inputs["issues"] = ()
    elif fault == "extra": inputs["issues"] = (issue, {**issue, "path": "issue:foreign"})
    elif fault == "foreign_owner": inputs["issues"] = ({**issue, "owner": "codex-foreign"},)
    elif fault == "source": inputs["source_revision_ref"] = "object-revision:other"
    elif fault == "scope": inputs["issues"] = ({**issue, "scope": ("source/two.py",)},)
    else: inputs["issues"] = ({**issue, "status": "closed"},)
    with pytest.raises(ValueError):
        derive_dependency_endpoint_context(**inputs)


def test_closed_lane_context_does_not_invent_work_or_satisfaction():
    inputs = context_inputs()
    issue = inputs["issues"][0]
    inputs["issues"] = ({**issue, "status": "closed"},)
    inputs["lane_authority"] = replace(inputs["lane_authority"], operational_state="complete")
    context = derive_dependency_endpoint_context(**inputs)
    assert context["phase"] is None and context["gate_authority_profile"] == "not_evaluated"


def redigest(context):
    for name, domain in (("goal_global", "goal-global-direction:"), ("lane", "goal-lane-direction:")):
        authority = context[name]
        if authority is not None:
            authority["authority_ref"] = domain + fingerprint({k: v for k, v in authority.items() if k != "authority_ref"})
    context["context_ref"] = "goal-dependency-endpoint-context:" + fingerprint({k: v for k, v in context.items() if k != "context_ref"})
    return context


@pytest.mark.parametrize("journal", [False, True])
@pytest.mark.parametrize("operational", [False, True])
def test_strict_context_roundtrip_is_detached_and_provider_neutral(journal, operational):
    context = derive_dependency_endpoint_context(**context_inputs(journal=journal, operational=operational))
    decoded = decode_dependency_endpoint_context(context)
    assert decoded == context and decoded is not context
    assert decoded["source_revision_ref"] == "object-revision:one"
    decoded["lane"]["role"] = "Different role"
    assert context["lane"]["role"] == "Runtime"


@pytest.mark.parametrize("fault", [
    "global_extra", "global_refs_boolean", "global_lifecycle", "global_ref", "global_hold",
    "lane_extra", "lane_running", "lane_qualified", "lane_issue_pair", "lane_source", "lane_hold",
    "issues_boolean", "issue_extra", "issue_owner_boolean", "issue_status", "issue_scope_type", "issue_scope_duplicate", "issue_digest",
    "entries_string", "definition_extra", "definition_ordinal", "definition_gate", "phase_extra", "phase_state", "phase_role", "phase_definition",
    "profile", "gate_profile", "document_ref",
])
def test_strict_context_refuses_redigested_nested_contract_substitutions(fault):
    context = deepcopy(derive_dependency_endpoint_context(**context_inputs(operational=True)))
    if fault == "global_extra": context["goal_global"]["caller_current"] = True
    elif fault == "global_refs_boolean": context["goal_global"]["governance_authority_refs"] = [True]
    elif fault == "global_lifecycle": context["goal_global"]["lifecycle_status"] = "running"
    elif fault == "global_ref": context["goal_global"]["owner_ref"] = True
    elif fault == "global_hold": context["goal_global"]["hold_state"] = "held"
    elif fault == "lane_extra": context["lane"]["extra"] = True
    elif fault == "lane_running": context["lane"]["operational_state"] = "running"
    elif fault == "lane_qualified": context["lane"]["qualification"] = "ambiguous"
    elif fault == "lane_issue_pair": context["lane"]["current_issue_authority_ref"] = None
    elif fault == "lane_source": context["lane"]["source_revision_ref"] = "object-revision:other"
    elif fault == "lane_hold": context["lane"]["operational_state"] = "held"
    elif fault == "issues_boolean": context["lane_issue_context"] = True
    elif fault.startswith("issue_"):
        issue = context["lane_issue_context"][0]
        if fault == "issue_extra": issue["extra"] = True
        elif fault == "issue_owner_boolean": issue["owner"] = True
        elif fault == "issue_status": issue["status"] = "running"
        elif fault == "issue_scope_type": issue["scope"] = "source/one.py"
        elif fault == "issue_scope_duplicate":
            issue["scope"] *= 2
            issue["scope_digest"] = fingerprint({"ownership_scope": issue["scope"]})
        else: issue["scope_digest"] = "sha256:" + "f" * 64
    elif fault == "entries_string": context["phase_operation_entries"] = "not-an-array"
    elif fault == "definition_extra": context["definition"]["extra"] = True
    elif fault == "definition_ordinal": context["definition"]["ordinal"] = True
    elif fault == "definition_gate": context["definition"]["gate"]["extra"] = True
    elif fault == "phase_extra": context["phase"]["extra"] = True
    elif fault == "phase_state": context["phase"]["state"] = "running"
    elif fault == "phase_role": context["phase"]["work_associations"][0]["role"] = "foreign"
    elif fault == "phase_definition": context["phase"]["title"] = "Not the definition title"
    elif fault == "profile": context["endpoint_profile"] = "definition_only_v1"
    elif fault == "gate_profile": context["gate_authority_profile"] = "qualified"
    else: context["document_ref"] = "goal-phase-document:made-up"
    with pytest.raises((ValueError, TypeError)):
        decode_dependency_endpoint_context(redigest(context))


def journal_context():
    from aware_goal_operational_runtime import GoalPhaseOperationJournalV1
    inputs = context_inputs(journal=True, operational=True)
    document = inputs["document"]
    approval = replace(document.phase_operation_journal.entries[0], coordinate=inputs["coordinate"],
        gate_digest=document.definitions[0].gate.gate_digest, source_preimage_ref=document.document_ref)
    revocation = replace(approval, decision="revoke", approval_entry_ref=approval.entry_ref,
        action_occurrence_ref="actor-action-occurrence:sha256:" + "9" * 64, idempotency_key="revoke-one")
    inputs["document"] = replace(document, phase_operation_journal=GoalPhaseOperationJournalV1((approval, revocation)))
    return derive_dependency_endpoint_context(**inputs)


def test_strict_context_retains_scoped_journal_sequence():
    context = journal_context()
    assert len(context["phase_operation_entries"]) == 2
    assert decode_dependency_endpoint_context(context) == context


@pytest.mark.parametrize("fault", ["unknown", "actor_boolean", "ref", "reverse", "none_profile", "gate", "foreign_coordinate"])
def test_strict_context_refuses_redigested_journal_substitutions(fault):
    context = journal_context()
    entry = context["phase_operation_entries"][0]
    if fault == "unknown": entry["extra"] = True
    elif fault == "actor_boolean": entry["actor_ref"] = True
    elif fault == "ref": entry["entry_ref"] = "goal-phase-operation-journal-entry:sha256:" + "f" * 64
    elif fault == "reverse": context["phase_operation_entries"].reverse()
    elif fault == "none_profile": context["operation_journal_profile"] = "none"
    else:
        for item in context["phase_operation_entries"]:
            if fault == "gate": item["gate_digest"] = "sha256:" + "f" * 64
            else: item["coordinate"]["phase_key"] = "foreign"
            if item["decision"] == "revoke": item["approval_entry_ref"] = entry["entry_ref"]
            item["entry_ref"] = "goal-phase-operation-journal-entry:" + fingerprint({k: v for k, v in item.items() if k != "entry_ref"})
    with pytest.raises((ValueError, TypeError)):
        decode_dependency_endpoint_context(redigest(context))


def absent_inputs(*, journal=False, operational=True):
    inputs = context_inputs(journal=journal, operational=operational)
    inputs.pop("lane_authority")
    if not operational:
        inputs["issues"] = ()
    return inputs


@pytest.mark.parametrize("journal", [False, True])
@pytest.mark.parametrize("operational", [False, True])
def test_absent_lane_context_retains_exact_facts_without_qualification(journal, operational):
    inputs = absent_inputs(journal=journal, operational=operational)
    # A resolved Issue owner is a fact, not a fabricated lane owner.
    inputs["issues"] = tuple({**issue, "owner": "codex-foundation"} for issue in inputs["issues"])
    context = derive_absent_lane_endpoint_context(**inputs)
    assert context["schema_id"] == "aware.goal.dependency-endpoint-context.v3"
    assert context["lane"] is None and context["lane_authority_profile"] == "absent_native_only_v1"
    assert context["lane_authority_reason"] == "lane_authority_absent"
    assert context["gate_authority_profile"] == "not_evaluated"
    assert context["effect_profile"] == "source_context_only_non_authorizing"
    assert bool(context["phase"]) is operational
    assert decode_dependency_endpoint_context(context) == context
    record = {"evaluation_profile": "source_context_only_non_authorizing",
        "dependent": {"context": derive_dependency_endpoint_context(**context_inputs())},
        "prerequisite": {"context": context}}
    assert dependency_endpoint_scope_profile((record,)) == "dependency_endpoint_context_v3"
    assert dependency_endpoint_scope_profile(()) == "dependency_endpoint_context_v2"


@pytest.mark.parametrize("fault", ["omitted", "extra", "closed", "scope"])
def test_absent_lane_projection_still_requires_complete_current_work_issue_facts(fault):
    inputs = absent_inputs()
    issue = inputs["issues"][0]
    if fault == "omitted": inputs["issues"] = ()
    elif fault == "extra": inputs["issues"] = (issue, {**issue, "path": "issue:foreign"})
    elif fault == "closed": inputs["issues"] = ({**issue, "status": "closed"},)
    else: inputs["issues"] = ({**issue, "scope": ("different.py",)},)
    with pytest.raises(ValueError):
        derive_absent_lane_endpoint_context(**inputs)


@pytest.mark.parametrize("fault", ["lane", "qualified", "reason", "scope_profile", "schema", "extra", "issues", "missing_work", "closed_work", "gate", "journal"])
def test_redigested_absent_context_substitutions_refuse(fault):
    context = derive_absent_lane_endpoint_context(**absent_inputs())
    if fault == "lane": context["lane"] = context_inputs()["lane_authority"].to_wire()
    elif fault == "qualified": context["lane_authority_profile"] = "qualified"
    elif fault == "reason": context["lane_authority_reason"] = "eligible"
    elif fault == "scope_profile": context["scope_profile"] = "dependency_endpoint_context_v2"
    elif fault == "schema": context["schema_id"] = "aware.goal.dependency-endpoint-context.v2"
    elif fault == "extra": context["eligible"] = True
    elif fault == "issues": context["lane_issue_context"] = True
    elif fault == "missing_work": context["lane_issue_context"] = []
    elif fault == "closed_work": context["lane_issue_context"][0]["status"] = "closed"
    elif fault == "gate": context["gate_authority_profile"] = "satisfied"
    else: context["phase_operation_entries"] = "approval"
    with pytest.raises((ValueError, TypeError)):
        decode_dependency_endpoint_context(redigest(context))
