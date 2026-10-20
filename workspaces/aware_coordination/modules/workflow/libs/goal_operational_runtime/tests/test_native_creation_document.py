"""Genesis structural reading, never authentic creation or journal issuance."""

import hashlib
import json
from dataclasses import replace

import pytest

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.native_creation_claims import GENESIS_SCHEMA, NativeCreationClaimError
from aware_goal_operational_runtime.native_creation_execution_authority import (
    GoalPhaseExecutionAuthorityV2, decode_goal_genesis_execution_authority,
)
from aware_goal_operational_runtime.phase_contracts import (
    GoalLanePhase, GoalLanePhaseGate, GoalLanePhaseState, GoalPhaseContractBundleV1, GoalPhaseCoordinate,
)
from aware_goal_operational_runtime.phase_document import (
    GoalLanePhaseDefinitionV1, GoalPhaseExecutionAuthorityV1, GoalPhaseNativeDocumentError,
    GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4,
    GoalPhaseOperationJournalEntryV1, GoalPhaseOperationJournalV1,
    GoalNativeLaneAuthorityV1,
    attach_goal_phase_native_carrier, extract_goal_phase_native_carrier,
    decode_goal_phase_native_document, encode_goal_phase_native_document,
    _decode_execution_authority,  # pyright: ignore[reportPrivateUsage]
)
from aware_goal_operational_runtime.phase_document_v5 import decode_goal_phase_native_document_v5
from aware_goal_operational_runtime.phase_native_lane_introduction import plan_goal_native_lane_introduction

COMPATIBILITY=b"# Goal: Customer Goal\n\n- Status: Proposed\n- Owner: object:owner:1\n"
GOAL="goal/2026-10-04/customer-goal"


def ref(domain,value):
    return domain+fingerprint({"fixture":value})


def genesis():
    return GoalPhaseExecutionAuthorityV2(creation_intent_ref=ref("goal-native-creation-intent:","intent"))


def base():
    definition=GoalLanePhaseDefinitionV1(
        coordinate=GoalPhaseCoordinate(goal_tag=GOAL,lane_key="runtime",phase_key="first"),
        ordinal=1,title="Authored first Phase",intent="Retain explicit Gate direction.",
        gate=GoalLanePhaseGate(gate_key="review",promise="Publish reviewed evidence.",
                              gate_contract_ref="contract:review-v1",evidence_schema_ref="evidence:review-v1"),
    )
    return dict(goal_tag=GOAL,compatibility_projection_sha256="sha256:"+hashlib.sha256(COMPATIBILITY).hexdigest(),
                compatibility_projection_byte_count=len(COMPATIBILITY),definitions=(definition,),
                operational_bundle=GoalPhaseContractBundleV1(phases=(),dependencies=()),
                unresolved_dependencies=(),source_refs=(),execution_authority=genesis())


def v3():
    fields=base()
    definition=fields["definitions"][0]
    fields["operational_bundle"]=GoalPhaseContractBundleV1(phases=(GoalLanePhase(
        coordinate=definition.coordinate,title=definition.title,ordinal=1,intent=definition.intent,
        state=GoalLanePhaseState.ACTIVE,gate=definition.gate,
    ),),dependencies=())
    entry=GoalPhaseOperationJournalEntryV1(
        operation_kind="approve_pursuit",decision="approve",coordinate=definition.coordinate,
        gate_digest=definition.gate.gate_digest,source_preimage_ref=ref("goal-phase-document:","source"),
        actor_ref="object:actor:1",action_occurrence_ref=ref("actor-action-occurrence:","action"),
        policy_ref=ref("goal-policy:","policy"),policy_digest=fingerprint({"fixture":"policy"}),
        idempotency_key="approval-fixture",delta_ref=ref("goal-delta:","delta"),event_ref=ref("goal-event:","event"),
    )
    return GoalPhaseNativeDocumentV3(**fields,phase_operation_journal=GoalPhaseOperationJournalV1(entries=(entry,)))


def redigest_document(body):
    body=dict(body)
    body["document_ref"]="goal-phase-document:"+fingerprint({k:v for k,v in body.items() if k!="document_ref"})
    return json.dumps(body).encode()


@pytest.mark.parametrize("document",[GoalPhaseNativeDocumentV2(**base()),v3()])
def test_v2_v3_exact_structural_round_trip_and_compatibility_carriage(document):
    payload=encode_goal_phase_native_document(document)
    restored=decode_goal_phase_native_document(payload)
    assert restored==document
    assert encode_goal_phase_native_document(restored)==payload
    carrier=attach_goal_phase_native_carrier(COMPATIBILITY,document)
    extracted=extract_goal_phase_native_carrier(carrier)
    assert extracted[0]==COMPATIBILITY
    assert encode_goal_phase_native_document(extracted[1])==payload
    assert json.loads(payload)["execution_authority"]["schema_id"]==GENESIS_SCHEMA
    assert not hasattr(restored.execution_authority,"verifier_token")
    if type(document) is GoalPhaseNativeDocumentV3:
        assert restored.phase_operation_journal==document.phase_operation_journal


def test_genesis_and_retirement_are_distinct_with_unchanged_legacy_wire():
    old=GoalPhaseExecutionAuthorityV1(
        source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
        parity_ref=ref("goal-phase-native-compatibility-parity:","parity"),
        proposal_aggregate_ref=ref("goal-phase-native-operational-bootstrap-proposal:","proposal"),
        coordinator_acceptance_ref=ref("goal-phase-native-operational-bootstrap-coordinator-acceptance:","acceptance"),
    )
    fields=base()
    fields["execution_authority"]=old
    wire=json.loads(encode_goal_phase_native_document(GoalPhaseNativeDocumentV2(**fields)))
    assert _decode_execution_authority(wire["execution_authority"])==old
    assert wire["execution_authority"]["legacy_execution_disposition"]=="retired"
    assert "creation_intent_ref" not in wire["execution_authority"]
    assert "parity_ref" not in genesis().to_wire()


def test_migration_only_reader_refuses_genesis_without_explicit_opt_in():
    with pytest.raises(GoalPhaseNativeDocumentError,match="explicit reader profile"):
        _decode_execution_authority(genesis().to_wire())
    assert _decode_execution_authority(genesis().to_wire(),allow_genesis=True)==genesis()


@pytest.mark.parametrize("field,value",[
    ("origin_profile","legacy"),("legacy_execution_disposition","retired"),
    ("target_execution_authority_profile","legacy_goal_lane_row_v1"),
    ("creation_intent_ref","uncommitted"),("schema_id","unknown"),
    ("parity_ref","fake"),("creation_intent_ref",True),
])
def test_redigested_nested_profile_substitution_refuses(field,value):
    body=json.loads(encode_goal_phase_native_document(GoalPhaseNativeDocumentV2(**base())))
    authority=dict(body["execution_authority"],**{field:value})
    authority["authority_ref"]="goal-phase-execution-authority:"+fingerprint({k:v for k,v in authority.items() if k!="authority_ref"})
    body["execution_authority"]=authority
    with pytest.raises(ValueError): decode_goal_phase_native_document(redigest_document(body))


@pytest.mark.parametrize("field,value",[
    ("authority_ref","foreign"),("creation_intent_ref",ref("goal-native-creation-intent:","foreign")),
    ("schema_id","unknown"),
])
def test_encoding_rejects_mutated_actual_genesis_record_without_repair(field,value):
    document=GoalPhaseNativeDocumentV2(**base())
    object.__setattr__(document.execution_authority,field,value)
    with pytest.raises(NativeCreationClaimError): encode_goal_phase_native_document(document)
    assert getattr(document.execution_authority,field)==value


def test_unknown_type_and_stripped_genesis_refuse():
    fields=base()
    fields["execution_authority"]=genesis().to_wire()
    with pytest.raises(TypeError): GoalPhaseNativeDocumentV2(**fields)
    document=GoalPhaseNativeDocumentV2(**base())
    body=json.loads(encode_goal_phase_native_document(document))
    del body["execution_authority"]["creation_intent_ref"]
    with pytest.raises(ValueError): decode_goal_phase_native_document(redigest_document(body))


def test_v4_and_v5_refuse_genesis_instead_of_inheriting_internal_v2_support():
    fields=base()
    with pytest.raises(GoalPhaseNativeDocumentError,match="V4 genesis"):
        GoalPhaseNativeDocumentV4(**fields,native_lane_authorities=(),operation_journal_profile="none")
    body=json.loads(encode_goal_phase_native_document(GoalPhaseNativeDocumentV2(**fields)))
    body.update(schema_id="aware.goal.lane-phase.document.v4",native_lane_authorities=[],operation_journal_profile="none")
    with pytest.raises(GoalPhaseNativeDocumentError): decode_goal_phase_native_document(redigest_document(body))
    body.update(schema_id="aware.goal.lane-phase.document.v5",acceptance_provenance_profile="aware.goal.acceptance-provenance.v2",
                acceptance_qualifications=[],acceptance_dependency_policies=[])
    with pytest.raises(ValueError,match="v5_genesis_provenance_unsupported"):
        decode_goal_phase_native_document_v5(redigest_document(body))


def test_genesis_constructor_and_decoder_keep_exact_claim_identity():
    value=genesis()
    assert decode_goal_genesis_execution_authority(json.dumps(value.to_wire()))==value
    assert replace(value).authority_ref==value.authority_ref
    with pytest.raises(NativeCreationClaimError): replace(value,legacy_execution_disposition="retired")


def test_v4_lane_introduction_refuses_genesis_before_building_a_target():
    source=attach_goal_phase_native_carrier(COMPATIBILITY,GoalPhaseNativeDocumentV2(**base()))
    lane=GoalNativeLaneAuthorityV1(goal_tag=GOAL,lane_key="runtime",role="implementation",
                                  owner_profile="provider_execution_v1",owner_ref="codex-fixture",
                                  operational_state="ready",state_detail=None,hold_authority_refs=(),
                                  current_work_association_ref=None)
    with pytest.raises(ValueError,match="native_lane_introduction_genesis_profile_unsupported"):
        plan_goal_native_lane_introduction(candidate=source,lane=lane,represented_lane_keys=())
    assert extract_goal_phase_native_carrier(source)[0]==COMPATIBILITY
