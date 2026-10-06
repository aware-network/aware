from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

from .contracts import (
    AuthorityKind,
    IntentRecord,
    IssueAuthorityEvidence,
    IssueEvidenceRef,
    IssueOperationalState,
    IssueOwnershipScopePath,
    IssueSnapshot,
    IssueStatus,
    IssueTimeAuthority,
    IssueUpdateLogEntry,
    ReconciliationState,
    ReconciliationStatus,
    TransitionOutcome,
)
from .journal import (
    IssueEvent,
    IssueEventKind,
    IssueJournal,
    IssueOperationalRecord,
)

CODEC_NAME = "aware.workflow.issue-operational-record"
CODEC_VERSION = 1


def encode_operational_record(record: IssueOperationalRecord) -> str:
    payload = {
        "codec": CODEC_NAME,
        "version": CODEC_VERSION,
        "authority_ref": record.authority_ref,
        "state": record.state.to_wire(),
        "journal": record.journal.to_wire(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def decode_operational_record(payload: str) -> IssueOperationalRecord:
    if not isinstance(payload, str) or not payload:
        raise ValueError("payload must be non-empty JSON text")
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid issue operational JSON") from exc
    root = _object(raw, "record")
    _keys(root, {"codec", "version", "authority_ref", "state", "journal"}, "record")
    if root["codec"] != CODEC_NAME or root["version"] != CODEC_VERSION:
        raise ValueError("unsupported issue operational codec")
    return IssueOperationalRecord(
        authority_ref=_string(root["authority_ref"], "authority_ref"),
        state=_state(_object(root["state"], "state")),
        journal=_journal(_object(root["journal"], "journal")),
    )


def _state(raw: Mapping[str, object]) -> IssueOperationalState:
    _keys(raw, {"authority", "issues", "intent_records"}, "state")
    return IssueOperationalState(
        authority=_authority(_object(raw["authority"], "authority")),
        issues=tuple(
            _issue(_object(item, "issue")) for item in _list(raw["issues"], "issues")
        ),
        intent_records=tuple(
            _intent_record(_object(item, "intent_record"))
            for item in _list(raw["intent_records"], "intent_records")
        ),
    )


def _authority(raw: Mapping[str, object]) -> IssueAuthorityEvidence:
    _keys(
        raw,
        {
            "kind",
            "provider_key",
            "authority_ref",
            "generation",
            "receipt_ref",
            "reconciliation",
        },
        "authority",
    )
    reconciliation = raw["reconciliation"]
    return IssueAuthorityEvidence(
        kind=AuthorityKind(_string(raw["kind"], "kind")),
        provider_key=_string(raw["provider_key"], "provider_key"),
        authority_ref=_string(raw["authority_ref"], "authority_ref"),
        generation=_integer(raw["generation"], "generation"),
        receipt_ref=_nullable_string(raw["receipt_ref"], "receipt_ref"),
        reconciliation=(
            None
            if reconciliation is None
            else _reconciliation(_object(reconciliation, "reconciliation"))
        ),
    )


def _reconciliation(raw: Mapping[str, object]) -> ReconciliationState:
    _keys(
        raw,
        {"status", "canonical_authority_ref", "evidence_ref", "reason"},
        "reconciliation",
    )
    return ReconciliationState(
        status=ReconciliationStatus(_string(raw["status"], "status")),
        canonical_authority_ref=_nullable_string(
            raw["canonical_authority_ref"], "canonical_authority_ref"
        ),
        evidence_ref=_nullable_string(raw["evidence_ref"], "evidence_ref"),
        reason=_nullable_string(raw["reason"], "reason"),
    )


def _issue(raw: Mapping[str, object]) -> IssueSnapshot:
    _keys(
        raw,
        {
            "issue_ref",
            "tag",
            "title",
            "status",
            "priority_level",
            "owner_session_id",
            "overview_content_ref",
            "scope_paths",
            "updates",
            "evidence_refs",
            "authority",
            "revision",
        },
        "issue",
    )
    return IssueSnapshot(
        issue_ref=_string(raw["issue_ref"], "issue_ref"),
        tag=_string(raw["tag"], "tag"),
        title=_string(raw["title"], "title"),
        status=IssueStatus(_string(raw["status"], "status")),
        priority_level=_string(raw["priority_level"], "priority_level"),
        owner_session_id=_nullable_string(raw["owner_session_id"], "owner_session_id"),
        overview_content_ref=_nullable_string(
            raw["overview_content_ref"], "overview_content_ref"
        ),
        scope_paths=tuple(
            IssueOwnershipScopePath(
                relative_path=_string(
                    _object(item, "scope_path")["relative_path"], "relative_path"
                )
            )
            for item in _list(raw["scope_paths"], "scope_paths")
        ),
        updates=tuple(
            _update(_object(item, "update"))
            for item in _list(raw["updates"], "updates")
        ),
        evidence_refs=tuple(
            _evidence(_object(item, "evidence"))
            for item in _list(raw["evidence_refs"], "evidence_refs")
        ),
        authority=_authority(_object(raw["authority"], "authority")),
        revision=_integer(raw["revision"], "revision"),
    )


def _update(raw: Mapping[str, object]) -> IssueUpdateLogEntry:
    _keys(
        raw,
        {
            "sequence",
            "message",
            "actor_ref",
            "actor_evidence_ref",
            "outcome",
            "command",
            "command_exit_code",
            "recorded_at",
            "time_authority",
        },
        "update",
    )
    exit_code = raw["command_exit_code"]
    return IssueUpdateLogEntry(
        sequence=_integer(raw["sequence"], "sequence"),
        message=_string(raw["message"], "message"),
        actor_ref=_string(raw["actor_ref"], "actor_ref"),
        actor_evidence_ref=_string(raw["actor_evidence_ref"], "actor_evidence_ref"),
        outcome=_string(raw["outcome"], "outcome"),
        command=_nullable_string(raw["command"], "command"),
        command_exit_code=(
            None if exit_code is None else _integer(exit_code, "command_exit_code")
        ),
        recorded_at=_nullable_string(raw["recorded_at"], "recorded_at"),
        time_authority=IssueTimeAuthority(
            _string(raw["time_authority"], "time_authority")
        ),
    )


def _evidence(raw: Mapping[str, object]) -> IssueEvidenceRef:
    _keys(raw, {"sequence", "path", "description"}, "evidence")
    return IssueEvidenceRef(
        sequence=_integer(raw["sequence"], "sequence"),
        path=_string(raw["path"], "path"),
        description=_nullable_string(raw["description"], "description"),
    )


def _intent_record(raw: Mapping[str, object]) -> IntentRecord:
    _keys(
        raw,
        {"client_intent_id", "fingerprint", "outcome", "affected_refs"},
        "intent_record",
    )
    return IntentRecord(
        client_intent_id=_string(raw["client_intent_id"], "client_intent_id"),
        fingerprint=_string(raw["fingerprint"], "fingerprint"),
        outcome=TransitionOutcome(_string(raw["outcome"], "outcome")),
        affected_refs=tuple(
            _string(item, "affected_ref")
            for item in _list(raw["affected_refs"], "affected_refs")
        ),
    )


def _journal(raw: Mapping[str, object]) -> IssueJournal:
    _keys(raw, {"epoch", "retention_limit", "next_cursor", "events"}, "journal")
    return IssueJournal(
        epoch=_string(raw["epoch"], "epoch"),
        retention_limit=_integer(raw["retention_limit"], "retention_limit"),
        next_cursor=_integer(raw["next_cursor"], "next_cursor"),
        events=tuple(
            _event(_object(item, "event")) for item in _list(raw["events"], "events")
        ),
    )


def _event(raw: Mapping[str, object]) -> IssueEvent:
    _keys(
        raw,
        {
            "event_ref",
            "authority_ref",
            "epoch",
            "cursor",
            "kind",
            "authority_generation",
            "issue_ref",
            "issue_revision",
            "receipt_ref",
            "affected_refs",
        },
        "event",
    )
    issue_revision = raw["issue_revision"]
    return IssueEvent(
        event_ref=_string(raw["event_ref"], "event_ref"),
        authority_ref=_string(raw["authority_ref"], "authority_ref"),
        epoch=_string(raw["epoch"], "epoch"),
        cursor=_integer(raw["cursor"], "cursor"),
        kind=IssueEventKind(_string(raw["kind"], "kind")),
        authority_generation=_integer(
            raw["authority_generation"], "authority_generation"
        ),
        issue_ref=_nullable_string(raw["issue_ref"], "issue_ref"),
        issue_revision=(
            None
            if issue_revision is None
            else _integer(issue_revision, "issue_revision")
        ),
        receipt_ref=_string(raw["receipt_ref"], "receipt_ref"),
        affected_refs=tuple(
            _string(item, "affected_ref")
            for item in _list(raw["affected_refs"], "affected_refs")
        ),
    )


def _keys(raw: Mapping[str, object], expected: set[str], label: str) -> None:
    if set(raw) != expected:
        raise ValueError(f"{label} keys do not match contract")


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be an object")
    return cast(Mapping[str, object], value)


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a list")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    return value


def _nullable_string(value: object, label: str) -> str | None:
    return None if value is None else _string(value, label)


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    return value
