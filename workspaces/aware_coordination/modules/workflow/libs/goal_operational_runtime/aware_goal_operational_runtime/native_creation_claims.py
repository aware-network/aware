"""Strict portable creation claims; decoding and joins never issue authority.

No provider, registration, census, exclusion, planner, reader or writer lives
here. In particular a digest or an `absent` declaration is not proof of absence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from .identity import fingerprint, normalize_goal_tag

GENESIS_SCHEMA = "aware.goal.phase-execution-authority.v2"
CONTEXT_SCHEMA = "aware.goal.native-creation-context.v1"
GRANT_SCHEMA = "aware.goal.native-creation-grant.v1"
SOURCE_SCHEMA = "aware.goal.native-creation-source-admission.v1"
ABSENCE_SCHEMA = "aware.goal.native-identity-absence.v1"
EXCLUSION_SCHEMA = "aware.goal.native-creation-namespace-exclusion.v1"
GIT_PROFILE = "goal-native-genesis-repository-issue-v1"

_COMMON = {"schema_id", "namespace_ref", "namespace_revision_ref", "target_locator_ref"}
_CONTRACTS: dict[str, tuple[set[str], str, str]] = {
    GENESIS_SCHEMA: (
        {"schema_id", "origin_profile", "target_execution_authority_profile",
         "legacy_execution_disposition", "creation_intent_ref"},
        "authority_ref", "goal-phase-execution-authority:",
    ),
    CONTEXT_SCHEMA: (
        _COMMON | {"provider_ref", "verifier_profile", "request_ref", "creator_ref",
                   "initial_owner_ref", "creation_grant_ref", "source_admission_ref",
                   "identity_absence_ref", "namespace_exclusion_ref", "verified_at"},
        "context_ref", "goal-native-creation-context:",
    ),
    GRANT_SCHEMA: (
        _COMMON | {"creator_ref", "initial_owner_ref", "request_ref", "permission",
                   "authority_profile", "authority_source_ref"},
        "grant_ref", "goal-native-creation-grant:",
    ),
    SOURCE_SCHEMA: (
        _COMMON | {"provider_ref", "admission_profile", "admission_authority_ref"},
        "admission_ref", "goal-native-creation-source-admission:",
    ),
    ABSENCE_SCHEMA: (
        _COMMON | {"goal_tag", "target_disposition", "history_profile",
                   "history_boundary_ref", "history_inventory_ref", "identity_inventory_ref"},
        "absence_ref", "goal-native-identity-absence:",
    ),
    EXCLUSION_SCHEMA: (
        {"schema_id", "provider_ref", "namespace_ref", "repository_binding_ref",
         "request_ref", "creator_ref", "enforcement_profile", "enforcement_authority_ref",
         "scope", "fence_ref", "acquired_namespace_revision_ref", "acquired_at"},
        "exclusion_ref", "goal-native-creation-namespace-exclusion:",
    ),
}
_FIXED = {
    GENESIS_SCHEMA: {"origin_profile": "native_genesis_v1",
                     "target_execution_authority_profile": "phase_native_operational_v1",
                     "legacy_execution_disposition": "not_applicable"},
    CONTEXT_SCHEMA: {"verifier_profile": GIT_PROFILE},
    GRANT_SCHEMA: {"permission": "create_proposed_goal", "authority_profile": GIT_PROFILE},
    SOURCE_SCHEMA: {"admission_profile": "protocol-native-goal-fs-v1"},
    ABSENCE_SCHEMA: {"target_disposition": "absent",
                     "history_profile": "goal-native-git-identity-census-v1"},
    EXCLUSION_SCHEMA: {"enforcement_profile": "goal-native-git-namespace-exclusion-v1",
                       "scope": "complete_repository_ref_domain"},
}
_REFERENCE_DOMAINS = {
    "creation_intent_ref": "goal-native-creation-intent:",
    "request_ref": "goal-native-creation-request:",
    "creation_grant_ref": "goal-native-creation-grant:",
    "source_admission_ref": "goal-native-creation-source-admission:",
    "identity_absence_ref": "goal-native-identity-absence:",
    "namespace_exclusion_ref": "goal-native-creation-namespace-exclusion:",
}


class NativeCreationClaimError(ValueError):
    """Malformed or inconsistent declaration, not an authority decision."""


def _token(value: object) -> str:
    if type(value) is not str or not value or re.search(r"[\s|\x00-\x1f\x7f]", value):
        raise NativeCreationClaimError("creation_claim_token")
    try:
        _ = value.encode("utf-8")
    except UnicodeError as exc:
        raise NativeCreationClaimError("creation_claim_encoding") from exc
    return value


def _reference(value: object, domain: str) -> None:
    if re.fullmatch(re.escape(domain) + r"sha256:[0-9a-f]{64}", _token(value)) is None:
        raise NativeCreationClaimError("creation_claim_reference")


def _instant(value: object) -> None:
    text = _token(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", text) is None:
        raise NativeCreationClaimError("creation_claim_instant")
    try:
        _ = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise NativeCreationClaimError("creation_claim_instant") from exc


def _validate(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise NativeCreationClaimError("creation_claim_object")
    body = cast(dict[str, object], value)
    schema = _token(body.get("schema_id"))
    if schema not in _CONTRACTS:
        raise NativeCreationClaimError("creation_claim_schema")
    fields, ref_field, domain = _CONTRACTS[schema]
    if set(body) != fields | {ref_field}:
        raise NativeCreationClaimError("creation_claim_fields")
    for field, raw in body.items():
        _ = _token(raw)
        if field in _REFERENCE_DOMAINS:
            _reference(raw, _REFERENCE_DOMAINS[field])
    for field, expected in _FIXED[schema].items():
        if body[field] != expected:
            raise NativeCreationClaimError("creation_claim_profile")
    for field in ("verified_at", "acquired_at"):
        if field in body:
            _instant(body[field])
    if "goal_tag" in body and normalize_goal_tag(body["goal_tag"]) != body["goal_tag"]:
        raise NativeCreationClaimError("creation_claim_goal_tag")
    if schema in {CONTEXT_SCHEMA, GRANT_SCHEMA} and body["creator_ref"] != body["initial_owner_ref"]:
        raise NativeCreationClaimError("creation_claim_initial_owner")
    expected_ref = domain + fingerprint({key: raw for key, raw in body.items() if key != ref_field})
    if body[ref_field] != expected_ref:
        raise NativeCreationClaimError("creation_claim_digest")
    return body


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    body: dict[str, object] = {}
    for key, value in pairs:
        if key in body:
            raise NativeCreationClaimError("creation_claim_duplicate_field")
        body[key] = value
    return body


def _parse(value: str) -> object:
    if type(value) is not str:
        raise NativeCreationClaimError("creation_claim_json_type")
    try:
        return cast(object, json.loads(value, object_pairs_hook=_pairs))
    except (ValueError, RecursionError) as exc:
        raise NativeCreationClaimError("creation_claim_json") from exc


def _json(body: dict[str, object]) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True, slots=True)
class NativeCreationClaimV1:
    """Detached canonical claim storage. Never a sealed verifier output."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not NativeCreationClaimV1:
            raise NativeCreationClaimError("creation_claim_type")
        return _validate(_parse(self.canonical_body))

    @property
    def reference(self) -> str:
        body = self.to_wire()
        return _token(body[_CONTRACTS[_token(body["schema_id"])][1]])


def make_native_creation_claim(schema_id: str, fields: dict[str, object]) -> NativeCreationClaimV1:
    """Author a digested declaration, not permission or provider issuance."""
    schema = _token(schema_id)
    if schema not in _CONTRACTS or type(fields) is not dict:
        raise NativeCreationClaimError("creation_claim_schema")
    expected, ref_field, domain = _CONTRACTS[schema]
    if set(fields) != expected - {"schema_id"}:
        raise NativeCreationClaimError("creation_claim_fields")
    body = {"schema_id": schema, **fields}
    body[ref_field] = domain + fingerprint(body)
    return NativeCreationClaimV1(_json(_validate(body)))


def decode_native_creation_claim(payload: str) -> NativeCreationClaimV1:
    return NativeCreationClaimV1(_json(_validate(_parse(payload))))


def encode_native_creation_claim(claim: NativeCreationClaimV1) -> str:
    if type(claim) is not NativeCreationClaimV1:
        raise NativeCreationClaimError("creation_claim_type")
    return _json(claim.to_wire())


def check_native_creation_context_claims(
    context: NativeCreationClaimV1,
    grant: NativeCreationClaimV1,
    source: NativeCreationClaimV1,
    absence: NativeCreationClaimV1,
    exclusion: NativeCreationClaimV1,
) -> None:
    """Check structural joins only. These records still prove no authority."""
    claims = (context, grant, source, absence, exclusion)
    schemas = (CONTEXT_SCHEMA, GRANT_SCHEMA, SOURCE_SCHEMA, ABSENCE_SCHEMA, EXCLUSION_SCHEMA)
    bodies: list[dict[str, object]] = []
    for claim, schema in zip(claims, schemas, strict=True):
        if type(claim) is not NativeCreationClaimV1:
            raise NativeCreationClaimError("creation_claim_type")
        body = claim.to_wire()
        if body["schema_id"] != schema:
            raise NativeCreationClaimError("creation_claim_join_schema")
        bodies.append(body)
    ctx, permission, admission, _absent, guard = bodies
    for body in bodies[1:]:
        if body["namespace_ref"] != ctx["namespace_ref"]:
            raise NativeCreationClaimError("creation_claim_namespace_join")
    for body in bodies[1:4]:
        for field in ("namespace_revision_ref", "target_locator_ref"):
            if body[field] != ctx[field]:
                raise NativeCreationClaimError("creation_claim_source_join")
    for body in (permission, guard):
        for field in ("request_ref", "creator_ref"):
            if body[field] != ctx[field]:
                raise NativeCreationClaimError("creation_claim_creator_join")
    if permission["initial_owner_ref"] != ctx["initial_owner_ref"]:
        raise NativeCreationClaimError("creation_claim_owner_join")
    if admission["provider_ref"] != ctx["provider_ref"] or guard["provider_ref"] != ctx["provider_ref"]:
        raise NativeCreationClaimError("creation_claim_provider_join")
    if guard["acquired_namespace_revision_ref"] != ctx["namespace_revision_ref"]:
        raise NativeCreationClaimError("creation_claim_fence_revision_join")
    if cast(str, guard["acquired_at"]) > cast(str, ctx["verified_at"]):
        raise NativeCreationClaimError("creation_claim_time_join")
    for field, claim in zip(
        ("creation_grant_ref", "source_admission_ref", "identity_absence_ref", "namespace_exclusion_ref"),
        claims[1:], strict=True,
    ):
        if ctx[field] != claim.reference:
            raise NativeCreationClaimError("creation_claim_reference_join")
