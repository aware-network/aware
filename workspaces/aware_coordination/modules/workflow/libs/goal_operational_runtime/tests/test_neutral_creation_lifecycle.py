"""Lifecycle wire/consistency proofs, never durable or issued evidence."""

import copy
import hashlib
import json

import pytest

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.native_creation_request import encode_native_goal_creation_request
from aware_goal_operational_runtime.neutral_creation_lifecycle import (
    PENDING_SCHEMA, REJECTION_SCHEMA, COMPLETION_SCHEMA,
    NeutralCreationLifecycleError, NeutralCreationLifecycleClaim,
    make_neutral_creation_lifecycle_claim, decode_neutral_creation_lifecycle_claim,
    encode_neutral_creation_lifecycle_claim, creation_body_content_ref,
    check_creation_pending_claim, check_creation_completion_claim, check_creation_rejection_request_claim,
)
from test_native_creation_plan import fixture as git_fixture
from test_neutral_creation_contracts import decision


def pending(dec=None):
    dec = dec or decision()
    body = dec.to_wire()
    request, auth = body["request"], body["authority_input"]
    return make_neutral_creation_lifecycle_claim(PENDING_SCHEMA, dict(
        operation_ref="object:operation:1", request_ref=request["request_ref"], idempotency_key=request["idempotency_key"],
        namespace_ref=auth["namespace_ref"], target_locator_ref=auth["target_locator_ref"],
        provider_ref=auth["provider_ref"], provider_generation_ref=auth["provider_generation_ref"],
        authority_profile_ref=auth["authority_profile_ref"], decision_ref=body["decision_ref"],
        semantic_state_ref=body["semantic_state"]["semantic_state_ref"], owner_ref=request["owner_ref"],
        owner_recovery_head_ref="object:recovery-head:1", expected_owner_revision_ref="object:owner-revision:1",
        original_provider_recovery_ref="object:original-recovery:1",
        request_body_ref=creation_body_content_ref(request), decision_body_ref=creation_body_content_ref(body),
    ))


def completion(status="applied", dec=None, pend=None):
    dec = dec or decision()
    pend = pend or pending(dec)
    d, p = dec.to_wire(), pend.to_wire()
    fields = {field:p[field] for field in ("operation_ref", "request_ref", "decision_ref", "semantic_state_ref",
        "provider_ref", "provider_generation_ref", "authority_profile_ref", "namespace_ref", "target_locator_ref")}
    fields.update(intent_ref=d["intent"]["intent_ref"], genesis_ref=d["genesis"]["authority_ref"],
                  before_namespace_revision_ref=d["authority_input"]["namespace_revision_ref"],
                  after_namespace_revision_ref="object:after-revision:1" if status=="applied" else None,
                  publication_effect_ref="object:unverified-effect:1" if status=="applied" else None,
                  effect_evidence_ref="object:unverified-evidence:1" if status=="applied" else None,
                  recovery_ref=p["original_provider_recovery_ref"] if status=="uncertain" else None,
                  effect_status=status, reason_code={"applied":"none", "unapplied":"source_stale", "uncertain":"recovery_required"}[status])
    return make_neutral_creation_lifecycle_claim(COMPLETION_SCHEMA, fields)


def rejection(payload=None, *, invalid=False, provider=None):
    provider = not invalid if provider is None else provider
    payload = (b"{bad json}" if invalid else encode_native_goal_creation_request(git_fixture()[0]).encode()) if payload is None else payload
    return make_neutral_creation_lifecycle_claim(REJECTION_SCHEMA, dict(
        operation_ref="object:operation:1", request_fingerprint="sha256:" + hashlib.sha256(payload).hexdigest(),
        request_ref=None if invalid else git_fixture()[0].request_ref,
        provider_ref="object:provider:1" if provider else None,
        provider_generation_ref="object:generation:1" if provider else None,
        reason_code="invalid_request" if invalid else "permission_refused",
    ))


def changed(claim, **changes):
    body = claim.to_wire()
    schema = body.pop("schema_id")
    ref_field = {PENDING_SCHEMA:"pending_operation_ref", REJECTION_SCHEMA:"rejection_ref", COMPLETION_SCHEMA:"completion_ref"}[schema]
    del body[ref_field]
    return make_neutral_creation_lifecycle_claim(schema, dict(body, **changes))


def redigest(body):
    body = copy.deepcopy(body)
    field, domain = {PENDING_SCHEMA:("pending_operation_ref","goal-creation-pending-operation:"),
        REJECTION_SCHEMA:("rejection_ref","goal-creation-rejection:"),
        COMPLETION_SCHEMA:("completion_ref","goal-creation-completion:")}[body["schema_id"]]
    body[field] = domain + fingerprint({k:v for k,v in body.items() if k!=field})
    return json.dumps(body)


@pytest.mark.parametrize("value", [pending(), completion(), completion("unapplied"), completion("uncertain"),
                                    rejection(), rejection(invalid=True), rejection(provider=True)])
def test_round_trip_and_detachment_confer_no_authority(value):
    restored = decode_neutral_creation_lifecycle_claim(encode_neutral_creation_lifecycle_claim(value))
    assert restored == value
    detached = restored.to_wire()
    detached["schema_id"] = "foreign"
    assert restored.to_wire()["schema_id"] != "foreign"
    for attr in ("persist", "dispatch", "require_verified", "live_handle", "verifier_token", "recover"):
        assert not hasattr(restored, attr)


@pytest.mark.parametrize("status", ["applied", "unapplied", "uncertain"])
def test_complete_structural_join_preserves_status_without_verifying_it(status):
    dec = decision()
    pend = pending(dec)
    result = completion(status, dec, pend)
    check_creation_pending_claim(pend, dec)
    check_creation_completion_claim(result, pend, dec)
    assert result.to_wire()["effect_status"] == status


@pytest.mark.parametrize("field", [
    "operation_ref", "idempotency_key", "namespace_ref", "target_locator_ref", "provider_ref", "provider_generation_ref",
    "authority_profile_ref", "owner_ref", "owner_recovery_head_ref", "expected_owner_revision_ref", "original_provider_recovery_ref",
])
@pytest.mark.parametrize("bad", [None, True, 1, [], {}, "", " padded ", "\ud800"])
def test_pending_fields_are_exact_text(field,bad):
    body = pending().to_wire()
    body[field] = bad
    with pytest.raises(NeutralCreationLifecycleError):
        decode_neutral_creation_lifecycle_claim(redigest(body))


@pytest.mark.parametrize("field,domain", [
    ("request_ref","goal-native-creation-request:"), ("decision_ref","goal-creation-decision:"),
    ("semantic_state_ref","goal-creation-semantic-state:"), ("request_body_ref","content:"), ("decision_body_ref","content:"),
])
def test_canonical_foreign_content_identity_refuses_join(field,domain):
    wrong = changed(pending(), **{field:domain + "sha256:" + "0"*64})
    with pytest.raises(NeutralCreationLifecycleError, match="pending_decision_join"):
        check_creation_pending_claim(wrong, decision())


@pytest.mark.parametrize("field", ["idempotency_key", "namespace_ref", "target_locator_ref", "provider_ref",
                                  "provider_generation_ref", "authority_profile_ref", "owner_ref"])
def test_canonical_pending_substitution_refuses(field):
    wrong = changed(pending(), **{field:"object:foreign"})
    with pytest.raises(NeutralCreationLifecycleError):
        check_creation_pending_claim(wrong, decision())


@pytest.mark.parametrize("field,value", [
    ("operation_ref","object:foreign"), ("provider_ref","object:foreign"),
    ("provider_generation_ref","object:foreign"), ("authority_profile_ref","object:foreign"),
    ("namespace_ref","object:foreign"), ("target_locator_ref","object:foreign"),
    ("request_ref","goal-native-creation-request:sha256:" + "0"*64),
    ("decision_ref","goal-creation-decision:sha256:" + "0"*64),
    ("semantic_state_ref","goal-creation-semantic-state:sha256:" + "0"*64),
    ("intent_ref","goal-native-creation-intent:sha256:" + "0"*64),
    ("genesis_ref","goal-phase-execution-authority:sha256:" + "0"*64),
    ("before_namespace_revision_ref","object:foreign"), ("recovery_ref","object:foreign"),
])
def test_canonical_completion_substitution_refuses(field,value):
    wrong = changed(completion("uncertain"), **{field:value})
    with pytest.raises(NeutralCreationLifecycleError):
        check_creation_completion_claim(wrong, pending(), decision())


@pytest.mark.parametrize("status,field,bad", [
    ("applied","reason_code","source_stale"), ("applied","after_namespace_revision_ref",None),
    ("applied","publication_effect_ref",None), ("applied","effect_evidence_ref",None),
    ("unapplied","reason_code","none"), ("unapplied","reason_code","invalid_request"),
    ("unapplied","after_namespace_revision_ref","object:after"), ("unapplied","publication_effect_ref","object:effect"),
    ("unapplied","effect_evidence_ref","object:evidence"), ("unapplied","recovery_ref","object:recovery"),
    ("uncertain","recovery_ref",None), ("uncertain","reason_code","none"),
    ("uncertain","reason_code","source_stale"), ("applied","effect_status","running"),
    ("applied","effect_status",True), ("applied","reason_code",True),
    ("applied","publication_effect_ref",True), ("uncertain","recovery_ref",False),
])
def test_redigested_contradictory_completion_refuses(status,field,bad):
    body = completion(status).to_wire()
    body[field] = bad
    with pytest.raises(NeutralCreationLifecycleError):
        decode_neutral_creation_lifecycle_claim(redigest(body))


@pytest.mark.parametrize("mask", range(8))
def test_uncertain_preserves_partial_coordinates_without_asserting_effect(mask):
    fields = ("after_namespace_revision_ref", "publication_effect_ref", "effect_evidence_ref")
    updates = {field: "object:known-but-unverified:"+field for i,field in enumerate(fields) if mask & (1 << i)}
    value = changed(completion("uncertain"), **updates)
    check_creation_completion_claim(value, pending(), decision())
    assert value.to_wire()["effect_status"] == "uncertain"
    for field, expected in updates.items():
        assert value.to_wire()[field] == expected


@pytest.mark.parametrize("field,bad", [
    ("provider_ref", None), ("provider_generation_ref", None),
    ("reason_code", "running"), ("request_ref", None), ("reason_code", "invalid_request"),
    ("request_fingerprint", "object:claim"),
])
def test_redigested_rejection_contradictions_refuse(field,bad):
    body = rejection().to_wire()
    body[field] = bad
    with pytest.raises(NeutralCreationLifecycleError):
        decode_neutral_creation_lifecycle_claim(redigest(body))


@pytest.mark.parametrize("reason", ["permission_refused", "identity_present", "source_stale",
    "authority_unavailable", "concurrency_unavailable", "concurrency_lost", "cancelled_before_effect"])
def test_provider_dependent_rejection_requires_provenance_pair(reason):
    body = rejection().to_wire()
    body.update(reason_code=reason, provider_ref=None, provider_generation_ref=None)
    fields = {key: value for key, value in body.items() if key not in {"schema_id", "rejection_ref"}}
    with pytest.raises(NeutralCreationLifecycleError, match="creation_rejection_provider_reason"):
        make_neutral_creation_lifecycle_claim(REJECTION_SCHEMA, fields)
    with pytest.raises(NeutralCreationLifecycleError, match="creation_rejection_provider_reason"):
        decode_neutral_creation_lifecycle_claim(redigest(body))
    qualified_claim = changed(rejection(), reason_code=reason)
    check_creation_rejection_request_claim(qualified_claim, encode_native_goal_creation_request(git_fixture()[0]).encode())


@pytest.mark.parametrize("payload", [b"{bad json}", b"\xff", b"null", b"{}"])
def test_invalid_input_preserves_exact_fingerprint_without_request_identity(payload):
    claim = rejection(payload, invalid=True)
    check_creation_rejection_request_claim(claim, payload)
    assert claim.to_wire()["request_ref"] is None
    with pytest.raises(NeutralCreationLifecycleError):
        check_creation_rejection_request_claim(claim, payload+b" ")


def test_valid_input_rejection_exact_bytes_and_wrong_classification_refuse():
    payload = encode_native_goal_creation_request(git_fixture()[0]).encode()
    check_creation_rejection_request_claim(rejection(payload), payload)
    with pytest.raises(NeutralCreationLifecycleError):
        check_creation_rejection_request_claim(rejection(payload, invalid=True), payload)
    with pytest.raises(NeutralCreationLifecycleError):
        check_creation_rejection_request_claim(rejection(), b"{bad json}")
    with pytest.raises(NeutralCreationLifecycleError):
        check_creation_rejection_request_claim(changed(rejection(payload), request_ref="goal-native-creation-request:sha256:"+"0"*64), payload)


@pytest.mark.parametrize("value,field", [(pending(),"pending_operation_ref"), (rejection(),"rejection_ref"), (completion(),"completion_ref")])
def test_actual_object_mutation_refuses_without_repair(value,field):
    body = value.to_wire()
    body[field] = "bad"
    raw = json.dumps(body)
    object.__setattr__(value, "canonical_body", raw)
    with pytest.raises(NeutralCreationLifecycleError):
        encode_neutral_creation_lifecycle_claim(value)
    assert value.canonical_body == raw


@pytest.mark.parametrize("value", [pending(), rejection(), completion()])
def test_extra_missing_duplicates_constructor_and_digest_refuse(value):
    body = value.to_wire()
    body["persisted"] = True
    with pytest.raises(NeutralCreationLifecycleError):
        decode_neutral_creation_lifecycle_claim(redigest(body))
    body = value.to_wire()
    del body["operation_ref"]
    with pytest.raises(NeutralCreationLifecycleError):
        decode_neutral_creation_lifecycle_claim(redigest(body))
    raw = encode_neutral_creation_lifecycle_claim(value)
    raw = raw.replace('"operation_ref":"object:operation:1"', '"operation_ref":"object:operation:1","operation_ref":"object:operation:1"')
    with pytest.raises(NeutralCreationLifecycleError):
        NeutralCreationLifecycleClaim(raw)
    with pytest.raises(NeutralCreationLifecycleError):
        decode_neutral_creation_lifecycle_claim(encode_neutral_creation_lifecycle_claim(value), expected_schema="foreign")


@pytest.mark.parametrize("payload", [None, True, 1, [], "null", "[]", "{}", "{bad json}"])
def test_malformed_payload_refuses(payload):
    with pytest.raises(NeutralCreationLifecycleError):
        decode_neutral_creation_lifecycle_claim(payload)
