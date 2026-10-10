"""Non-authorizing managed-replacement wire codecs.

These functions prove structural validity and content integrity only. A decoded
signature, reference, claimed resource or result is NOT verified authority.
Issuer trust, external reference resolution, physical effects, source admission
and live currentness belong to independently admitted concrete providers.
No filesystem, clock, process, crypto or provider callback is used here.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import unicodedata
from collections.abc import Callable
from typing import cast

PREFIX = "aware.managed-replacement."
MAX_WIRE_BYTES = 1 << 20
MAX_DEPTH = 24
MAX_CONTENT_BYTES = 16 << 20
MAX_UINT = (1 << 63) - 1
LIVE_WINDOW_NS = 10_000_000_000

Check = Callable[[object], None]


class GuardedReplacementContractError(ValueError):
    """Malformed or contradictory unverified transport."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GuardedReplacementContractError(message)


def _mapping(value: object) -> dict[str, object]:
    _require(type(value) is dict, "expected exact JSON object")
    return cast(dict[str, object], value)


def _text(value: object) -> str:
    _require(type(value) is str, "expected exact JSON string")
    text = cast(str, value)
    _require(unicodedata.normalize("NFC", text) == text, "non-NFC string")
    _require(not any(0xD800 <= ord(c) <= 0xDFFF for c in text), "surrogate string")
    return text


def _uint(value: object) -> None:
    _require(type(value) is int and 0 <= value <= MAX_UINT, "invalid unsigned integer")


def _positive(value: object) -> None:
    _uint(value)
    _require(cast(int, value) > 0, "expected positive integer")


def _pattern(pattern: str) -> Check:
    def check(value: object) -> None:
        _require(re.fullmatch(pattern, _text(value)) is not None, "invalid text domain")
    return check


_id = _pattern(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,191}")
_digest = _pattern(r"sha256:[0-9a-f]{64}")
_hex32 = _pattern(r"[0-9a-f]{64}")
_hex64 = _pattern(r"[0-9a-f]{128}")


def _enum(*values: str) -> Check:
    def check(value: object) -> None:
        _require(_text(value) in values, "unknown enum")
    return check


def _null(value: object) -> None:
    _require(value is None, "expected null")


def _nullable(check: Check) -> Check:
    def validate(value: object) -> None:
        if value is not None:
            check(value)
    return validate


def _path(value: object) -> None:
    text = _text(value)
    _require(1 <= len(text.encode("utf-8")) <= 4096, "path byte bound")
    _require("\\" not in text and not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in text), "unsafe path")
    _require(all(segment not in ("", ".", "..") for segment in text.split("/")), "noncanonical relative path")


def _reference(schema: str) -> Check:
    # Structural pointer validation is deliberately NOT target resolution.
    return _pattern(re.escape(PREFIX + schema) + r":sha256:[0-9a-f]{64}")


def _object(**fields: Check) -> Check:
    def check(value: object) -> None:
        data = _mapping(value)
        _require(set(data) == set(fields), "missing or unknown fields")
        for name, validate in fields.items():
            validate(data[name])
    return check


def _ordered_array[K: (int, bytes, tuple[str, int, int])](
    check: Check, key: Callable[[object], K], limit: int,
) -> Check:
    def validate(value: object) -> None:
        _require(type(value) is list and len(cast(list[object], value)) <= limit, "invalid bounded array")
        entries = cast(list[object], value)
        for entry in entries:
            check(entry)
        keys = [key(entry) for entry in entries]
        _require(all(keys[i - 1] < keys[i] for i in range(1, len(keys))), "unordered or duplicate set")
    return validate


_reader_gids = _ordered_array(_positive, lambda value: cast(int, value), 16)
_content = _object(digest=_digest, size=_uint)
_file = _object(content=_content, uid=_positive, gid=_positive, mode=_uint,
                device_major=_uint, device_minor=_uint, inode=_positive, link_count=_positive)
_process = _object(pid=_positive, start_ticks=_positive, boot_id=_hex32,
                   executable=_digest, uid=_positive, gid=_positive)
_storage = _object(storage_id=_id, filesystem=_enum("ext4"), device_major=_uint,
                   device_minor=_uint, root_inode=_positive, anchor_digest=_digest,
                   provisioning_profile=_enum("fresh_exclusive_volume_v1"),
                   exposure_policy=_enum("broker_write_admitted_readers_only_v1"))
_observation = _object(repository_binding_ref=_id, epoch=_id, cursor=_uint,
                       snapshot_digest=_digest, visibility_policy_ref=_id, visibility_policy_version=_id)
_coordinate = _object(kind=_enum("observation"), repository_binding_ref=_id,
                      state_digest=_digest, observation=_observation, revision_ref=_null)
_stage = _enum("admitted", "staged", "replaced", "durable", "complete")
_sync = _enum("not_started", "complete", "failed")


def _process_key(value: object) -> tuple[str, int, int]:
    data = _mapping(value)
    return cast(str, data["boot_id"]), cast(int, data["pid"]), cast(int, data["start_ticks"])


_shapes: dict[str, Check] = {
    "deployment.v1": _object(
        deployment_id=_id, host_id=_id, workspace_binding_ref=_id,
        backend=_enum("linux_managed_volume_broker_v1"), physical_profile=_enum("continuous_root_v1"),
        operation_profile=_enum("guarded_replace_existing_v1"), release_digest=_digest,
        configuration_digest=_digest, storage=_storage, writer_uid=_positive, writer_gid=_positive,
        reader_gids=_reader_gids, policy_digest=_digest, publication_ref=_reference("deployment-effect.v1"),
        supervisor_issuer_id=_id, supervisor_key_id=_digest, broker_issuer_id=_id, broker_key_id=_digest,
        workspace_issuer_id=_id, workspace_key_id=_digest, activation_sequence=_positive),
    "issuer-appointment.v1": _object(
        deployment_ref=_reference("deployment.v1"), issuer_id=_id, key_id=_digest, public_key=_hex32,
        role=_enum("supervisor", "broker", "workspace"),
        allowed_schemas=_ordered_array(_id, lambda value: cast(str, value).encode("ascii"), 8),
        appointment_sequence=_positive),
    "live.v1": _object(
        deployment_ref=_reference("deployment.v1"), challenge=_hex32, session_id=_id,
        activation_sequence=_positive, policy_sequence=_positive, observed_boottime_ns=_uint,
        expires_boottime_ns=_uint, state=_enum("active", "quiescing", "revoked", "unavailable"),
        broker=_process, mount_namespace_id=_positive, mount_id=_positive, root=_storage,
        configuration_digest=_digest, release_digest=_digest, writer_policy_digest=_digest,
        fencing_record_ref=_reference("fence.v1")),
    "grant.v1": _object(
        deployment_ref=_reference("deployment.v1"), workspace_binding_ref=_id, holder_id=_id,
        operation_ref=_id, idempotency_key=_id, target_path=_path, purpose=_enum("replace_existing"),
        source_admission_ref=_reference("workspace-source-admission.v1"), policy_sequence=_positive,
        issued_boottime_ns=_uint, expires_boottime_ns=_uint, boot_id=_hex32),
    "admission.v1": _object(
        deployment_ref=_reference("deployment.v1"), live_ref=_reference("live.v1"),
        grant_ref=_reference("grant.v1"), session_id=_id, operation_ref=_id, idempotency_key=_id,
        workspace_binding_ref=_id, target_path=_path, expected_coordinate=_coordinate,
        before=_file, replacement=_content, exclusion_id=_id, activation_sequence=_positive,
        journal_intent_ref=_reference("journal-intent.v1")),
    "result.v1": _object(
        admission_ref=_reference("admission.v1"), deployment_ref=_reference("deployment.v1"),
        operation_ref=_id, idempotency_key=_id, activation_sequence=_positive,
        status=_enum("applied", "unapplied", "uncertain"), after=_nullable(_file), stage=_stage,
        journal_result_ref=_reference("journal-result.v1"), terminal_live_ref=_nullable(_reference("live.v1")),
        reason=_enum("none", "authority_refused", "cancelled_before_replace", "effect_uncertain", "sync_failed", "recovery_required")),
    "refusal.v1": _object(request_fingerprint=_digest, status=_enum("conflict", "denied"),
                           reason=_enum("preimage_conflict", "authority_refused", "unsupported_target", "verification_unavailable")),
    "recovery.v1": _object(
        original_admission_ref=_reference("admission.v1"), original_result_ref=_nullable(_reference("result.v1")),
        recovered_result_ref=_reference("result.v1"), recovery_live_ref=_reference("live.v1"), fencing_record_ref=_reference("fence.v1")),
    "deployment-effect.v1": _object(
        deployment_id=_id, host_id=_id, configuration_digest=_digest, release_digest=_digest,
        storage=_storage, writer_uid=_positive, writer_gid=_positive, reader_gids=_reader_gids,
        policy_digest=_digest, operator_admission_ref=_digest, effect_sequence=_positive,
        initialization=_enum("fresh_before_untrusted_exposure"), completed_boottime_ns=_uint, boot_id=_hex32),
    "workspace-source-admission.v1": _object(
        workspace_binding_ref=_id, holder_id=_id, target_path=_path, purpose=_enum("replace_existing"),
        policy_digest=_digest, policy_sequence=_positive, boot_id=_hex32, issued_boottime_ns=_uint, expires_boottime_ns=_uint),
    "fence.v1": _object(
        deployment_ref=_reference("deployment.v1"), activation_sequence=_positive,
        prior_processes=_ordered_array(_process, _process_key, 64), mode=_enum("fresh_start", "terminated_previous_generation"),
        policy_sequence=_positive, completed_boottime_ns=_uint, boot_id=_hex32),
    "journal-intent.v1": _object(
        deployment_ref=_reference("deployment.v1"), live_ref=_reference("live.v1"), grant_ref=_reference("grant.v1"),
        session_id=_id, operation_ref=_id, idempotency_key=_id, target_path=_path, expected_coordinate=_coordinate,
        before=_file, replacement=_content, activation_sequence=_positive, exclusion_id=_id, sequence=_positive),
    "journal-result.v1": _object(
        journal_intent_ref=_reference("journal-intent.v1"), admission_ref=_reference("admission.v1"), sequence=_positive,
        stage=_stage, after=_nullable(_file), file_sync=_sync, directory_sync=_sync,
        replacement=_enum("not_started", "complete", "unknown")),
}

BODY_SCHEMAS = tuple(sorted(PREFIX + name for name in _shapes))
_role_schemas = {
    "supervisor": ("fence.v1", "live.v1", "recovery.v1"),
    "broker": ("admission.v1", "journal-intent.v1", "journal-result.v1", "result.v1"),
    "workspace": ("grant.v1", "issuer-appointment.v1", "workspace-source-admission.v1"),
}


def _tree(value: object, depth: int = 0) -> None:
    _require(depth <= MAX_DEPTH, "nesting bound")
    if type(value) in (dict, list):
        _require(depth < MAX_DEPTH, "nesting bound")
    if type(value) is dict:
        for key, child in cast(dict[str, object], value).items():
            _require(type(key) is str and key.isascii(), "non-ASCII field key")
            _tree(child, depth + 1)
    elif type(value) is list:
        for child in cast(list[object], value):
            _tree(child, depth + 1)
    elif type(value) is str:
        _ = _text(value)
    elif value is not None:
        _uint(value)


def canonical_json(value: object) -> bytes:
    """Canonical bounded encoding; no authority is established."""
    _tree(value)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    _require(len(raw) <= MAX_WIRE_BYTES, "wire byte bound")
    return raw


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _scan_depth(raw: bytes) -> None:
    depth, quoted, escaped = 0, False, False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            _require(depth <= MAX_DEPTH, "nesting bound")
        elif byte in (93, 125):
            depth -= 1


def _parse(raw: bytes) -> dict[str, object]:
    _require(type(raw) is bytes and 0 < len(raw) <= MAX_WIRE_BYTES, "wire byte bound/type")
    _scan_depth(raw)
    try:
        value = cast(object, json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs))
    except (UnicodeError, ValueError, RecursionError) as error:
        raise GuardedReplacementContractError("invalid JSON") from error
    _require(canonical_json(value) == raw, "noncanonical wire")
    return _mapping(value)


def _local_invariants(value: object) -> None:
    if type(value) is list:
        for entry in cast(list[object], value):
            _local_invariants(entry)
        return
    if type(value) is not dict:
        return
    data = cast(dict[str, object], value)
    if set(data) == {"digest", "size"}:
        _require(cast(int, data["size"]) <= MAX_CONTENT_BYTES, "content size bound")
    if "link_count" in data:
        _require(data["link_count"] == 1 and data["mode"] in (384, 416), "unsupported file metadata")
    if "observation" in data:
        observation = _mapping(data["observation"])
        _require(data["repository_binding_ref"] == observation["repository_binding_ref"], "coordinate binding disagreement")
        _require(data["state_digest"] == observation["snapshot_digest"], "coordinate digest disagreement")
    for child in data.values():
        _local_invariants(child)


def validate_body(body: object) -> None:
    """Validate claims, not issuance. External references remain unqualified."""
    _tree(body)
    data = _mapping(body)
    schema = _text(data.get("schema"))
    _require(schema in BODY_SCHEMAS, "unknown body schema")
    name = schema[len(PREFIX):]
    _shapes[name]({key: value for key, value in data.items() if key != "schema"})
    _local_invariants(data)
    if name == "admission.v1":
        coordinate = _mapping(data["expected_coordinate"])
        _require(data["workspace_binding_ref"] == coordinate["repository_binding_ref"], "admission source binding disagreement")
    if name == "issuer-appointment.v1":
        public_key = bytes.fromhex(cast(str, data["public_key"]))
        _require(data["key_id"] == "sha256:" + hashlib.sha256(public_key).hexdigest(), "public key digest disagreement")
        expected = sorted(PREFIX + item for item in _role_schemas[cast(str, data["role"])])
        _require(data["allowed_schemas"] == expected, "role schema disagreement")
    if name in ("live.v1", "grant.v1", "workspace-source-admission.v1"):
        start_key = "observed_boottime_ns" if name == "live.v1" else "issued_boottime_ns"
        delta = cast(int, data["expires_boottime_ns"]) - cast(int, data[start_key])
        _require(delta > 0 and (name != "live.v1" or delta <= LIVE_WINDOW_NS), "invalid expiry window")
    if name == "fence.v1" and data["mode"] == "fresh_start":
        _require(data["prior_processes"] == [], "fresh-start process contradiction")
    if name == "refusal.v1":
        _require((data["status"] == "conflict") == (data["reason"] == "preimage_conflict"), "refusal contradiction")
    if name == "result.v1":
        status, stage, reason = data["status"], data["stage"], data["reason"]
        if status == "applied":
            _require(data["after"] is not None and stage == "complete" and reason == "none" and data["terminal_live_ref"] is not None, "applied contradiction")
        elif status == "unapplied":
            _require(data["after"] is None and stage in ("admitted", "staged") and reason in ("authority_refused", "cancelled_before_replace"), "unapplied contradiction")
        else:
            _require(data["after"] is None and reason in ("effect_uncertain", "sync_failed", "recovery_required"), "uncertain contradiction")
    if name == "journal-result.v1":
        if data["stage"] in ("durable", "complete"):
            _require(data["after"] is not None and data["replacement"] == "complete" and data["file_sync"] == "complete" and data["directory_sync"] == "complete", "durable journal contradiction")
        if data["stage"] in ("admitted", "staged"):
            _require(data["after"] is None and data["replacement"] == "not_started", "pre-effect journal contradiction")


def derive_body_ref(body: object) -> str:
    validate_body(body)
    data = _mapping(body)
    schema = cast(str, data["schema"])
    return schema + ":sha256:" + hashlib.sha256(schema.encode("ascii") + b"\0" + canonical_json(data)).hexdigest()


def validate_record(record: object) -> None:
    data = _mapping(record)
    if data.get("schema") != PREFIX + "signed.v1":
        validate_body(data)
        return
    _object(schema=_enum(PREFIX + "signed.v1"), body=validate_body, body_ref=_id,
            issuer_id=_id, key_id=_digest, signature_profile=_enum("ed25519_v1"), signature=_hex64)(data)
    _require(_mapping(data["body"])["schema"] != PREFIX + "refusal.v1", "refusal cannot assert signature authority")
    _require(data["body_ref"] == derive_body_ref(data["body"]), "body reference disagreement")


def encode_record(record: object) -> bytes:
    validate_record(record)
    return canonical_json(record)


def decode_record(raw: bytes) -> dict[str, object]:
    """Return a fresh mutable UNVERIFIED transport mapping, never a capability."""
    data = _parse(raw)
    validate_record(data)
    return data


def signature_input(record: object) -> bytes:
    """Bytes to sign/verify later with an admitted issuer, NOT crypto verification."""
    validate_record(record)
    data = _mapping(record)
    _require(data["schema"] == PREFIX + "signed.v1", "expected signed envelope")
    fields = {key: data[key] for key in ("body_ref", "issuer_id", "key_id", "signature_profile")}
    return (PREFIX + "signature.v1").encode("ascii") + b"\0" + canonical_json(fields)


def encode_replacement_bytes(content: bytes) -> str:
    """Separate bounded content transport; never embeds bytes in authority."""
    _require(type(content) is bytes and len(content) <= MAX_CONTENT_BYTES, "replacement byte bound/type")
    return base64.urlsafe_b64encode(content).decode("ascii").rstrip("=")


def decode_replacement_bytes(encoded: str) -> bytes:
    _require(type(encoded) is str and len(encoded) <= (MAX_CONTENT_BYTES * 4 + 2) // 3, "replacement encoding bound/type")
    _require(re.fullmatch(r"[A-Za-z0-9_-]*", encoded) is not None, "noncanonical base64url")
    try:
        content = base64.b64decode(encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
    except (ValueError, binascii.Error) as error:
        raise GuardedReplacementContractError("invalid base64url") from error
    _require(encode_replacement_bytes(content) == encoded, "noncanonical base64url bits")
    return content


def validate_result_links(*, result: object, admission: object, journal: object, terminal_live: object | None) -> None:
    """Pure supplied-body integrity/consistency join. Does NOT qualify any source."""
    for body in (result, admission, journal):
        validate_body(body)
    r, a, j = _mapping(result), _mapping(admission), _mapping(journal)
    _require(r["schema"] == PREFIX + "result.v1" and a["schema"] == PREFIX + "admission.v1" and j["schema"] == PREFIX + "journal-result.v1", "wrong join schemas")
    _require(r["admission_ref"] == j["admission_ref"] == derive_body_ref(a), "admission link disagreement")
    _require(r["journal_result_ref"] == derive_body_ref(j), "journal link disagreement")
    _require(j["journal_intent_ref"] == a["journal_intent_ref"], "intent link disagreement")
    for name in ("deployment_ref", "operation_ref", "idempotency_key", "activation_sequence"):
        _require(r[name] == a[name], "operation link disagreement")
    _require(r["after"] == j["after"] and r["stage"] == j["stage"], "journal/result disagreement")
    if r["status"] == "applied":
        after, before = _mapping(r["after"]), _mapping(a["before"])
        _require(after["content"] == a["replacement"], "replacement disagreement")
        _require(all(after[key] == before[key] for key in ("uid", "gid", "mode", "device_major", "device_minor")), "metadata changed")
    if r["status"] == "unapplied":
        _require(j["replacement"] == "not_started", "unapplied replacement contradiction")
    if terminal_live is not None:
        validate_body(terminal_live)
        live = _mapping(terminal_live)
        _require(live["schema"] == PREFIX + "live.v1" and r["terminal_live_ref"] == derive_body_ref(live), "terminal live link disagreement")
        _require(live["deployment_ref"] == a["deployment_ref"] and live["activation_sequence"] == a["activation_sequence"] and live["session_id"] == a["session_id"] and live["state"] == "active", "terminal live/session disagreement")
    else:
        _require(r["terminal_live_ref"] is None, "missing referenced terminal body")
