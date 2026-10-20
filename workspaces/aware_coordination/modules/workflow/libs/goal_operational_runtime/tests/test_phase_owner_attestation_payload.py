"""Complete projections and real Identity transport limits, not issuer proofs."""

import importlib
import json
from pathlib import Path

import pytest

from aware_goal_operational_runtime.phase_owner_attestation import (
    AUTHORIZATION_SCHEMA, DECISION_SCHEMA, OwnerAttestationCodecError,
    make_owner_attestation_claim_v2,
)
from aware_goal_operational_runtime.phase_owner_attestation_payload import (
    PAYLOAD_SCHEMA, OwnerAttestationActionPayloadV2,
    make_owner_attestation_action_payload_v2, project_owner_attestation_action_payload_v2,
    encode_owner_attestation_action_payload_v2, decode_owner_attestation_action_payload_v2,
)
from test_phase_owner_attestation import grant, decision, wire


@pytest.fixture
def identity_transport(monkeypatch):
    # Explicit test-only source input, not an installed client or provider rail.
    root = next(p for p in Path(__file__).resolve().parents if (p / "workspaces/aware_network").is_dir())
    source = root / "workspaces/aware_network/modules/identity/libs/identity_action_submission_runtime"
    monkeypatch.syspath_prepend(str(source))
    module = importlib.import_module("aware_identity_action_submission_runtime.contracts")
    assert Path(module.__file__).resolve().is_relative_to(source)
    return module


def _submission(identity, payload):
    fields = payload.to_wire()["fields"]
    return identity.FrozenSubmission(
        operation_key="controlled:original-operation", action_kind=payload.to_wire()["claim_schema_id"],
        target_ref="controlled:phase-target", source_epoch=fields["source_epoch"], payload=payload.to_wire(),
    )


def _nodes(value):
    return 1 + (sum(_nodes(v) for v in value.values()) if isinstance(value, dict)
                else sum(_nodes(v) for v in value) if isinstance(value, list) else 0)


@pytest.mark.parametrize("claim", [grant(), decision(), decision("decline"), decision(limitation=True)])
def test_full_projection_excludes_only_future_occurrence_and_enclosing_claim_ref(claim):
    original = claim.to_wire()
    self_field = "authorization_ref" if original["schema_id"] == AUTHORIZATION_SCHEMA else "decision_ref"
    projected = project_owner_attestation_action_payload_v2(claim)
    expected = {k: v for k, v in original.items() if k not in {"schema_id", "action_occurrence_ref", self_field}}
    assert projected.to_wire() == {"schema_id": PAYLOAD_SCHEMA, "claim_schema_id": original["schema_id"], "fields": expected}
    assert decode_owner_attestation_action_payload_v2(encode_owner_attestation_action_payload_v2(projected)).to_wire() == projected.to_wire()
    assert "action_occurrence_ref" not in projected.to_wire()["fields"]
    assert self_field not in projected.to_wire()["fields"]
    assert not hasattr(projected, "verified") and not hasattr(projected, "verifier_token")
    assert not hasattr(projected, "outcome")


@pytest.mark.parametrize("claim", [grant(), decision(), decision("decline"), decision(limitation=True)])
def test_complete_seven_obligations_and_limits_use_real_identity_contract(identity_transport, claim):
    projected = project_owner_attestation_action_payload_v2(claim)
    submission = _submission(identity_transport, projected)
    submission.validate()
    assert len(submission.canonical_bytes) <= identity_transport.SUBMISSION_BYTES == 16384
    assert _nodes(submission.body) <= 256
    assert submission.body["payload"] == projected.to_wire()
    assert submission.body["source_epoch"] == claim.to_wire()["source_epoch"]
    if claim.to_wire()["schema_id"] == DECISION_SCHEMA:
        assert len(submission.body["payload"]["fields"]["obligations"]) == 7
        assert submission.body["payload"]["fields"]["limitations"] == claim.to_wire()["limitations"]
        assert submission.body["payload"]["fields"]["evidence_inventory"] == claim.to_wire()["evidence_inventory"]


def test_payload_can_be_prepared_before_an_occurrence_exists_and_is_detached():
    fields = project_owner_attestation_action_payload_v2(decision(limitation=True)).to_wire()["fields"]
    prepared = make_owner_attestation_action_payload_v2(DECISION_SCHEMA, fields)
    before = prepared.reference
    fields["limitations"][0]["rationale"] = "Foreign rationale"
    assert prepared.reference == before
    assert prepared.to_wire()["fields"]["limitations"][0]["rationale"] != "Foreign rationale"
    assert prepared.to_wire()["fields"]["evidence_inventory"][0]["source_epoch"]["source_revision"] == "object:historical:1"


def test_future_occurrence_changes_do_not_create_a_digest_cycle():
    original = decision().to_wire()
    fields = {k: v for k, v in original.items() if k not in {"schema_id", "decision_ref"}}
    other = make_owner_attestation_claim_v2(DECISION_SCHEMA, dict(fields, action_occurrence_ref="actor-action-occurrence:sha256:" + "b" * 64))
    assert other.reference != decision().reference
    assert project_owner_attestation_action_payload_v2(other).reference == project_owner_attestation_action_payload_v2(decision()).reference


@pytest.mark.parametrize("field", ["action_occurrence_ref", "decision_ref", "schema_id"])
def test_future_or_extra_claim_fields_refuse(field):
    body = project_owner_attestation_action_payload_v2(decision()).to_wire()
    body["fields"][field] = "foreign:reference"
    with pytest.raises(OwnerAttestationCodecError): decode_owner_attestation_action_payload_v2(wire(body))


@pytest.mark.parametrize("fault", ["missing-obligation", "missing-review", "hidden-limitations", "extra-field", "changed-profile", "schema-confusion"])
def test_incomplete_or_unsupported_projection_refuses(fault):
    body = project_owner_attestation_action_payload_v2(decision(limitation=True)).to_wire()
    fields = body["fields"]
    if fault == "missing-obligation": fields["obligations"].pop()
    elif fault == "missing-review": fields["evidence_inventory"].pop()
    elif fault == "hidden-limitations": fields.pop("limitations")
    elif fault == "extra-field": fields["verified"] = True
    elif fault == "changed-profile": fields["profile"] = "evaluator_proven"
    else: body["claim_schema_id"] = AUTHORIZATION_SCHEMA
    with pytest.raises(OwnerAttestationCodecError): decode_owner_attestation_action_payload_v2(wire(body))


def test_oversized_rationale_refuses_identity_transport_without_trimming(identity_transport):
    body = project_owner_attestation_action_payload_v2(decision(limitation=True)).to_wire()
    body["fields"]["limitations"][0]["rationale"] = "x" * 16384
    payload = decode_owner_attestation_action_payload_v2(wire(body))
    before = encode_owner_attestation_action_payload_v2(payload)
    with pytest.raises(identity_transport.SubmissionError, match="submission_too_large"):
        _submission(identity_transport, payload)
    assert encode_owner_attestation_action_payload_v2(payload) == before


def test_node_exhaustion_refuses_identity_transport_without_omitting_evidence(identity_transport):
    body = project_owner_attestation_action_payload_v2(decision()).to_wire()
    inventory = body["fields"]["evidence_inventory"]
    template = inventory[0]
    inventory.extend(dict(template, evidence_ref=f"evidence:retained-{i:02d}") for i in range(30))
    inventory.sort(key=lambda item: item["evidence_ref"])
    payload = decode_owner_attestation_action_payload_v2(wire(body))
    before = encode_owner_attestation_action_payload_v2(payload)
    with pytest.raises(identity_transport.SubmissionError, match="submission_shape_exhausted"):
        _submission(identity_transport, payload)
    assert encode_owner_attestation_action_payload_v2(payload) == before


def test_claim_mutation_is_not_repaired_during_projection():
    value = decision()
    body = value.to_wire(); body["decision_ref"] = "goal-owner-phase-acceptance-decision:sha256:" + "a" * 64
    malformed = wire(body); object.__setattr__(value, "canonical_body", malformed)
    with pytest.raises(OwnerAttestationCodecError): project_owner_attestation_action_payload_v2(value)
    assert value.canonical_body == malformed


@pytest.mark.parametrize("raw", ['{"schema_id":"a","schema_id":"b"}', '{"schema_id":NaN}', '[]', b"\xff"])
def test_bad_json_refuses(raw):
    with pytest.raises(OwnerAttestationCodecError): decode_owner_attestation_action_payload_v2(raw)


def test_noncanonical_or_mutated_payload_storage_refuses():
    value = project_owner_attestation_action_payload_v2(grant())
    with pytest.raises(OwnerAttestationCodecError, match="noncanonical"):
        OwnerAttestationActionPayloadV2(json.dumps(value.to_wire(), indent=2))
    body = value.to_wire(); body["fields"]["action_occurrence_ref"] = "foreign:occurrence"
    malformed = wire(body); object.__setattr__(value, "canonical_body", malformed)
    with pytest.raises(OwnerAttestationCodecError): encode_owner_attestation_action_payload_v2(value)
    assert value.canonical_body == malformed


def test_neutral_source_imports_no_identity_or_provider_implementation():
    module = importlib.import_module("aware_goal_operational_runtime.phase_owner_attestation_payload")
    source = Path(module.__file__).read_text()
    assert "import aware_identity" not in source
    assert "from aware_identity" not in source
    assert "import aware_goal_native_fs_adapter" not in source
