"""Claims only: fixtures provide no actor, acceptance or dependency authority."""

import hashlib
import json

import pytest

from aware_goal_operational_runtime.dependencies import GoalDependencyRelation
from aware_goal_operational_runtime.phase_contracts import GoalPhaseCoordinate, GoalPhaseDependency
from aware_goal_operational_runtime.phase_frontier import goal_phase_dependency_digest

from aware_goal_operational_runtime.phase_acceptance_provenance import (
    BASELINE_POLICY, LEGACY_PROFILE, OWNER_PROFILE, PROVEN_PROFILE,
    POLICY_SCHEMA, QUALIFICATION_SCHEMA, AcceptanceProvenanceClaimV2,
    AcceptanceProvenanceError, decode_acceptance_provenance_v2,
    encode_acceptance_provenance_v2, make_acceptance_provenance_claim_v2,
)


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return "sha256:" + hashlib.sha256(wire(value).encode()).hexdigest()


def ref(domain, value):
    return domain + digest(value)


def coordinate(phase="portal", goal="goal/2026-10-03/example"):
    return {"goal_tag": goal, "lane_key": "runtime", "phase_key": phase}


def qualification(mode="owner_attested", kind="acceptance"):
    return make_acceptance_provenance_claim_v2(QUALIFICATION_SCHEMA, {
        "coordinate": coordinate(), "definition_ref": ref("goal-phase-definition:", "definition"),
        "gate_digest": digest("gate"), "evidence_kind": kind,
        "evidence_ref": ref("goal-phase-acceptance:", "accepted") if kind == "acceptance" else "object:observation:1",
        "evidence_source_epoch": {"provider_binding_ref": "object:repository:1", "source_revision": "object:revision:original",
                                  "document_ref": ref("goal-phase-document:", "original"), "goal_sha256": digest("goal")},
        "mode": mode, "profile": {"owner_attested": OWNER_PROFILE, "evaluator_proven": PROVEN_PROFILE,
                                  "legacy_unqualified": LEGACY_PROFILE}[mode],
        "authority_refs": [] if mode == "legacy_unqualified" else ["object:authority:1"],
        "evidence_refs": [] if mode == "legacy_unqualified" else ["object:evidence:1"],
        "decision_ref": ref("goal-owner-phase-acceptance-decision:", "decision") if mode == "owner_attested" else None,
        "profile_authorization_ref": ref("goal-owner-phase-acceptance-authorization:", "grant") if mode == "owner_attested" else None,
    })


def policy(modes=None):
    declaration = {"owner_goal_tag": coordinate()["goal_tag"], "dependency_key": "requires_portal",
                   "dependent": coordinate("consumer"), "prerequisite": coordinate(goal="goal/2026-10-03/prerequisite"),
                   "required_gate_digest": digest("gate"), "relation": "requires_acceptance",
                   "reason": "Requires accepted portal.", "evidence_refs": []}
    return make_acceptance_provenance_claim_v2(POLICY_SCHEMA, {
        "declaration": declaration, "declaration_digest": canonical_declaration_digest(declaration),
        "required_modes": ["evaluator_proven"] if modes is None else modes,
        "authority_profile": "versioned_baseline" if modes is None else "dependent_goal_authorized",
        "policy_authority_ref": BASELINE_POLICY if modes is None else ref("goal-acceptance-dependency-policy-authorization:", "grant"),
    })


def canonical_declaration_digest(declaration):
    return goal_phase_dependency_digest(GoalPhaseDependency(
        owner_goal_tag=declaration["owner_goal_tag"], dependency_key=declaration["dependency_key"],
        dependent=GoalPhaseCoordinate(**declaration["dependent"]),
        prerequisite=GoalPhaseCoordinate(**declaration["prerequisite"]),
        required_gate_digest=declaration["required_gate_digest"],
        relation=GoalDependencyRelation(declaration["relation"]), reason=declaration["reason"],
        evidence_refs=tuple(declaration["evidence_refs"]),
    ))


def test_existing_canonical_dependency_digest_is_retained_unchanged():
    original = policy().to_wire()
    existing_digest = canonical_declaration_digest(original["declaration"])
    assert original["declaration_digest"] == existing_digest
    restored = decode_acceptance_provenance_v2(redigest(original))
    assert restored.to_wire()["declaration_digest"] == existing_digest
    assert existing_digest != digest(original["declaration"])
    bare = restored.to_wire()
    bare["declaration_digest"] = digest(bare["declaration"])
    with pytest.raises(AcceptanceProvenanceError, match="provenance_declaration_digest"):
        decode_acceptance_provenance_v2(redigest(bare))


def redigest(body):
    field, domain = ("qualification_ref", "goal-acceptance-qualification:") if body["schema_id"] == QUALIFICATION_SCHEMA else (
        "policy_ref", "goal-acceptance-dependency-policy:")
    body[field] = ref(domain, {key: value for key, value in body.items() if key != field})
    return wire(body)


def mutate(body, path, value):
    target = body
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


@pytest.mark.parametrize("mode", ["owner_attested", "evaluator_proven", "legacy_unqualified"])
@pytest.mark.parametrize("kind", ["acceptance", "gate_observation"])
def test_round_trip_preserves_mode_and_original_epoch_without_issuing_authority(mode, kind):
    claim = qualification(mode, kind)
    restored = decode_acceptance_provenance_v2(encode_acceptance_provenance_v2(claim).encode())
    assert restored.to_wire() == claim.to_wire()
    assert restored.to_wire()["mode"] == mode
    assert restored.to_wire()["evidence_source_epoch"]["source_revision"] == "object:revision:original"
    assert not hasattr(restored, "verifier_token")
    assert not hasattr(restored, "eligibility")
    detached = restored.to_wire()
    detached["coordinate"]["phase_key"] = "changed"
    assert restored.to_wire() == claim.to_wire()


@pytest.mark.parametrize("path,value", [
    (("mode",), "running"), (("mode",), True), (("profile",), PROVEN_PROFILE),
    (("coordinate", "phase_key"), "Bad_Key"), (("coordinate", "goal_tag"), "goal://2026-10-03/example"),
    (("coordinate", "extra"), "x"), (("definition_ref",), "definition:fake"),
    (("gate_digest",), "sha256:" + "a" * 40), (("evidence_kind",), "approved"),
    (("evidence_ref",), "object:foreign"), (("evidence_source_epoch", "current"), True),
    (("evidence_source_epoch", "source_revision"), False), (("evidence_source_epoch", "goal_sha256"), "SHA256:x"),
    (("authority_refs",), []), (("authority_refs",), ["z", "a"]), (("authority_refs",), ["a", "a"]),
    (("evidence_refs",), [1]), (("decision_ref",), None), (("profile_authorization_ref",), "grant:foreign"),
    (("passed",), True),
])
def test_redigested_qualification_substitution_refuses(path, value):
    body = qualification().to_wire()
    mutate(body, path, value)
    with pytest.raises(AcceptanceProvenanceError):
        decode_acceptance_provenance_v2(redigest(body))


@pytest.mark.parametrize("mode", ["legacy_unqualified", "evaluator_proven"])
@pytest.mark.parametrize("field", ["decision_ref", "profile_authorization_ref"])
def test_non_owner_modes_cannot_carry_attestation_fields(mode, field):
    body = qualification(mode).to_wire()
    body[field] = qualification().to_wire()[field]
    with pytest.raises(AcceptanceProvenanceError):
        decode_acceptance_provenance_v2(redigest(body))


@pytest.mark.parametrize("field", ["authority_refs", "evidence_refs"])
def test_legacy_claim_cannot_promote_authority(field):
    body = qualification("legacy_unqualified").to_wire()
    body[field] = ["authority:claimed"]
    with pytest.raises(AcceptanceProvenanceError, match="legacy_promotion"):
        decode_acceptance_provenance_v2(redigest(body))


@pytest.mark.parametrize("modes", [None, ["owner_attested"], ["evaluator_proven", "owner_attested"]])
def test_policy_preserves_exact_declaration_mode_pairs_without_permission(modes):
    claim = policy(modes)
    assert decode_acceptance_provenance_v2(encode_acceptance_provenance_v2(claim)).to_wire() == claim.to_wire()
    assert claim.to_wire()["required_modes"] == (["evaluator_proven"] if modes is None else modes)
    assert not hasattr(claim, "verifier_token")


@pytest.mark.parametrize("path,value", [
    (("required_modes",), []), (("required_modes",), ["legacy_unqualified"]),
    (("required_modes",), ["owner_attested"]), (("required_modes",), [True]),
    (("required_modes",), ["evaluator_proven", "evaluator_proven"]),
    (("authority_profile",), "untrusted"), (("policy_authority_ref",), "grant:foreign"),
    (("declaration_digest",), digest("foreign")), (("declaration", "relation"), "requires_completion"),
    (("declaration", "owner_goal_tag"), "goal/2026-10-03/foreign"),
    (("declaration", "dependent", "phase_key"), "foreign"),
    (("declaration", "required_gate_digest"), digest("foreign")),
    (("declaration", "reason"), " trimmed "), (("declaration", "evidence_refs"), [True]),
    (("declaration", "extra"), "unknown"), (("policy",), "extra"),
])
def test_redigested_policy_substitution_refuses(path, value):
    body = policy().to_wire()
    mutate(body, path, value)
    with pytest.raises(AcceptanceProvenanceError):
        decode_acceptance_provenance_v2(redigest(body))


@pytest.mark.parametrize("claim", [qualification(), policy()])
def test_postconstruction_mutation_and_noncanonical_storage_refuse_without_repair(claim):
    original = claim.canonical_body
    body = claim.to_wire()
    field = "qualification_ref" if body["schema_id"] == QUALIFICATION_SCHEMA else "policy_ref"
    body[field] = ref("foreign:", "mutated")
    changed = wire(body)
    object.__setattr__(claim, "canonical_body", changed)
    with pytest.raises(AcceptanceProvenanceError):
        encode_acceptance_provenance_v2(claim)
    assert claim.canonical_body == changed
    with pytest.raises(AcceptanceProvenanceError, match="canonical"):
        AcceptanceProvenanceClaimV2(json.dumps(json.loads(original), indent=2))


@pytest.mark.parametrize("data", [b"\xff", "[]", "{", '{"schema_id":"a","schema_id":"b"}',
                                  '{"schema_id":"a","nested":{"a":1,"a":2}}', '{"schema_id":NaN}'])
def test_invalid_json_and_duplicate_nested_fields_refuse(data):
    with pytest.raises(AcceptanceProvenanceError):
        decode_acceptance_provenance_v2(data)


def test_fabricated_but_consistent_claim_is_not_authenticated():
    body = qualification().to_wire()
    body["authority_refs"] = ["object:authority:invented"]
    body["decision_ref"] = ref("goal-owner-phase-acceptance-decision:", "invented")
    claimed = decode_acceptance_provenance_v2(redigest(body))
    assert claimed.to_wire() == body
    assert not hasattr(claimed, "currentness")
    # Concrete owner-action verifiers MUST refuse these fabricated claims.
