"""Non-authorizing lifecycle claims and consistency joins for Goal creation.

No persistence, witness issuance, dispatch, provider query or recovery exists
here. Even a decoded `applied` completion is untrusted transport data.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import cast

from .identity import fingerprint
from .native_creation_request import decode_native_goal_creation_request
from .neutral_creation_contracts import (
    DECISION_SCHEMA, NeutralGoalCreationClaim, decode_neutral_goal_creation_claim,
)

PENDING_SCHEMA = "aware.goal.creation-pending-operation.v2"
REJECTION_SCHEMA = "aware.goal.creation-rejection.v2"
COMPLETION_SCHEMA = "aware.goal.creation-completion.v2"
_PENDING_FIELDS = {
    "schema_id", "operation_ref", "request_ref", "idempotency_key", "namespace_ref", "target_locator_ref",
    "provider_ref", "provider_generation_ref", "authority_profile_ref", "decision_ref", "semantic_state_ref",
    "owner_ref", "owner_recovery_head_ref", "expected_owner_revision_ref", "original_provider_recovery_ref",
    "request_body_ref", "decision_body_ref",
}
_REJECTION_FIELDS = {
    "schema_id", "operation_ref", "request_fingerprint", "request_ref", "provider_ref",
    "provider_generation_ref", "reason_code",
}
_COMPLETION_FIELDS = {
    "schema_id", "operation_ref", "request_ref", "decision_ref", "semantic_state_ref", "intent_ref", "genesis_ref",
    "provider_ref", "provider_generation_ref", "authority_profile_ref", "namespace_ref",
    "before_namespace_revision_ref", "after_namespace_revision_ref", "target_locator_ref",
    "effect_status", "publication_effect_ref", "effect_evidence_ref", "recovery_ref", "reason_code",
}
_CONTRACTS = {
    PENDING_SCHEMA: (_PENDING_FIELDS, "pending_operation_ref", "goal-creation-pending-operation:"),
    REJECTION_SCHEMA: (_REJECTION_FIELDS, "rejection_ref", "goal-creation-rejection:"),
    COMPLETION_SCHEMA: (_COMPLETION_FIELDS, "completion_ref", "goal-creation-completion:"),
}
_DOMAINS = {
    "request_ref": "goal-native-creation-request:", "decision_ref": "goal-creation-decision:",
    "semantic_state_ref": "goal-creation-semantic-state:", "intent_ref": "goal-native-creation-intent:",
    "genesis_ref": "goal-phase-execution-authority:", "request_body_ref": "content:", "decision_body_ref": "content:",
}
_NEGATIVE_REASONS = {
    "permission_refused", "identity_present", "source_stale", "authority_unavailable",
    "concurrency_unavailable", "concurrency_lost", "invalid_request", "cancelled_before_effect",
}
_COMPLETION_NULLABLE = {"after_namespace_revision_ref", "publication_effect_ref", "effect_evidence_ref", "recovery_ref"}
_REJECTION_NULLABLE = {"request_ref", "provider_ref", "provider_generation_ref"}


class NeutralCreationLifecycleError(ValueError):
    """Invalid transport/consistency claims, not an authentic effect verdict."""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _token(value: object) -> str:
    if type(value) is not str or not value or re.search(r"[\s|\x00-\x1f\x7f]", value):
        raise NeutralCreationLifecycleError("creation_lifecycle_token")
    _ = value.encode("utf-8")
    return value


def _digest(value: object, domain: str = "") -> None:
    if re.fullmatch(re.escape(domain) + r"sha256:[0-9a-f]{64}", _token(value)) is None:
        raise NeutralCreationLifecycleError("creation_lifecycle_reference")


def _object(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(cast(dict[str, object], value)) != fields:
        raise NeutralCreationLifecycleError("creation_lifecycle_fields")
    return cast(dict[str, object], value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    body: dict[str, object] = {}
    for key, value in pairs:
        if key in body:
            raise NeutralCreationLifecycleError("creation_lifecycle_duplicate_field")
        body[key] = value
    return body


def _parse(payload: str) -> object:
    if type(payload) is not str:
        raise NeutralCreationLifecycleError("creation_lifecycle_payload")
    try:
        return cast(object, json.loads(payload, object_pairs_hook=_pairs))
    except (ValueError, RecursionError) as exc:
        raise NeutralCreationLifecycleError("creation_lifecycle_json") from exc


def _validate(value: object, expected_schema: str | None = None) -> dict[str, object]:
    if type(value) is not dict:
        raise NeutralCreationLifecycleError("creation_lifecycle_object")
    schema = _token(cast(dict[str, object], value).get("schema_id"))
    if schema not in _CONTRACTS or expected_schema is not None and schema != expected_schema:
        raise NeutralCreationLifecycleError("creation_lifecycle_schema")
    fields, ref_field, domain = _CONTRACTS[schema]
    body = _object(cast(dict[str, object], value), fields | {ref_field})
    nullable: set[str] = _COMPLETION_NULLABLE if schema == COMPLETION_SCHEMA else _REJECTION_NULLABLE if schema == REJECTION_SCHEMA else set()
    for key, item in body.items():
        if key in nullable and item is None:
            continue
        _ = _token(item)
        if key in _DOMAINS:
            _digest(item, _DOMAINS[key])
    if schema == REJECTION_SCHEMA:
        _digest(body["request_fingerprint"])
        if body["reason_code"] not in _NEGATIVE_REASONS:
            raise NeutralCreationLifecycleError("creation_rejection_reason")
        if (body["request_ref"] is None) != (body["reason_code"] == "invalid_request"):
            raise NeutralCreationLifecycleError("creation_rejection_request_state")
        if (body["provider_ref"] is None) != (body["provider_generation_ref"] is None):
            raise NeutralCreationLifecycleError("creation_rejection_provider_pair")
        if body["provider_ref"] is None and body["reason_code"] != "invalid_request":
            raise NeutralCreationLifecycleError("creation_rejection_provider_reason")
    elif schema == COMPLETION_SCHEMA:
        effect_fields = ("after_namespace_revision_ref", "publication_effect_ref", "effect_evidence_ref")
        status = body["effect_status"]
        if status == "applied":
            if body["reason_code"] != "none" or any(body[field] is None for field in effect_fields):
                raise NeutralCreationLifecycleError("creation_completion_applied_state")
        elif status == "unapplied":
            if body["reason_code"] not in _NEGATIVE_REASONS - {"invalid_request"} or any(body[field] is not None for field in nullable):
                raise NeutralCreationLifecycleError("creation_completion_unapplied_state")
        elif status == "uncertain":
            if body["reason_code"] != "recovery_required" or body["recovery_ref"] is None:
                raise NeutralCreationLifecycleError("creation_completion_uncertain_state")
        else:
            raise NeutralCreationLifecycleError("creation_completion_status")
    _digest(body[ref_field], domain)
    if body[ref_field] != domain + fingerprint({key: item for key, item in body.items() if key != ref_field}):
        raise NeutralCreationLifecycleError("creation_lifecycle_digest")
    return body


def _checked(value: object, expected_schema: str | None = None) -> dict[str, object]:
    try:
        return _validate(value, expected_schema)
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise NeutralCreationLifecycleError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class NeutralCreationLifecycleClaim:
    """Detached record; never durable admission or qualified completion."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not NeutralCreationLifecycleClaim:
            raise NeutralCreationLifecycleError("creation_lifecycle_type")
        return _checked(_parse(self.canonical_body))

    @property
    def reference(self) -> str:
        body = self.to_wire()
        return cast(str, body[_CONTRACTS[cast(str, body["schema_id"])][1]])


def make_neutral_creation_lifecycle_claim(schema: str, fields: dict[str, object]) -> NeutralCreationLifecycleClaim:
    """Author a digested declaration, not persisted or issued authority."""
    if type(schema) is not str or schema not in _CONTRACTS:
        raise NeutralCreationLifecycleError("creation_lifecycle_schema")
    expected, ref_field, domain = _CONTRACTS[schema]
    fields = _object(fields, expected - {"schema_id"})
    body = {"schema_id": schema, **fields}
    body[ref_field] = domain + fingerprint(body)
    return NeutralCreationLifecycleClaim(_json(_checked(body)))


def decode_neutral_creation_lifecycle_claim(payload: str, *, expected_schema: str | None = None) -> NeutralCreationLifecycleClaim:
    return NeutralCreationLifecycleClaim(_json(_checked(_parse(payload), expected_schema)))


def encode_neutral_creation_lifecycle_claim(value: NeutralCreationLifecycleClaim) -> str:
    if type(value) is not NeutralCreationLifecycleClaim:
        raise NeutralCreationLifecycleError("creation_lifecycle_type")
    return _json(value.to_wire())


def _lifecycle(value: NeutralCreationLifecycleClaim, schema: str) -> dict[str, object]:
    if type(value) is not NeutralCreationLifecycleClaim:
        raise NeutralCreationLifecycleError("creation_lifecycle_type")
    return _checked(value.to_wire(), schema)


def _decision(value: NeutralGoalCreationClaim) -> dict[str, object]:
    if type(value) is not NeutralGoalCreationClaim:
        raise NeutralCreationLifecycleError("creation_lifecycle_decision_type")
    # Owning strict decoder revalidates the actual body, never an expected value.
    try:
        return decode_neutral_goal_creation_claim(_json(value.to_wire()), expected_schema=DECISION_SCHEMA).to_wire()
    except ValueError as exc:
        raise NeutralCreationLifecycleError(str(exc)) from exc


def creation_body_content_ref(body: dict[str, object]) -> str:
    """Content identity of canonical retained bytes; no retrieval or authority."""
    return "content:sha256:" + hashlib.sha256(_json(body).encode("utf-8")).hexdigest()


def check_creation_pending_claim(pending: NeutralCreationLifecycleClaim, decision: NeutralGoalCreationClaim) -> None:
    """Complete structural correlation only; does not verify recovery/durability."""
    body = _lifecycle(pending, PENDING_SCHEMA)
    dec = _decision(decision)
    req = cast(dict[str, object], dec["request"])
    auth = cast(dict[str, object], dec["authority_input"])
    state = cast(dict[str, object], dec["semantic_state"])
    expected = {
        "request_ref": req["request_ref"], "idempotency_key": req["idempotency_key"],
        "owner_ref": req["owner_ref"], "decision_ref": dec["decision_ref"],
        "semantic_state_ref": state["semantic_state_ref"],
        "request_body_ref": creation_body_content_ref(req), "decision_body_ref": creation_body_content_ref(dec),
        **{field: auth[field] for field in (
            "namespace_ref", "target_locator_ref", "provider_ref", "provider_generation_ref", "authority_profile_ref",
        )},
    }
    if any(body[field] != value for field, value in expected.items()):
        raise NeutralCreationLifecycleError("creation_pending_decision_join")


def check_creation_completion_claim(
    completion: NeutralCreationLifecycleClaim, pending: NeutralCreationLifecycleClaim, decision: NeutralGoalCreationClaim,
) -> None:
    """No effect verification: `applied` remains a caller-authored claim."""
    check_creation_pending_claim(pending, decision)
    body = _lifecycle(completion, COMPLETION_SCHEMA)
    pend = _lifecycle(pending, PENDING_SCHEMA)
    dec = _decision(decision)
    auth = cast(dict[str, object], dec["authority_input"])
    intent = cast(dict[str, object], dec["intent"])
    genesis = cast(dict[str, object], dec["genesis"])
    for field in ("operation_ref", "request_ref", "decision_ref", "semantic_state_ref", "provider_ref",
                  "provider_generation_ref", "authority_profile_ref", "namespace_ref", "target_locator_ref"):
        if body[field] != pend[field]:
            raise NeutralCreationLifecycleError("creation_completion_pending_join")
    if body["before_namespace_revision_ref"] != auth["namespace_revision_ref"] or body["intent_ref"] != intent["intent_ref"] or body["genesis_ref"] != genesis["authority_ref"]:
        raise NeutralCreationLifecycleError("creation_completion_decision_join")
    if body["recovery_ref"] is not None and body["recovery_ref"] != pend["original_provider_recovery_ref"]:
        raise NeutralCreationLifecycleError("creation_completion_recovery_join")


def check_creation_rejection_request_claim(rejection: NeutralCreationLifecycleClaim, submitted_bytes: bytes) -> None:
    """Bind exact submitted bytes, including malformed JSON, without admission."""
    body = _lifecycle(rejection, REJECTION_SCHEMA)
    if type(submitted_bytes) is not bytes:
        raise NeutralCreationLifecycleError("creation_rejection_input_bytes")
    if body["request_fingerprint"] != "sha256:" + hashlib.sha256(submitted_bytes).hexdigest():
        raise NeutralCreationLifecycleError("creation_rejection_fingerprint_join")
    try:
        request = decode_native_goal_creation_request(submitted_bytes.decode("utf-8"))
    except (ValueError, UnicodeError):
        if body["reason_code"] != "invalid_request" or body["request_ref"] is not None:
            raise NeutralCreationLifecycleError("creation_rejection_invalid_request_join")
    else:
        if body["reason_code"] == "invalid_request" or body["request_ref"] != request.request_ref:
            raise NeutralCreationLifecycleError("creation_rejection_valid_request_join")
