"""No fixture is issued owner, action, evidence or publication authority."""

import json

import pytest

from aware_goal_operational_runtime.phase_acceptance_provenance import OWNER_PROFILE
from aware_goal_operational_runtime.phase_owner_attestation import (
    AUTHORIZATION_SCHEMA, DECISION_SCHEMA, OBLIGATIONS, EVIDENCE_ROLES,
    OwnerAttestationClaimV2, OwnerAttestationCodecError,
    check_owner_attestation_claim_pair_v2, decode_owner_attestation_v2,
    encode_owner_attestation_v2, make_owner_attestation_claim_v2,
)
from aware_goal_operational_runtime.identity import fingerprint


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def ref(domain, value):
    return domain + fingerprint(value)


def common():
    return {
        "coordinate": {"goal_tag": "goal/2026-10-03/example", "lane_key": "runtime", "phase_key": "portal"},
        "definition_ref": ref("goal-phase-definition:", "definition"), "gate_digest": fingerprint("gate"),
        "source_epoch": {"provider_binding_ref": "object:repository:1", "source_revision": "object:revision:source",
                         "document_ref": ref("goal-phase-document:", "source"), "goal_sha256": fingerprint("source")},
        "profile": OWNER_PROFILE, "owner_actor_ref": "identity:actor-one", "owner_execution_id": "codex-execution-one",
        "owner_authority_ref": "object:owner-authority:1", "issued_at": "2026-10-03T00:00:00Z",
        "action_occurrence_ref": ref("actor-action-occurrence:", "authorization-action"),
    }


def grant():
    return make_owner_attestation_claim_v2(AUTHORIZATION_SCHEMA, dict(
        common(), promise_interpretation="unchanged_gate_attestation",
        obligation_keys=list(OBLIGATIONS), evidence_roles=list(EVIDENCE_ROLES),
    ))


def decision(verdict="accept", *, limitation=False):
    inventory = [{"evidence_ref": "evidence:" + role, "role": role,
                  "content_identity": {"content_ref": "object:content:" + role, "sha256": fingerprint(role), "byte_count": 42},
                  "source_epoch": {"provider_binding_ref": "object:evidence-provider:1", "source_revision": "object:historical:1"},
                  "publication_authority_ref": "object:publication:" + role} for role in EVIDENCE_ROLES]
    return make_owner_attestation_claim_v2(DECISION_SCHEMA, dict(
        common(), authorization_ref=grant().reference, verdict=verdict,
        action_occurrence_ref=ref("actor-action-occurrence:", "decision-action"), issued_at="2026-10-03T01:00:00Z",
        evidence_inventory=inventory,
        obligations=[{"key": key, "attestation": "met" if verdict == "accept" else "not_met",
                      "evidence_refs": ["evidence:implementation"]} for key in OBLIGATIONS],
        limitations=([{"key": "disclosed-failure", "description": "Failure retained outside the unchanged promise.",
                       "evidence_refs": ["evidence:implementation"], "disposition": "outside_gate",
                       "rationale": "Review explicitly distinguishes the invariant boundary.",
                       "review_evidence_ref": "evidence:independent_review"}] if limitation else []),
    ))


def redigest(body):
    field, domain = (("authorization_ref", "goal-owner-phase-acceptance-authorization:")
                     if body["schema_id"] == AUTHORIZATION_SCHEMA else ("decision_ref", "goal-owner-phase-acceptance-decision:"))
    body[field] = ref(domain, {key: value for key, value in body.items() if key != field})
    return wire(body)


def mutate(body, path, value):
    current = body
    for key in path[:-1]: current = current[key]
    current[path[-1]] = value


@pytest.mark.parametrize("value", [grant(), decision(), decision("decline"), decision(limitation=True)])
def test_round_trip_is_not_an_issued_action_or_accepted_gate(value):
    restored = decode_owner_attestation_v2(encode_owner_attestation_v2(value))
    assert restored.to_wire() == value.to_wire()
    assert not hasattr(restored, "verifier_token")
    assert not hasattr(restored, "outcome")
    assert not hasattr(restored, "currentness")
    detached = restored.to_wire()
    detached["owner_actor_ref"] = "identity:foreign"
    assert restored.to_wire() == value.to_wire()


def test_pure_pair_does_not_authenticate_the_owner_or_independent_review():
    assert check_owner_attestation_claim_pair_v2(grant(), decision()) is None
    assert decision().to_wire()["evidence_inventory"][0]["source_epoch"]["source_revision"] == "object:historical:1"


@pytest.mark.parametrize("path,value", [
    (("profile",), "evaluator_proven"), (("owner_execution_id",), "alias"), (("owner_actor_ref",), True),
    (("owner_authority_ref",), None), (("issued_at",), "2026-02-31T00:00:00Z"),
    (("issued_at",), "2026-10-03"), (("action_occurrence_ref",), "action:fake"),
    (("source_epoch", "current"), True), (("source_epoch", "source_revision"), 1),
    (("verdict",), "satisfied"), (("obligations", 0, "attestation"), "passed"),
    (("obligations", 0, "attestation"), "unavailable"), (("obligations", 0, "evidence_refs"), []),
    (("obligations", 0, "evidence_refs"), ["foreign:evidence"]),
    (("evidence_inventory", 0, "role"), "issue_closed"),
    (("evidence_inventory", 0, "content_identity", "byte_count"), True),
    (("evidence_inventory", 0, "source_epoch", "current"), True),
    (("evidence_inventory", 0, "publication_authority_ref"), False),
    (("coordinate", "extra"), "foreign"), (("gate_digest",), "sha256:" + "a" * 40),
    (("decision",), "foreign"),
])
def test_redigested_decision_transport_substitutions_refuse(path, value):
    body = decision().to_wire()
    mutate(body, path, value)
    with pytest.raises(OwnerAttestationCodecError):
        decode_owner_attestation_v2(redigest(body))


@pytest.mark.parametrize("fault", ["missing-obligation", "extra-obligation", "duplicate-obligation", "order-obligation",
                                    "missing-review", "duplicate-evidence", "order-evidence"])
def test_complete_claimed_coverage_and_pairing_refuse(fault):
    body = decision().to_wire()
    if fault == "missing-obligation": body["obligations"].pop()
    elif fault == "extra-obligation": body["obligations"].append(dict(body["obligations"][0], key="extra"))
    elif fault == "duplicate-obligation": body["obligations"][1] = body["obligations"][0]
    elif fault == "order-obligation": body["obligations"].reverse()
    elif fault == "missing-review": body["evidence_inventory"].pop()
    elif fault == "duplicate-evidence": body["evidence_inventory"].append(body["evidence_inventory"][0])
    else: body["evidence_inventory"].reverse()
    with pytest.raises(OwnerAttestationCodecError):
        decode_owner_attestation_v2(redigest(body))


@pytest.mark.parametrize("field,value", [("disposition", "waived"), ("disposition", "in_scope_blocker"),
                                        ("review_evidence_ref", "evidence:implementation"), ("rationale", ""),
                                        ("description", True), ("evidence_refs", ["evidence:foreign"])])
def test_disclosed_limitation_contradictions_refuse(field, value):
    body = decision(limitation=True).to_wire()
    body["limitations"][0][field] = value
    with pytest.raises(OwnerAttestationCodecError):
        decode_owner_attestation_v2(redigest(body))


def test_decline_preserves_failure_and_unavailable_instead_of_discarding_evidence():
    body = decision("decline").to_wire()
    body["obligations"][0]["attestation"] = "unavailable"
    body["obligations"][0]["evidence_refs"] = []
    restored = decode_owner_attestation_v2(redigest(body))
    assert restored.to_wire()["verdict"] == "decline"
    assert restored.to_wire()["obligations"][0]["attestation"] == "unavailable"
    assert restored.to_wire()["obligations"][1]["attestation"] == "not_met"


@pytest.mark.parametrize("field,value", [("promise_interpretation", "waive_gate"), ("obligation_keys", []),
                                        ("evidence_roles", ["implementation"]), ("delegation", "allowed")])
def test_authorization_cannot_weaken_the_promised_profile(field, value):
    body = grant().to_wire()
    body[field] = value
    with pytest.raises(OwnerAttestationCodecError):
        decode_owner_attestation_v2(redigest(body))


@pytest.mark.parametrize("field,value", [("owner_actor_ref", "identity:foreign"), ("owner_execution_id", "codex-foreign"),
                                        ("gate_digest", fingerprint("foreign")), ("owner_authority_ref", "authority:foreign"),
                                        ("issued_at", "2026-10-02T00:00:00Z"),
                                        ("action_occurrence_ref", common()["action_occurrence_ref"])])
def test_pair_revalidates_exact_owner_target_and_distinct_action_order(field, value):
    body = decision().to_wire()
    body[field] = value
    substituted = decode_owner_attestation_v2(redigest(body))
    with pytest.raises(OwnerAttestationCodecError):
        check_owner_attestation_claim_pair_v2(grant(), substituted)


def test_mutated_storage_refuses_without_repair_and_fake_consistent_pair_stays_a_claim():
    value = decision()
    body = value.to_wire()
    body["decision_ref"] = ref("goal-owner-phase-acceptance-decision:", "foreign")
    changed = wire(body)
    object.__setattr__(value, "canonical_body", changed)
    with pytest.raises(OwnerAttestationCodecError): encode_owner_attestation_v2(value)
    assert value.canonical_body == changed
    with pytest.raises(OwnerAttestationCodecError, match="canonical"):
        OwnerAttestationClaimV2(json.dumps(grant().to_wire(), indent=2))
    authorization = grant().to_wire()
    authorization["owner_authority_ref"] = "object:invented-owner"
    fake_grant = decode_owner_attestation_v2(redigest(authorization))
    body = decision().to_wire()
    body["owner_authority_ref"] = "object:invented-owner"
    body["authorization_ref"] = fake_grant.reference
    fake_decision = decode_owner_attestation_v2(redigest(body))
    assert check_owner_attestation_claim_pair_v2(fake_grant, fake_decision) is None
    assert not hasattr(fake_decision, "verifier_token")


@pytest.mark.parametrize("payload", [b"\xff", b"[]", b'{"schema_id":"a","schema_id":"b"}', b'{"x":NaN}'])
def test_invalid_json_refuses(payload):
    with pytest.raises(OwnerAttestationCodecError): decode_owner_attestation_v2(payload)
