"""Portable owner-attestation claims, not action or publication authority.

No Issue parsing, issuance, policy evaluation, currentness, acceptance, seal,
provider calls or writer exists in these strict contracts and pure joins.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from .phase_acceptance_provenance import (
    OWNER_PROFILE, AcceptanceProvenanceError,
    _coordinate, _digest, _epoch, _json, _object, _parse, _ref, _sha, _token, _tokens,  # pyright: ignore[reportPrivateUsage]
)

AUTHORIZATION_SCHEMA = "aware.goal.owner-attestation-authorization.v2"
DECISION_SCHEMA = "aware.goal.owner-attestation-decision.v2"
OBLIGATIONS = tuple(sorted(("environment_portal", "attention_resolution", "owner_only_carriage",
                            "human_agent_parity", "negative_coordinates", "r3c_stability", "f2_stability")))
EVIDENCE_ROLES = ("closeout", "implementation", "independent_review")
_SCHEMAS = {
    AUTHORIZATION_SCHEMA: ("authorization_ref", "goal-owner-phase-acceptance-authorization:"),
    DECISION_SCHEMA: ("decision_ref", "goal-owner-phase-acceptance-decision:"),
}
_COMMON = {"schema_id", "coordinate", "definition_ref", "gate_digest", "source_epoch", "profile",
           "owner_actor_ref", "owner_execution_id", "owner_authority_ref", "issued_at", "action_occurrence_ref"}


class OwnerAttestationCodecError(ValueError):
    """Invalid or internally contradictory claim, never an issuance verdict."""


def _array(value: object) -> list[object]:
    if type(value) is not list:
        raise OwnerAttestationCodecError("attestation_array")
    return cast(list[object], value)


def _text(value: object) -> str:
    if type(value) is not str or not value or value != value.strip() or "\x00" in value:
        raise OwnerAttestationCodecError("attestation_text")
    try:
        _ = value.encode("utf-8")
    except UnicodeError as exc:
        raise OwnerAttestationCodecError("attestation_text") from exc
    return value


def _instant(value: object) -> datetime:
    text = _token(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", text) is None:
        raise OwnerAttestationCodecError("attestation_instant")
    try:
        return datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise OwnerAttestationCodecError("attestation_instant") from exc


def _common(body: dict[str, object]) -> None:
    _ = _coordinate(body["coordinate"])
    _ = _ref(body["definition_ref"], "goal-phase-definition:")
    _ = _sha(body["gate_digest"])
    _epoch(body["source_epoch"])
    if body["profile"] != OWNER_PROFILE:
        raise OwnerAttestationCodecError("attestation_profile")
    _ = _token(body["owner_actor_ref"])
    execution = _token(body["owner_execution_id"])
    if re.fullmatch(r"[a-z][a-z0-9_]*-[A-Za-z0-9][A-Za-z0-9._-]*", execution) is None:
        raise OwnerAttestationCodecError("attestation_execution")
    _ = _token(body["owner_authority_ref"])
    _ = _ref(body["action_occurrence_ref"], "actor-action-occurrence:")
    _ = _instant(body["issued_at"])


def _authorization(body: dict[str, object]) -> None:
    _ = _object(body, _COMMON | {"authorization_ref", "promise_interpretation", "obligation_keys", "evidence_roles"})
    _common(body)
    if body["promise_interpretation"] != "unchanged_gate_attestation":
        raise OwnerAttestationCodecError("attestation_promise_interpretation")
    if _tokens(body["obligation_keys"]) != list(OBLIGATIONS) or _tokens(body["evidence_roles"]) != list(EVIDENCE_ROLES):
        raise OwnerAttestationCodecError("attestation_authorization_coverage")


def _inventory(value: object) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    keys: list[str] = []
    for raw in _array(value):
        item = _object(raw, {"evidence_ref", "role", "content_identity", "source_epoch", "publication_authority_ref"})
        reference = _token(item["evidence_ref"])
        if item["role"] not in EVIDENCE_ROLES:
            raise OwnerAttestationCodecError("attestation_evidence_role")
        content = _object(item["content_identity"], {"content_ref", "sha256", "byte_count"})
        _ = _token(content["content_ref"])
        _ = _sha(content["sha256"])
        if type(content["byte_count"]) is not int or content["byte_count"] <= 0:
            raise OwnerAttestationCodecError("attestation_byte_count")
        epoch = _object(item["source_epoch"], {"provider_binding_ref", "source_revision"})
        _ = _token(epoch["provider_binding_ref"])
        _ = _token(epoch["source_revision"])
        _ = _token(item["publication_authority_ref"])
        result[reference] = item
        keys.append(reference)
    if keys != sorted(set(keys)):
        raise OwnerAttestationCodecError("attestation_inventory_order")
    return result


def _decision(body: dict[str, object]) -> None:
    _ = _object(body, _COMMON | {"decision_ref", "authorization_ref", "verdict", "evidence_inventory", "obligations", "limitations"})
    _common(body)
    _ = _ref(body["authorization_ref"], "goal-owner-phase-acceptance-authorization:")
    if body["verdict"] not in ("accept", "decline"):
        raise OwnerAttestationCodecError("attestation_verdict")
    inventory = _inventory(body["evidence_inventory"])
    keys: list[str] = []
    for raw in _array(body["obligations"]):
        item = _object(raw, {"key", "attestation", "evidence_refs"})
        key = _token(item["key"])
        if item["attestation"] not in ("met", "not_met", "unavailable"):
            raise OwnerAttestationCodecError("attestation_obligation_state")
        refs = _tokens(item["evidence_refs"], nonempty=item["attestation"] != "unavailable")
        if any(reference not in inventory for reference in refs):
            raise OwnerAttestationCodecError("attestation_evidence_join")
        if body["verdict"] == "accept" and item["attestation"] != "met":
            raise OwnerAttestationCodecError("attestation_accept_contradiction")
        keys.append(key)
    if keys != list(OBLIGATIONS):
        raise OwnerAttestationCodecError("attestation_obligation_coverage")
    limitation_keys: list[str] = []
    for raw in _array(body["limitations"]):
        item = _object(raw, {"key", "description", "evidence_refs", "disposition", "rationale", "review_evidence_ref"})
        limitation_keys.append(_token(item["key"]))
        _ = _text(item["description"])
        _ = _text(item["rationale"])
        refs = _tokens(item["evidence_refs"])
        if any(reference not in inventory for reference in refs):
            raise OwnerAttestationCodecError("attestation_evidence_join")
        if item["disposition"] not in ("in_scope_blocker", "outside_gate", "unverified"):
            raise OwnerAttestationCodecError("attestation_limitation_disposition")
        review_ref = item["review_evidence_ref"]
        if item["disposition"] == "outside_gate":
            review_ref = _token(review_ref)
            if review_ref not in inventory or inventory[review_ref]["role"] != "independent_review":
                raise OwnerAttestationCodecError("attestation_limitation_review")
        elif review_ref is not None:
            raise OwnerAttestationCodecError("attestation_limitation_review")
        if body["verdict"] == "accept" and item["disposition"] != "outside_gate":
            raise OwnerAttestationCodecError("attestation_accept_contradiction")
    if limitation_keys != sorted(set(limitation_keys)):
        raise OwnerAttestationCodecError("attestation_limitation_order")
    if body["verdict"] == "accept" and {item["role"] for item in inventory.values()} != set(EVIDENCE_ROLES):
        raise OwnerAttestationCodecError("attestation_accept_evidence_coverage")


def _validate(raw: object) -> dict[str, object]:
    if type(raw) is not dict:
        raise OwnerAttestationCodecError("attestation_fields")
    body = cast(dict[str, object], raw)
    schema = _token(body.get("schema_id"))
    if schema not in _SCHEMAS:
        raise OwnerAttestationCodecError("attestation_schema")
    if schema == AUTHORIZATION_SCHEMA:
        _authorization(body)
    else:
        _decision(body)
    field, domain = _SCHEMAS[schema]
    if body[field] != domain + _digest({key: value for key, value in body.items() if key != field}):
        raise OwnerAttestationCodecError("attestation_digest")
    return body


@dataclass(frozen=True, slots=True)
class OwnerAttestationClaimV2:
    """Canonical declaration storage; no issued action, policy or acceptance."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not OwnerAttestationClaimV2 or type(self.canonical_body) is not str:
            raise OwnerAttestationCodecError("attestation_type")
        try:
            body = _validate(_parse(self.canonical_body))
        except AcceptanceProvenanceError as exc:
            raise OwnerAttestationCodecError(str(exc)) from exc
        if self.canonical_body != _json(body):
            raise OwnerAttestationCodecError("attestation_canonical")
        return body

    @property
    def reference(self) -> str:
        body = self.to_wire()
        return cast(str, body[_SCHEMAS[cast(str, body["schema_id"])][0]])


def decode_owner_attestation_v2(payload: bytes | str) -> OwnerAttestationClaimV2:
    try:
        return OwnerAttestationClaimV2(_json(_validate(_parse(payload))))
    except AcceptanceProvenanceError as exc:
        raise OwnerAttestationCodecError(str(exc)) from exc


def encode_owner_attestation_v2(value: OwnerAttestationClaimV2) -> bytes:
    if type(value) is not OwnerAttestationClaimV2:
        raise OwnerAttestationCodecError("attestation_type")
    return _json(value.to_wire()).encode()


def make_owner_attestation_claim_v2(schema: str, fields: dict[str, object]) -> OwnerAttestationClaimV2:
    """Derive a claim identity only, never mint a trusted owner action."""
    if type(schema) is not str or schema not in _SCHEMAS or type(fields) is not dict:
        raise OwnerAttestationCodecError("attestation_schema")
    field, domain = _SCHEMAS[schema]
    if field in fields or "schema_id" in fields:
        raise OwnerAttestationCodecError("attestation_fields")
    body = dict(fields, schema_id=schema)
    body[field] = domain + _digest(body)
    return decode_owner_attestation_v2(_json(body))


def check_owner_attestation_claim_pair_v2(authorization: OwnerAttestationClaimV2, decision: OwnerAttestationClaimV2) -> None:
    """Pure claim join; verifies no action, owner, evidence or source authority."""
    if type(authorization) is not OwnerAttestationClaimV2 or type(decision) is not OwnerAttestationClaimV2:
        raise OwnerAttestationCodecError("attestation_type")
    grant, action = authorization.to_wire(), decision.to_wire()
    if grant["schema_id"] != AUTHORIZATION_SCHEMA or action["schema_id"] != DECISION_SCHEMA:
        raise OwnerAttestationCodecError("attestation_pair_profile")
    if action["authorization_ref"] != authorization.reference or any(
        grant[key] != action[key] for key in (
            "coordinate", "definition_ref", "gate_digest", "source_epoch", "profile",
            "owner_actor_ref", "owner_execution_id", "owner_authority_ref",
        )
    ):
        raise OwnerAttestationCodecError("attestation_pair_binding")
    if grant["action_occurrence_ref"] == action["action_occurrence_ref"] or _instant(grant["issued_at"]) > _instant(action["issued_at"]):
        raise OwnerAttestationCodecError("attestation_pair_action_order")
