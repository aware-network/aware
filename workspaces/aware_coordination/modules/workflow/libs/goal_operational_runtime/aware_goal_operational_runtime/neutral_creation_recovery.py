"""Non-authorizing recovery records. No persistence, prevention or dispatch.

An effect-verification reference is untrusted data, never terminal no-effect
proof. Only separately admitted concrete verifiers can qualify these claims.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import cast

from .identity import fingerprint
from .neutral_creation_contracts import NeutralGoalCreationClaim
from .neutral_creation_lifecycle import (
    COMPLETION_SCHEMA, PENDING_SCHEMA, NeutralCreationLifecycleClaim,
    check_creation_completion_claim, check_creation_pending_claim,
    creation_body_content_ref, decode_neutral_creation_lifecycle_claim,
    encode_neutral_creation_lifecycle_claim,
)

RECOVERY_SCHEMA = "aware.goal.creation-recovery-coordinate.v1"
DISPATCH_SCHEMA = "aware.goal.creation-dispatch-claim.v1"
SETTLEMENT_SCHEMA = "aware.goal.creation-settlement-record.v1"
WITNESS_SCHEMA = "aware.goal.creation-durability-witness.v1"
_COMMON = {"schema_id", "operation_ref", "owner_ref", "provider_ref", "provider_generation_ref"}
_RECORD = _COMMON | {"pending_operation_ref", "pending_body_ref", "owner_recovery_head_ref",
    "expected_owner_revision_ref", "original_provider_recovery_ref"}
_CONTRACTS = {
    RECOVERY_SCHEMA: (_COMMON | {"request_ref", "idempotency_key", "namespace_ref", "target_locator_ref",
        "authority_profile_ref", "query_binding_ref", "issuance_evidence_ref"},
        "recovery_coordinate_ref", "goal-creation-recovery-coordinate:"),
    DISPATCH_SCHEMA: (_RECORD, "dispatch_claim_ref", "goal-creation-dispatch-claim:"),
    SETTLEMENT_SCHEMA: (_RECORD | {"completion_ref", "completion_body_ref", "effect_verification_ref"},
        "settlement_record_ref", "goal-creation-settlement-record:"),
    WITNESS_SCHEMA: ({"schema_id", "record_kind", "record_ref", "record_body_ref", "operation_ref", "owner_ref",
        "owner_recovery_head_ref", "before_owner_revision_ref", "after_owner_revision_ref",
        "persistence_provider_ref", "persistence_generation_ref", "durability_profile_ref",
        "durability_evidence_ref", "reread_evidence_ref"},
        "durability_witness_ref", "goal-creation-durability-witness:"),
}
_KINDS = {"pending": (PENDING_SCHEMA, "pending_operation_ref", "goal-creation-pending-operation:"),
    "dispatch": (DISPATCH_SCHEMA, "dispatch_claim_ref", "goal-creation-dispatch-claim:"),
    "settlement": (SETTLEMENT_SCHEMA, "settlement_record_ref", "goal-creation-settlement-record:")}
_DOMAINS = {"request_ref": "goal-native-creation-request:", "pending_operation_ref": "goal-creation-pending-operation:",
    "completion_ref": "goal-creation-completion:", "pending_body_ref": "content:",
    "completion_body_ref": "content:", "record_body_ref": "content:"}


class NeutralCreationRecoveryError(ValueError):
    """Invalid claims; not a provider, cancellation or durability verdict."""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _token(value: object) -> str:
    if type(value) is not str or not value or re.search(r"[\s|\x00-\x1f\x7f]", value):
        raise NeutralCreationRecoveryError("creation_recovery_token")
    _ = value.encode("utf-8")
    return value


def _digest(value: object, domain: str) -> None:
    if re.fullmatch(re.escape(domain) + r"sha256:[0-9a-f]{64}", _token(value)) is None:
        raise NeutralCreationRecoveryError("creation_recovery_reference")


def _validate(value: object, expected_schema: str | None = None) -> dict[str, object]:
    if type(value) is not dict:
        raise NeutralCreationRecoveryError("creation_recovery_object")
    body = cast(dict[str, object], value)
    schema = _token(body.get("schema_id"))
    if schema not in _CONTRACTS or expected_schema is not None and expected_schema != schema:
        raise NeutralCreationRecoveryError("creation_recovery_schema")
    fields, ref_field, domain = _CONTRACTS[schema]
    if set(body) != fields | {ref_field}:
        raise NeutralCreationRecoveryError("creation_recovery_fields")
    for key, item in body.items():
        _ = _token(item)
        if key in _DOMAINS:
            _digest(item, _DOMAINS[key])
    if schema == WITNESS_SCHEMA:
        kind = cast(str, body["record_kind"])
        if kind not in _KINDS:
            raise NeutralCreationRecoveryError("creation_recovery_record_kind")
        _digest(body["record_ref"], _KINDS[kind][2])
        if body["before_owner_revision_ref"] == body["after_owner_revision_ref"]:
            raise NeutralCreationRecoveryError("creation_recovery_revision")
    _digest(body[ref_field], domain)
    if body[ref_field] != domain + fingerprint({key: item for key, item in body.items() if key != ref_field}):
        raise NeutralCreationRecoveryError("creation_recovery_digest")
    return body


def _checked(value: object, expected_schema: str | None = None) -> dict[str, object]:
    try:
        return _validate(value, expected_schema)
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise NeutralCreationRecoveryError(str(exc)) from exc


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise NeutralCreationRecoveryError("creation_recovery_duplicate")
        result[key] = value
    return result


def _parse(payload: str) -> object:
    if type(payload) is not str:
        raise NeutralCreationRecoveryError("creation_recovery_payload")
    try:
        return cast(object, json.loads(payload, object_pairs_hook=_pairs))
    except (ValueError, RecursionError) as exc:
        raise NeutralCreationRecoveryError("creation_recovery_json") from exc


@dataclass(frozen=True, slots=True)
class NeutralCreationRecoveryClaim:
    """Detached claim: decoding cannot restore an issuer seal."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not NeutralCreationRecoveryClaim:
            raise NeutralCreationRecoveryError("creation_recovery_type")
        return _checked(_parse(self.canonical_body))

    @property
    def reference(self) -> str:
        body = self.to_wire()
        return cast(str, body[_CONTRACTS[cast(str, body["schema_id"])][1]])


def make_neutral_creation_recovery_claim(schema: str, fields: dict[str, object]) -> NeutralCreationRecoveryClaim:
    if type(schema) is not str or schema not in _CONTRACTS:
        raise NeutralCreationRecoveryError("creation_recovery_schema")
    expected, ref_field, domain = _CONTRACTS[schema]
    if type(fields) is not dict or set(fields) != expected - {"schema_id"}:
        raise NeutralCreationRecoveryError("creation_recovery_fields")
    body = {"schema_id": schema, **fields}
    try:
        body[ref_field] = domain + fingerprint(body)
        return NeutralCreationRecoveryClaim(_json(_checked(body)))
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise NeutralCreationRecoveryError(str(exc)) from exc


def decode_neutral_creation_recovery_claim(payload: str, *, expected_schema: str | None = None) -> NeutralCreationRecoveryClaim:
    return NeutralCreationRecoveryClaim(_json(_checked(_parse(payload), expected_schema)))


def encode_neutral_creation_recovery_claim(value: NeutralCreationRecoveryClaim) -> str:
    return _json(_claim(value))


def _claim(value: NeutralCreationRecoveryClaim, schema: str | None = None) -> dict[str, object]:
    if type(value) is not NeutralCreationRecoveryClaim:
        raise NeutralCreationRecoveryError("creation_recovery_type")
    return _checked(value.to_wire(), schema)


def _lifecycle(value: NeutralCreationLifecycleClaim, schema: str) -> dict[str, object]:
    return decode_neutral_creation_lifecycle_claim(encode_neutral_creation_lifecycle_claim(value), expected_schema=schema).to_wire()


def _join(body: dict[str, object], expected: dict[str, object]) -> None:
    if any(body[key] != item for key, item in expected.items()):
        raise NeutralCreationRecoveryError("creation_recovery_join")


def check_creation_recovery_coordinate_claim(
    coordinate: NeutralCreationRecoveryClaim, pending: NeutralCreationLifecycleClaim, decision: NeutralGoalCreationClaim,
) -> None:
    """Identity consistency only, never authenticate a query route."""
    check_creation_pending_claim(pending, decision)
    body, pend = _claim(coordinate, RECOVERY_SCHEMA), _lifecycle(pending, PENDING_SCHEMA)
    _join(body, {key: pend[key] for key in _COMMON - {"schema_id"} | {
        "request_ref", "idempotency_key", "namespace_ref", "target_locator_ref", "authority_profile_ref"}})
    if pend["original_provider_recovery_ref"] != body["recovery_coordinate_ref"]:
        raise NeutralCreationRecoveryError("creation_recovery_coordinate_join")


def check_creation_durability_witness_claim(
    witness: NeutralCreationRecoveryClaim, record: NeutralCreationRecoveryClaim | NeutralCreationLifecycleClaim,
) -> None:
    """Exact record/CAS correlation only, not a durable-write witness."""
    body = _claim(witness, WITNESS_SCHEMA)
    schema, ref_field, _ = _KINDS[cast(str, body["record_kind"])]
    rec = _lifecycle(record, schema) if type(record) is NeutralCreationLifecycleClaim else _claim(cast(NeutralCreationRecoveryClaim, record), schema)
    _join(body, {"record_ref": rec[ref_field], "record_body_ref": creation_body_content_ref(rec),
        "before_owner_revision_ref": rec["expected_owner_revision_ref"],
        **{key: rec[key] for key in ("operation_ref", "owner_ref", "owner_recovery_head_ref")}})


def check_creation_dispatch_claim(
    dispatch: NeutralCreationRecoveryClaim, pending: NeutralCreationLifecycleClaim,
    decision: NeutralGoalCreationClaim, coordinate: NeutralCreationRecoveryClaim, pending_witness: NeutralCreationRecoveryClaim,
) -> None:
    """No dispatch authorization: all supplied witnesses remain claims."""
    check_creation_recovery_coordinate_claim(coordinate, pending, decision)
    check_creation_durability_witness_claim(pending_witness, pending)
    body, pend, witness = _claim(dispatch, DISPATCH_SCHEMA), _lifecycle(pending, PENDING_SCHEMA), _claim(pending_witness, WITNESS_SCHEMA)
    _join(body, {key: pend[key] for key in _RECORD - {"schema_id", "pending_operation_ref", "pending_body_ref", "expected_owner_revision_ref"}})
    _join(body, {"pending_operation_ref": pend["pending_operation_ref"], "pending_body_ref": creation_body_content_ref(pend),
        "expected_owner_revision_ref": witness["after_owner_revision_ref"]})


def check_creation_settlement_claim(
    settlement: NeutralCreationRecoveryClaim, completion: NeutralCreationLifecycleClaim,
    dispatch: NeutralCreationRecoveryClaim, dispatch_witness: NeutralCreationRecoveryClaim,
    pending: NeutralCreationLifecycleClaim, decision: NeutralGoalCreationClaim,
    coordinate: NeutralCreationRecoveryClaim, pending_witness: NeutralCreationRecoveryClaim,
) -> None:
    """Terminal-shape correlation only; no effect or permanent prevention proof.

    In particular an unapplied claim cannot authorize settlement/retry here.
    Concrete terminal-proof qualification is deliberately not implemented.
    """
    check_creation_dispatch_claim(dispatch, pending, decision, coordinate, pending_witness)
    check_creation_durability_witness_claim(dispatch_witness, dispatch)
    check_creation_completion_claim(completion, pending, decision)
    body, comp, disp = _claim(settlement, SETTLEMENT_SCHEMA), _lifecycle(completion, COMPLETION_SCHEMA), _claim(dispatch, DISPATCH_SCHEMA)
    witness = _claim(dispatch_witness, WITNESS_SCHEMA)
    if comp["effect_status"] not in {"applied", "unapplied"}:
        raise NeutralCreationRecoveryError("creation_recovery_nonterminal_completion")
    _join(body, {key: disp[key] for key in _RECORD - {"schema_id", "expected_owner_revision_ref"}})
    _join(body, {"expected_owner_revision_ref": witness["after_owner_revision_ref"],
        "completion_ref": comp["completion_ref"], "completion_body_ref": creation_body_content_ref(comp)})
