"""Original local intent issuer using its retained Project attempt.

No Git writer, Goal semantics, replacement or alternate authority store.
Owner-private local retention is not Identity or protection against same-UID
attackers. A damaged/interrupted record refuses; it is never adopted or repaired.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime, timedelta

from aware_workspace_sdk.initial_authoring.goal_source import _state as _source_state
from aware_workspace_sdk.initial_authoring.values import _canonical, initial_reference

from .initial_authoring import _private, _read_record, _write_record, project_attempt

_RECORD = "goal-intent.json"


def _content(facts, payload, key):
    return {
        "schema_id": "aware.workspace.initial-goal-intent-permission.v1",
        "profile": "repository_initial_authoring_v1",
        "operation_key": "authorize_proposed_goal_intent",
        "source": facts,
        "intent_utf8": payload.decode("utf-8"),
        "intent_sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
        "idempotency_key": key,
        "issuer_ref": facts["issuer_ref"],
        "issuer_generation": facts["issuer_generation"],
        "publication_admission": "not_issued",
    }


def _source(port, context):
    state = _source_state(context)
    if state.owner._physical is not port:
        raise ValueError("initial_goal_intent_foreign_provider")
    return state, context.require_current()


def _validate(record, expected):
    if type(record) is not dict or set(record) != {
        *expected,
        "issued_at",
        "expires_at",
        "permission_ref",
    }:
        raise ValueError("initial_goal_intent_record_invalid")
    if _canonical({k: record[k] for k in expected}) != _canonical(expected):
        raise ValueError("initial_goal_intent_record_binding_mismatch")
    if type(record["issued_at"]) is not str or type(record["expires_at"]) is not str:
        raise ValueError("initial_goal_intent_times_invalid")
    issued = datetime.fromisoformat(record["issued_at"])
    expires = datetime.fromisoformat(record["expires_at"])
    if (
        issued.utcoffset() != timedelta(0)
        or expires.utcoffset() != timedelta(0)
        or expires - issued != timedelta(seconds=300)
        or issued.isoformat(timespec="microseconds") != record["issued_at"]
        or expires.isoformat(timespec="microseconds") != record["expires_at"]
    ):
        raise ValueError("initial_goal_intent_times_invalid")
    body = {k: v for k, v in record.items() if k != "permission_ref"}
    if record["permission_ref"] != initial_reference(
        "workspace-initial-goal-intent-permission", body
    ):
        raise ValueError("initial_goal_intent_reference_invalid")
    return record


def authorize(port, claim):
    from aware_workspace_sdk.initial_authoring.goal_intent import _spend_claim

    context, payload, key, _, _ = _spend_claim(port, claim)
    state, facts = _source(port, context)
    issued = datetime.now(UTC)
    body = {
        **_content(facts, payload, key),
        "issued_at": issued.isoformat(timespec="microseconds"),
        "expires_at": (issued + timedelta(seconds=300)).isoformat(
            timespec="microseconds"
        ),
    }
    record = {
        **body,
        "permission_ref": initial_reference(
            "workspace-initial-goal-intent-permission", body
        ),
    }
    if len(_canonical(record)) + 1 > 262144:
        raise ValueError("initial_goal_intent_record_limit")
    with project_attempt(port, state.project_request) as attempt:
        if _RECORD in os.listdir(attempt.directory):
            raise ValueError("initial_goal_intent_already_reserved")
        _write_record(attempt.directory, _RECORD, record)
        if _canonical(
            _validate(
                _read_record(attempt.directory, _RECORD), _content(facts, payload, key)
            )
        ) != _canonical(record):
            raise ValueError("initial_goal_intent_reread_mismatch")
    # A terminal source change leaves the durable claim but issues no live
    # permission. Nothing here is authorization to retry or dispatch a writer.
    if _canonical(context.require_current()) != _canonical(facts):
        raise ValueError("initial_goal_intent_source_changed")
    return record


def observe(port, context, payload, key):
    state, facts = _source(port, context)
    with project_attempt(port, state.project_request) as attempt:
        record = _validate(
            _read_record(attempt.directory, _RECORD), _content(facts, payload, key)
        )
        descriptor = os.open(
            _RECORD,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=attempt.directory,
        )
        try:
            _private(os.fstat(descriptor), 0o600)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(attempt.directory)
        if _canonical(_read_record(attempt.directory, _RECORD)) != _canonical(record):
            raise ValueError("initial_goal_intent_reread_mismatch")
    if _canonical(context.require_current()) != _canonical(facts):
        raise ValueError("initial_goal_intent_source_changed")
    return record
