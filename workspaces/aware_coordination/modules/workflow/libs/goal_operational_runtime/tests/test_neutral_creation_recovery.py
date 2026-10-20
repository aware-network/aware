"""Claim-only conformance; no durable backend or terminal-proof issuer."""

import copy
import json

import pytest

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.neutral_creation_lifecycle import (
    make_neutral_creation_lifecycle_claim, creation_body_content_ref,
)
from aware_goal_operational_runtime.neutral_creation_recovery import (
    RECOVERY_SCHEMA, DISPATCH_SCHEMA, SETTLEMENT_SCHEMA, WITNESS_SCHEMA,
    NeutralCreationRecoveryError, NeutralCreationRecoveryClaim,
    make_neutral_creation_recovery_claim, decode_neutral_creation_recovery_claim,
    encode_neutral_creation_recovery_claim, check_creation_recovery_coordinate_claim,
    check_creation_dispatch_claim, check_creation_settlement_claim, check_creation_durability_witness_claim,
)
from test_neutral_creation_contracts import decision
from test_neutral_creation_lifecycle import pending, completion


REFS = {RECOVERY_SCHEMA:("recovery_coordinate_ref", "goal-creation-recovery-coordinate:"),
    DISPATCH_SCHEMA:("dispatch_claim_ref", "goal-creation-dispatch-claim:"),
    SETTLEMENT_SCHEMA:("settlement_record_ref", "goal-creation-settlement-record:"),
    WITNESS_SCHEMA:("durability_witness_ref", "goal-creation-durability-witness:")}


def make(schema, body):
    return make_neutral_creation_recovery_claim(schema, body)


def change(value, **updates):
    body = value.to_wire()
    schema = body.pop("schema_id")
    del body[REFS[schema][0]]
    return make(schema, dict(body, **updates))


def lifecycle_change(value, **updates):
    body = value.to_wire()
    schema = body.pop("schema_id")
    del body["pending_operation_ref"]
    return make_neutral_creation_lifecycle_claim(schema, dict(body, **updates))


def redigest(body):
    body = copy.deepcopy(body)
    ref, domain = REFS[body["schema_id"]]
    body[ref] = domain + fingerprint({key: item for key, item in body.items() if key != ref})
    return json.dumps(body)


def witness(record, kind, after):
    body = record.to_wire()
    ref = {"pending":"pending_operation_ref", "dispatch":"dispatch_claim_ref", "settlement":"settlement_record_ref"}[kind]
    return make(WITNESS_SCHEMA, dict(
        record_kind=kind, record_ref=body[ref], record_body_ref=creation_body_content_ref(body),
        operation_ref=body["operation_ref"], owner_ref=body["owner_ref"], owner_recovery_head_ref=body["owner_recovery_head_ref"],
        before_owner_revision_ref=body["expected_owner_revision_ref"], after_owner_revision_ref=after,
        persistence_provider_ref="fixture:store", persistence_generation_ref="fixture:generation",
        durability_profile_ref="fixture:unadmitted-profile", durability_evidence_ref="fixture:unverified-write",
        reread_evidence_ref="fixture:unverified-reread"))


def fixture(status="applied"):
    dec = decision()
    pend = pending(dec)
    p = pend.to_wire()
    coord = make(RECOVERY_SCHEMA, dict(
        {key:p[key] for key in ("operation_ref", "request_ref", "idempotency_key", "namespace_ref", "target_locator_ref",
            "owner_ref", "provider_ref", "provider_generation_ref", "authority_profile_ref")},
        query_binding_ref="fixture:query", issuance_evidence_ref="fixture:unverified-issuance"))
    pend = lifecycle_change(pend, original_provider_recovery_ref=coord.reference)
    pw = witness(pend, "pending", "fixture:revision:2")
    p = pend.to_wire()
    fields = {key:p[key] for key in ("operation_ref", "owner_ref", "owner_recovery_head_ref", "provider_ref",
        "provider_generation_ref", "original_provider_recovery_ref")}
    fields.update(pending_operation_ref=pend.reference, pending_body_ref=creation_body_content_ref(p),
        expected_owner_revision_ref=pw.to_wire()["after_owner_revision_ref"])
    disp = make(DISPATCH_SCHEMA, fields)
    dw = witness(disp, "dispatch", "fixture:revision:3")
    comp = completion(status, dec, pend)
    settle = make(SETTLEMENT_SCHEMA, dict(fields, expected_owner_revision_ref=dw.to_wire()["after_owner_revision_ref"],
        completion_ref=comp.reference, completion_body_ref=creation_body_content_ref(comp.to_wire()),
        effect_verification_ref="fixture:unverified-effect-or-terminal-proof"))
    return dec, pend, coord, pw, disp, dw, comp, settle


F = fixture()
CLAIMS = [F[2], F[3], F[4], F[5], F[7], witness(F[7], "settlement", "fixture:revision:4")]


@pytest.mark.parametrize("claim", CLAIMS)
def test_round_trip_detached_non_authorizing(claim):
    restored = decode_neutral_creation_recovery_claim(encode_neutral_creation_recovery_claim(claim))
    assert restored == claim
    body = restored.to_wire()
    body["operation_ref"] = "foreign:operation"
    assert restored.to_wire()["operation_ref"] != body["operation_ref"]
    for name in ("dispatch", "persist", "prevent", "require_verified", "verifier_token", "recover"):
        assert not hasattr(restored, name)


@pytest.mark.parametrize("status", ["applied", "unapplied"])
def test_complete_consistency_joins_never_qualify_authority(status):
    dec, pend, coord, pw, disp, dw, comp, settle = fixture(status)
    check_creation_recovery_coordinate_claim(coord, pend, dec)
    check_creation_durability_witness_claim(pw, pend)
    check_creation_dispatch_claim(disp, pend, dec, coord, pw)
    check_creation_settlement_claim(settle, comp, disp, dw, pend, dec, coord, pw)
    check_creation_durability_witness_claim(witness(settle, "settlement", "fixture:revision:4"), settle)
    # Even a structurally joined unapplied claim has no authority to retry.
    assert not hasattr(settle, "retry")


def test_nonterminal_completion_cannot_join_settlement():
    dec, pend, coord, pw, disp, dw, comp, settle = fixture("uncertain")
    with pytest.raises(NeutralCreationRecoveryError, match="nonterminal"):
        check_creation_settlement_claim(settle, comp, disp, dw, pend, dec, coord, pw)


@pytest.mark.parametrize("field", ["operation_ref", "request_ref", "idempotency_key", "namespace_ref", "target_locator_ref",
    "owner_ref", "provider_ref", "provider_generation_ref", "authority_profile_ref"])
def test_redigested_coordinate_substitution_refuses(field):
    dec, pend, coord, *_ = fixture()
    bad = "goal-native-creation-request:sha256:" + "0"*64 if field == "request_ref" else "foreign:binding"
    with pytest.raises(NeutralCreationRecoveryError, match="join"):
        check_creation_recovery_coordinate_claim(change(coord, **{field:bad}), pend, dec)


@pytest.mark.parametrize("field", ["operation_ref", "pending_operation_ref", "pending_body_ref", "owner_ref",
    "owner_recovery_head_ref", "expected_owner_revision_ref", "provider_ref", "provider_generation_ref", "original_provider_recovery_ref"])
def test_redigested_dispatch_substitution_refuses(field):
    dec, pend, coord, pw, disp, *_ = fixture()
    domain = {"pending_operation_ref":"goal-creation-pending-operation:", "pending_body_ref":"content:"}.get(field)
    bad = domain + "sha256:" + "0"*64 if domain else "foreign:binding"
    with pytest.raises(NeutralCreationRecoveryError, match="join"):
        check_creation_dispatch_claim(change(disp, **{field:bad}), pend, dec, coord, pw)


@pytest.mark.parametrize("field", ["operation_ref", "pending_operation_ref", "pending_body_ref", "owner_ref",
    "owner_recovery_head_ref", "expected_owner_revision_ref", "provider_ref", "provider_generation_ref",
    "original_provider_recovery_ref", "completion_ref", "completion_body_ref"])
def test_redigested_settlement_substitution_refuses(field):
    dec, pend, coord, pw, disp, dw, comp, settle = fixture()
    domain = {"pending_operation_ref":"goal-creation-pending-operation:", "pending_body_ref":"content:",
        "completion_ref":"goal-creation-completion:", "completion_body_ref":"content:"}.get(field)
    bad = domain + "sha256:" + "0"*64 if domain else "foreign:binding"
    with pytest.raises(NeutralCreationRecoveryError, match="join"):
        check_creation_settlement_claim(change(settle, **{field:bad}), comp, disp, dw, pend, dec, coord, pw)


@pytest.mark.parametrize("kind,record", [("pending", F[1]), ("dispatch", F[4]), ("settlement", F[7])])
@pytest.mark.parametrize("field", ["record_ref", "record_body_ref", "operation_ref", "owner_ref", "owner_recovery_head_ref", "before_owner_revision_ref"])
def test_redigested_witness_substitution_refuses(kind, record, field):
    value = witness(record, kind, "fixture:revision:final")
    bad = value.to_wire()[field]
    bad = bad[:-1] + ("0" if bad[-1] != "0" else "1") if field in {"record_ref", "record_body_ref"} else "foreign:binding"
    with pytest.raises(NeutralCreationRecoveryError, match="join"):
        check_creation_durability_witness_claim(change(value, **{field:bad}), record)


@pytest.mark.parametrize("claim", CLAIMS)
@pytest.mark.parametrize("bad", [None, True, 0, [], {}, "", " ", "bad\x00token", "bad|token"])
def test_constructor_and_redigested_decoding_reject_bad_tokens(claim, bad):
    body = claim.to_wire()
    body["operation_ref"] = bad
    fields = {key:item for key,item in body.items() if key not in {"schema_id", REFS[body["schema_id"]][0]}}
    with pytest.raises(NeutralCreationRecoveryError):
        make(body["schema_id"], fields)
    with pytest.raises(NeutralCreationRecoveryError):
        decode_neutral_creation_recovery_claim(redigest(body))


@pytest.mark.parametrize("kind", ["running", "unapplied", "uncertain", "", True])
def test_unknown_witness_kind_refuses(kind):
    body = F[3].to_wire()
    body["record_kind"] = kind
    with pytest.raises(NeutralCreationRecoveryError):
        decode_neutral_creation_recovery_claim(redigest(body))


def test_wrong_kind_domain_and_no_revision_advance_refuse():
    for update in ({"record_kind":"dispatch"}, {"after_owner_revision_ref":F[3].to_wire()["before_owner_revision_ref"]}):
        with pytest.raises(NeutralCreationRecoveryError):
            change(F[3], **update)


@pytest.mark.parametrize("claim", CLAIMS)
def test_fields_duplicates_wrong_schema_and_actual_mutation_refuse(claim):
    for body in (dict(claim.to_wire(), foreign=True), {key:value for key,value in claim.to_wire().items() if key != "owner_ref"}):
        with pytest.raises(NeutralCreationRecoveryError):
            decode_neutral_creation_recovery_claim(redigest(body))
    encoded = encode_neutral_creation_recovery_claim(claim)
    with pytest.raises(NeutralCreationRecoveryError):
        decode_neutral_creation_recovery_claim(encoded[:-1]+',"operation_ref":"foreign"}')
    with pytest.raises(NeutralCreationRecoveryError):
        decode_neutral_creation_recovery_claim(encoded, expected_schema="foreign")
    mutated = copy.copy(claim)
    body = mutated.to_wire()
    body["operation_ref"] = "foreign"
    object.__setattr__(mutated, "canonical_body", json.dumps(body))
    before = mutated.canonical_body
    with pytest.raises(NeutralCreationRecoveryError):
        encode_neutral_creation_recovery_claim(mutated)
    assert mutated.canonical_body == before


@pytest.mark.parametrize("payload", [None, b"{}", "null", "[]", "{}", "{bad json}"])
def test_invalid_payload_refuses(payload):
    with pytest.raises(NeutralCreationRecoveryError):
        decode_neutral_creation_recovery_claim(payload)


def test_wrong_witness_record_and_mutated_existing_pending_refuse():
    dec, pend, coord, pw, disp, dw, *_ = fixture()
    with pytest.raises(ValueError):
        check_creation_durability_witness_claim(dw, pend)
    p = pend.to_wire()
    p["operation_ref"] = "foreign"
    object.__setattr__(pend, "canonical_body", json.dumps(p))
    with pytest.raises(ValueError):
        check_creation_dispatch_claim(disp, pend, dec, coord, pw)


def test_recovery_coordinate_mismatch_is_not_repaired():
    dec, pend, coord, *_ = fixture()
    altered = lifecycle_change(pend, original_provider_recovery_ref="foreign:query")
    with pytest.raises(NeutralCreationRecoveryError, match="coordinate_join"):
        check_creation_recovery_coordinate_claim(coord, altered, dec)
