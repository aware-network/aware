"""Non-authorizing V2 acceptance provenance and dependency-policy codecs.

Decoded records are claims, never qualified authority. No Issue, actor, source,
evaluator, acceptance, dependency or V5 carrier is verified by this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import cast

from .dependencies import GoalDependencyRelation
from .phase_contracts import GoalPhaseCoordinate, GoalPhaseDependency
from .phase_frontier import goal_phase_dependency_digest

QUALIFICATION_SCHEMA = "aware.goal.acceptance-qualification.v2"
POLICY_SCHEMA = "aware.goal.acceptance-dependency-policy.v2"
OWNER_PROFILE = "aware.goal.phase-acceptance-profile/owner-attested-v2"
PROVEN_PROFILE = "aware.goal.phase-gate-evaluator/environment-attention-portal-v2"
LEGACY_PROFILE = "aware.goal.acceptance-profile/legacy-unqualified-v1"
BASELINE_POLICY = "aware.goal.acceptance-dependency-policy/evaluator-proven-v2"
_SCHEMAS = {
    QUALIFICATION_SCHEMA: ("qualification_ref", "goal-acceptance-qualification:"),
    POLICY_SCHEMA: ("policy_ref", "goal-acceptance-dependency-policy:"),
}


class AcceptanceProvenanceError(ValueError):
    """Malformed claim or internal contradiction; not an authority verdict."""


def _json(value: object) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise AcceptanceProvenanceError("provenance_json") from exc


def _parse(data: str | bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise AcceptanceProvenanceError("provenance_duplicate_field")
            result[key] = value
        return result

    def constant(_value: str) -> object:
        raise AcceptanceProvenanceError("provenance_nonfinite")

    if type(data) not in (str, bytes):
        raise AcceptanceProvenanceError("provenance_json_type")
    try:
        wire = data.decode("utf-8") if type(data) is bytes else data
        return cast(object, json.loads(wire, object_pairs_hook=pairs, parse_constant=constant))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AcceptanceProvenanceError("provenance_json") from exc


def _object(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(cast(dict[str, object], value)) != fields:
        raise AcceptanceProvenanceError("provenance_fields")
    return cast(dict[str, object], value)


def _token(value: object) -> str:
    if type(value) is not str or not value or "|" in value or any(
        c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value
    ):
        raise AcceptanceProvenanceError("provenance_token")
    try:
        _ = value.encode("utf-8")
    except UnicodeError as exc:
        raise AcceptanceProvenanceError("provenance_token") from exc
    return value


def _sha(value: object) -> str:
    text = _token(value)
    if re.fullmatch(r"sha256:[0-9a-f]{64}", text) is None:
        raise AcceptanceProvenanceError("provenance_digest")
    return text


def _ref(value: object, domain: str) -> str:
    text = _token(value)
    if not text.startswith(domain):
        raise AcceptanceProvenanceError("provenance_reference")
    _ = _sha(text[len(domain):])
    return text


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _tokens(value: object, *, nonempty: bool = True) -> list[str]:
    if type(value) is not list:
        raise AcceptanceProvenanceError("provenance_array")
    items = [_token(item) for item in cast(list[object], value)]
    if items != sorted(set(items)) or (nonempty and not items):
        raise AcceptanceProvenanceError("provenance_array_order")
    return items


def _coordinate(value: object) -> GoalPhaseCoordinate:
    body = _object(value, {"goal_tag", "lane_key", "phase_key"})
    values = tuple(_token(body[key]) for key in ("goal_tag", "lane_key", "phase_key"))
    try:
        result = GoalPhaseCoordinate(*values)
    except (TypeError, ValueError) as exc:
        raise AcceptanceProvenanceError("provenance_coordinate") from exc
    if values != (result.goal_tag, result.lane_key, result.phase_key):
        raise AcceptanceProvenanceError("provenance_coordinate_normalization")
    return result


def _epoch(value: object) -> None:
    body = _object(value, {"provider_binding_ref", "source_revision", "document_ref", "goal_sha256"})
    _ = _token(body["provider_binding_ref"])
    _ = _token(body["source_revision"])
    _ = _ref(body["document_ref"], "goal-phase-document:")
    _ = _sha(body["goal_sha256"])


def _qualification(body: dict[str, object]) -> None:
    _ = _object(body, {
        "schema_id", "qualification_ref", "coordinate", "definition_ref", "gate_digest",
        "evidence_kind", "evidence_ref", "evidence_source_epoch", "mode", "profile",
        "authority_refs", "evidence_refs", "decision_ref", "profile_authorization_ref",
    })
    _ = _coordinate(body["coordinate"])
    _ = _ref(body["definition_ref"], "goal-phase-definition:")
    _ = _sha(body["gate_digest"])
    if body["evidence_kind"] == "acceptance":
        _ = _ref(body["evidence_ref"], "goal-phase-acceptance:")
    elif body["evidence_kind"] == "gate_observation":
        # Existing observation contracts permit provider-neutral opaque tokens.
        _ = _token(body["evidence_ref"])
    else:
        raise AcceptanceProvenanceError("provenance_evidence_kind")
    _epoch(body["evidence_source_epoch"])
    mode = _token(body["mode"])
    expected_profile = {"owner_attested": OWNER_PROFILE, "evaluator_proven": PROVEN_PROFILE,
                        "legacy_unqualified": LEGACY_PROFILE}.get(mode)
    if expected_profile is None or body["profile"] != expected_profile:
        raise AcceptanceProvenanceError("provenance_mode_profile")
    authority = _tokens(body["authority_refs"], nonempty=mode != "legacy_unqualified")
    evidence = _tokens(body["evidence_refs"], nonempty=mode != "legacy_unqualified")
    if mode == "owner_attested":
        _ = _ref(body["decision_ref"], "goal-owner-phase-acceptance-decision:")
        _ = _ref(body["profile_authorization_ref"], "goal-owner-phase-acceptance-authorization:")
    elif body["decision_ref"] is not None or body["profile_authorization_ref"] is not None:
        raise AcceptanceProvenanceError("provenance_foreign_decision")
    if mode == "legacy_unqualified" and (authority or evidence):
        raise AcceptanceProvenanceError("provenance_legacy_promotion")


def _policy(body: dict[str, object]) -> None:
    _ = _object(body, {"schema_id", "policy_ref", "declaration", "declaration_digest",
                      "required_modes", "authority_profile", "policy_authority_ref"})
    declaration = _object(body["declaration"], {
        "owner_goal_tag", "dependency_key", "dependent", "prerequisite",
        "required_gate_digest", "relation", "reason", "evidence_refs",
    })
    if declaration["relation"] != "requires_acceptance":
        raise AcceptanceProvenanceError("provenance_dependency_relation")
    reason = declaration["reason"]
    if type(reason) is not str or not reason.strip() or reason != reason.strip():
        raise AcceptanceProvenanceError("provenance_dependency_reason")
    try:
        _ = reason.encode("utf-8")
    except UnicodeError as exc:
        raise AcceptanceProvenanceError("provenance_dependency_reason") from exc
    try:
        dependency = GoalPhaseDependency(
            owner_goal_tag=_token(declaration["owner_goal_tag"]),
            dependency_key=_token(declaration["dependency_key"]),
            dependent=_coordinate(declaration["dependent"]),
            prerequisite=_coordinate(declaration["prerequisite"]),
            required_gate_digest=_sha(declaration["required_gate_digest"]),
            relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE, reason=reason,
            evidence_refs=tuple(_tokens(declaration["evidence_refs"], nonempty=False)),
        )
    except (TypeError, ValueError) as exc:
        raise AcceptanceProvenanceError("provenance_dependency") from exc
    if dependency.owner_goal_tag != declaration["owner_goal_tag"]:
        raise AcceptanceProvenanceError("provenance_dependency_normalization")
    if body["declaration_digest"] != goal_phase_dependency_digest(dependency):
        raise AcceptanceProvenanceError("provenance_declaration_digest")
    modes = _tokens(body["required_modes"])
    if any(mode not in ("evaluator_proven", "owner_attested") for mode in modes):
        raise AcceptanceProvenanceError("provenance_required_modes")
    if body["authority_profile"] == "versioned_baseline":
        if modes != ["evaluator_proven"] or body["policy_authority_ref"] != BASELINE_POLICY:
            raise AcceptanceProvenanceError("provenance_baseline_policy")
    elif body["authority_profile"] == "dependent_goal_authorized":
        _ = _ref(body["policy_authority_ref"], "goal-acceptance-dependency-policy-authorization:")
    else:
        raise AcceptanceProvenanceError("provenance_policy_profile")


def _validate(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise AcceptanceProvenanceError("provenance_fields")
    body = cast(dict[str, object], value)
    schema = _token(body.get("schema_id"))
    if schema not in _SCHEMAS:
        raise AcceptanceProvenanceError("provenance_schema")
    if schema == QUALIFICATION_SCHEMA:
        _qualification(body)
    else:
        _policy(body)
    field, domain = _SCHEMAS[schema]
    if body[field] != domain + _digest({key: item for key, item in body.items() if key != field}):
        raise AcceptanceProvenanceError("provenance_reference_digest")
    return body


@dataclass(frozen=True, slots=True)
class AcceptanceProvenanceClaimV2:
    """Canonical detached claim storage; no verifier token or authority result."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not AcceptanceProvenanceClaimV2 or type(self.canonical_body) is not str:
            raise AcceptanceProvenanceError("provenance_claim_type")
        body = _validate(_parse(self.canonical_body))
        if self.canonical_body != _json(body):
            raise AcceptanceProvenanceError("provenance_canonical")
        return body

    @property
    def reference(self) -> str:
        body = self.to_wire()
        return cast(str, body[_SCHEMAS[cast(str, body["schema_id"])][0]])


def decode_acceptance_provenance_v2(data: str | bytes) -> AcceptanceProvenanceClaimV2:
    return AcceptanceProvenanceClaimV2(_json(_validate(_parse(data))))


def encode_acceptance_provenance_v2(claim: AcceptanceProvenanceClaimV2) -> str:
    if type(claim) is not AcceptanceProvenanceClaimV2:
        raise AcceptanceProvenanceError("provenance_claim_type")
    return _json(claim.to_wire())


def make_acceptance_provenance_claim_v2(schema: str, fields: dict[str, object]) -> AcceptanceProvenanceClaimV2:
    """Derive a claim digest, NOT policy permission or acceptance qualification."""
    if type(schema) is not str or schema not in _SCHEMAS or type(fields) is not dict:
        raise AcceptanceProvenanceError("provenance_schema")
    field, domain = _SCHEMAS[schema]
    if "schema_id" in fields or field in fields:
        raise AcceptanceProvenanceError("provenance_fields")
    body = dict(fields, schema_id=schema)
    body[field] = domain + _digest(body)
    return decode_acceptance_provenance_v2(_json(body))
