"""Complete pre-issuance Goal payload projections, never issued actions.

No Identity import, enrollment, dispatch, currentness, post-issuance joining or
acceptance exists here. Identity retains ownership of its transport limits and
issuance/verifier. Authored timestamps and identity fields remain claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from .phase_acceptance_provenance import (
    AcceptanceProvenanceError, _digest, _json, _object, _parse,  # pyright: ignore[reportPrivateUsage]
)
from .phase_owner_attestation import (
    AUTHORIZATION_SCHEMA, DECISION_SCHEMA, OwnerAttestationClaimV2,
    OwnerAttestationCodecError, make_owner_attestation_claim_v2,
)

PAYLOAD_SCHEMA = "aware.goal.owner-attestation-action-payload.v2"
_SELF_FIELDS = {AUTHORIZATION_SCHEMA: "authorization_ref", DECISION_SCHEMA: "decision_ref"}


def _validate_payload(raw: object) -> dict[str, object]:
    body = _object(raw, {"schema_id", "claim_schema_id", "fields"})
    if body["schema_id"] != PAYLOAD_SCHEMA:
        raise OwnerAttestationCodecError("attestation_payload_schema")
    schema = body["claim_schema_id"]
    if type(schema) is not str or schema not in _SELF_FIELDS or type(body["fields"]) is not dict:
        raise OwnerAttestationCodecError("attestation_payload_fields")
    fields = cast(dict[str, object], body["fields"])
    if {"schema_id", "action_occurrence_ref", _SELF_FIELDS[schema]} & fields.keys():
        raise OwnerAttestationCodecError("attestation_payload_future_reference")
    # Reuse the accepted complete claim law, with a validation-only scaffold.
    # Neither this synthetic occurrence nor the derived claim escapes here.
    # It issues nothing; it avoids duplicating Gate/coverage/limitation rules.
    _ = make_owner_attestation_claim_v2(schema, {
        **fields, "action_occurrence_ref": "actor-action-occurrence:sha256:" + "0" * 64,
    })
    return body


@dataclass(frozen=True, slots=True)
class OwnerAttestationActionPayloadV2:
    """Detached complete business data, without a future enclosing claim ref."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not OwnerAttestationActionPayloadV2 or type(self.canonical_body) is not str:
            raise OwnerAttestationCodecError("attestation_payload_type")
        try:
            body = _validate_payload(_parse(self.canonical_body))
        except AcceptanceProvenanceError as exc:
            raise OwnerAttestationCodecError(str(exc)) from exc
        if _json(body) != self.canonical_body:
            raise OwnerAttestationCodecError("attestation_payload_noncanonical")
        return body

    @property
    def reference(self) -> str:
        # Reference is external to its body. It is content identity, not authority.
        return "goal-owner-attestation-action-payload:" + _digest(self.to_wire())


def make_owner_attestation_action_payload_v2(
    claim_schema: str, fields: dict[str, object],
) -> OwnerAttestationActionPayloadV2:
    """Freeze all original semantic fields before Identity issuance."""
    if type(fields) is not dict:
        raise OwnerAttestationCodecError("attestation_payload_fields")
    return decode_owner_attestation_action_payload_v2(_json({
        "schema_id": PAYLOAD_SCHEMA, "claim_schema_id": claim_schema, "fields": fields,
    }))


def project_owner_attestation_action_payload_v2(
    claim: OwnerAttestationClaimV2,
) -> OwnerAttestationActionPayloadV2:
    """Project a revalidated claim; never repair mutation or authenticate it."""
    if type(claim) is not OwnerAttestationClaimV2:
        raise OwnerAttestationCodecError("attestation_type")
    original = claim.to_wire()
    schema = cast(str, original["schema_id"])
    fields = {k: v for k, v in original.items() if k not in {
        "schema_id", "action_occurrence_ref", _SELF_FIELDS[schema],
    }}
    return make_owner_attestation_action_payload_v2(schema, fields)


def decode_owner_attestation_action_payload_v2(
    payload: bytes | str,
) -> OwnerAttestationActionPayloadV2:
    try:
        return OwnerAttestationActionPayloadV2(_json(_validate_payload(_parse(payload))))
    except AcceptanceProvenanceError as exc:
        raise OwnerAttestationCodecError(str(exc)) from exc


def encode_owner_attestation_action_payload_v2(value: OwnerAttestationActionPayloadV2) -> bytes:
    if type(value) is not OwnerAttestationActionPayloadV2:
        raise OwnerAttestationCodecError("attestation_payload_type")
    return _json(value.to_wire()).encode()
