from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, NoReturn, cast

from .contracts import AuthorityKind, IssueSnapshot, IssueStatus, IssueTimeAuthority
from .journal import IssueEvent, IssueEventKind

WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA = (
    "aware.workflow.issue-activity-observation.v1"
)
MAX_WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_BYTES = 16_777_216
_MAX_UINT = 9_007_199_254_740_991
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


class WorkflowIssueActivityObservationError(ValueError):
    pass


class WorkflowIssueActivitySelectionKind(StrEnum):
    CURRENT = "current"
    HISTORICAL = "historical"


class WorkflowIssueActivityOutcomeKind(StrEnum):
    SELECTED = "selected"
    UNAVAILABLE = "unavailable"


class WorkflowIssueActivityUnavailableReason(StrEnum):
    AUTHORITY_UNAVAILABLE = "authority_unavailable"
    ISSUE_UNAVAILABLE = "issue_unavailable"
    ACTIVITY_UNAVAILABLE = "activity_unavailable"
    HISTORY_NOT_RETAINED = "history_not_retained"
    ACTIVITY_STATE_UNAVAILABLE = "activity_state_unavailable"
    ACTIVITY_TIME_UNAVAILABLE = "activity_time_unavailable"
    AMBIGUOUS = "ambiguous"
    STALE = "stale"
    CONFLICTING = "conflicting"


def _fail(code: str) -> NoReturn:
    raise WorkflowIssueActivityObservationError(code)


def _text(value: object, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if type(value) is not str:
        _fail("invalid_text")
    result = cast(str, value)
    if not result or unicodedata.normalize("NFC", result) != result:
        _fail("invalid_text")
    if any(
        ord(char) < 32 or 127 <= ord(char) <= 159 or 0xD800 <= ord(char) <= 0xDFFF
        for char in result
    ):
        _fail("invalid_text")
    return result


def _uint(value: object, *, positive: bool = False) -> int:
    if type(value) is not int:
        _fail("invalid_integer")
    result = cast(int, value)
    if not 0 <= result <= _MAX_UINT or (positive and result == 0):
        _fail("invalid_integer")
    return result


def _timestamp(value: object) -> str:
    result = cast(str, _text(value))
    if not _UTC.fullmatch(result):
        _fail("invalid_timestamp")
    try:
        if datetime.fromisoformat(result).strftime("%Y-%m-%dT%H:%M:%SZ") != result:
            _fail("invalid_timestamp")
    except ValueError as exc:
        raise WorkflowIssueActivityObservationError("invalid_timestamp") from exc
    return result


def _schema(value: str) -> None:
    if value != WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA:
        _fail("schema_mismatch")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def _digest(domain: str, body: dict[str, object]) -> str:
    return (
        "sha256:"
        + hashlib.sha256(domain.encode() + b"\0" + _canonical(body)).hexdigest()
    )


def _ref(prefix: str, digest: str) -> str:
    return prefix + digest.removeprefix("sha256:")


def _exact_enum(value: object, cls: type[StrEnum]) -> None:
    if type(value) is not cls:
        _fail("foreign_enum")


def _validate_snapshot(value: object) -> IssueSnapshot:
    if type(value) is not IssueSnapshot:
        _fail("foreign_snapshot")
    # Existing construction owns its graph invariants. Exact nested types are checked
    # before its wire behavior is used.
    from .contracts import (
        IssueAuthorityEvidence,
        IssueEvidenceRef,
        IssueOwnershipScopePath,
        IssueUpdateLogEntry,
        ReconciliationState,
    )

    snapshot = cast(IssueSnapshot, value)
    if type(snapshot.authority) is not IssueAuthorityEvidence:
        _fail("foreign_snapshot")
    if (
        snapshot.authority.reconciliation is not None
        and type(snapshot.authority.reconciliation) is not ReconciliationState
    ):
        _fail("foreign_snapshot")
    if type(snapshot.scope_paths) is not tuple or any(
        type(x) is not IssueOwnershipScopePath for x in snapshot.scope_paths
    ):
        _fail("foreign_snapshot")
    if type(snapshot.updates) is not tuple or any(
        type(x) is not IssueUpdateLogEntry for x in snapshot.updates
    ):
        _fail("foreign_snapshot")
    if type(snapshot.evidence_refs) is not tuple or any(
        type(x) is not IssueEvidenceRef for x in snapshot.evidence_refs
    ):
        _fail("foreign_snapshot")
    _exact_enum(snapshot.status, IssueStatus)
    _exact_enum(snapshot.authority.kind, AuthorityKind)
    for update in snapshot.updates:
        _exact_enum(update.time_authority, IssueTimeAuthority)
    return snapshot


def _validate_event(value: object) -> IssueEvent:
    if type(value) is not IssueEvent or type(value.affected_refs) is not tuple:
        _fail("foreign_event")
    event = cast(IssueEvent, value)
    _exact_enum(event.kind, IssueEventKind)
    return event


def _snapshot_wire(value: IssueSnapshot) -> dict[str, object]:
    return _validate_snapshot(value).to_wire()


def _event_wire(value: IssueEvent) -> dict[str, object]:
    return _validate_event(value).to_wire()


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowIssueActivityOwnerObservationV1:
    schema_version: str
    authority_kind: AuthorityKind
    authority_ref: str
    authority_generation: int
    authority_receipt_ref: str | None
    store_generation: int
    journal_epoch: str
    earliest_cursor: int
    latest_cursor: int | None
    next_cursor: int
    owner_observation_ref: str
    owner_observation_digest: str

    def __post_init__(self) -> None:
        _validated_owner(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowIssueActivityHeadV1:
    schema_version: str
    owner_observation: WorkflowIssueActivityOwnerObservationV1
    authority_kind: AuthorityKind
    authority_ref: str
    authority_generation: int
    authority_receipt_ref: str | None
    issue_ref: str
    issue_revision: int
    issue_revision_ref: str
    lifecycle_state: IssueStatus
    owner_ref: str | None
    issue_snapshot: IssueSnapshot
    issue_snapshot_digest: str
    head_ref: str
    head_digest: str

    def __post_init__(self) -> None:
        body = _head_body(self)
        _check_identity(
            self,
            body,
            "aware.workflow.issue-activity.head.v1",
            "workflow-issue-activity-head:",
            "head_ref",
            "head_digest",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowIssueActivityMemberV1:
    schema_version: str
    owner_observation: WorkflowIssueActivityOwnerObservationV1
    authority_ref: str
    authority_generation: int
    journal_epoch: str
    event_ref: str
    event_cursor: int
    event_kind: IssueEventKind
    issue_ref: str
    issue_revision: int
    issue_revision_ref: str
    lifecycle_state: IssueStatus
    activity_at: str
    activity_time_authority: IssueTimeAuthority
    actor_execution_ref: str | None
    source_receipt_ref: str
    affected_refs: tuple[str, ...]
    issue_snapshot: IssueSnapshot
    issue_snapshot_digest: str
    event: IssueEvent
    activity_ref: str
    activity_digest: str

    def __post_init__(self) -> None:
        body = _member_body(self)
        _check_identity(
            self,
            body,
            "aware.workflow.issue-activity.member.v1",
            "workflow-issue-activity:",
            "activity_ref",
            "activity_digest",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowIssueActivityUnavailableV1:
    schema_version: str
    owner_observation: WorkflowIssueActivityOwnerObservationV1
    authority_kind: AuthorityKind
    authority_ref: str
    authority_generation: int
    authority_receipt_ref: str | None
    store_generation: int
    journal_epoch: str
    issue_ref: str
    selection_kind: WorkflowIssueActivitySelectionKind
    requested_issue_revision_ref: str | None
    reason: WorkflowIssueActivityUnavailableReason
    detail: str
    observed_at: str
    unavailable_ref: str
    unavailable_digest: str

    def __post_init__(self) -> None:
        body = _unavailable_body(self)
        _check_identity(
            self,
            body,
            "aware.workflow.issue-activity.unavailable.v1",
            "workflow-issue-activity-unavailable:",
            "unavailable_ref",
            "unavailable_digest",
        )


ActivityOutcome = WorkflowIssueActivityMemberV1 | WorkflowIssueActivityUnavailableV1


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowIssueActivityHorizonV1:
    schema_version: str
    owner_observation: WorkflowIssueActivityOwnerObservationV1
    observed_at: str
    heads: tuple[WorkflowIssueActivityHeadV1, ...]
    outcome_coordinates: tuple[tuple[str, str], ...]
    head_closure_digest: str
    outcome_closure_digest: str
    horizon_ref: str
    horizon_digest: str

    def __post_init__(self) -> None:
        body = _horizon_structural_body(self)
        _check_identity(
            self,
            body,
            "aware.workflow.issue-activity.horizon.v1",
            "workflow-issue-activity-horizon:",
            "horizon_ref",
            "horizon_digest",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowIssueActivitySelectionV1:
    schema_version: str
    horizon_ref: str
    horizon_digest: str
    selection_kind: WorkflowIssueActivitySelectionKind
    issue_ref: str
    requested_issue_revision_ref: str | None
    outcome_kind: WorkflowIssueActivityOutcomeKind
    outcome_ref: str
    outcome_digest: str
    selection_ref: str
    selection_digest: str

    def __post_init__(self) -> None:
        body = _selection_body(self)
        _check_identity(
            self,
            body,
            "aware.workflow.issue-activity.selection.v1",
            "workflow-issue-activity-selection:",
            "selection_ref",
            "selection_digest",
        )


def _unchecked[T](cls: type[T], fields: Mapping[str, object]) -> T:
    value = object.__new__(cls)
    for name, item in fields.items():
        object.__setattr__(value, name, item)
    return cast(T, value)


def _owner_body(value: WorkflowIssueActivityOwnerObservationV1) -> dict[str, object]:
    if type(value) is not WorkflowIssueActivityOwnerObservationV1:
        _fail("foreign_owner_observation")
    _exact_enum(value.authority_kind, AuthorityKind)
    _schema(value.schema_version)
    _text(value.authority_ref)
    _text(value.authority_receipt_ref, nullable=True)
    _text(value.journal_epoch)
    _uint(value.authority_generation)
    _uint(value.store_generation)
    _uint(value.earliest_cursor, positive=True)
    _uint(value.next_cursor, positive=True)
    if value.latest_cursor is None:
        if value.earliest_cursor != value.next_cursor:
            _fail("invalid_journal_bounds")
    else:
        _uint(value.latest_cursor, positive=True)
        if (
            value.earliest_cursor > value.latest_cursor
            or value.next_cursor != value.latest_cursor + 1
        ):
            _fail("invalid_journal_bounds")
    return {
        name: getattr(value, name)
        if name != "authority_kind"
        else value.authority_kind.value
        for name in (
            "schema_version",
            "authority_kind",
            "authority_ref",
            "authority_generation",
            "authority_receipt_ref",
            "store_generation",
            "journal_epoch",
            "earliest_cursor",
            "latest_cursor",
            "next_cursor",
        )
    }


def _check_identity(
    value: object,
    body: dict[str, object],
    domain: str,
    prefix: str,
    ref_name: str,
    digest_name: str,
) -> None:
    expected = _digest(domain, body)
    if getattr(value, digest_name) != expected or getattr(value, ref_name) != _ref(
        prefix, expected
    ):
        _fail("identity_mismatch")


def derive_workflow_issue_activity_owner_observation(
    *,
    authority_kind: AuthorityKind,
    authority_ref: str,
    authority_generation: int,
    authority_receipt_ref: str | None,
    store_generation: int,
    journal_epoch: str,
    earliest_cursor: int,
    latest_cursor: int | None,
    next_cursor: int,
) -> WorkflowIssueActivityOwnerObservationV1:
    fields: dict[str, Any] = {
        "schema_version": WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
        "authority_kind": authority_kind,
        "authority_ref": authority_ref,
        "authority_generation": authority_generation,
        "authority_receipt_ref": authority_receipt_ref,
        "store_generation": store_generation,
        "journal_epoch": journal_epoch,
        "earliest_cursor": earliest_cursor,
        "latest_cursor": latest_cursor,
        "next_cursor": next_cursor,
        "owner_observation_ref": "",
        "owner_observation_digest": "",
    }
    seed = _unchecked(WorkflowIssueActivityOwnerObservationV1, fields)
    body = _owner_body(seed)
    digest = _digest("aware.workflow.issue-activity.owner-observation.v1", body)
    return _unchecked(
        WorkflowIssueActivityOwnerObservationV1,
        {
            **fields,
            "owner_observation_ref": _ref(
                "workflow-issue-activity-owner-observation:", digest
            ),
            "owner_observation_digest": digest,
        },
    )


def _validated_owner(
    value: WorkflowIssueActivityOwnerObservationV1,
) -> dict[str, object]:
    body = _owner_body(value)
    _check_identity(
        value,
        body,
        "aware.workflow.issue-activity.owner-observation.v1",
        "workflow-issue-activity-owner-observation:",
        "owner_observation_ref",
        "owner_observation_digest",
    )
    return body


def _snapshot_digest(snapshot: IssueSnapshot) -> str:
    return _digest(
        "aware.workflow.issue-snapshot.observation.v1", _snapshot_wire(snapshot)
    )


def _issue_revision_ref(issue_ref: str, revision: int) -> str:
    return f"{issue_ref}:revision:{revision}"


def _head_body(value: WorkflowIssueActivityHeadV1) -> dict[str, object]:
    _schema(value.schema_version)
    _exact_enum(value.authority_kind, AuthorityKind)
    _exact_enum(value.lifecycle_state, IssueStatus)
    _validated_owner(value.owner_observation)
    snapshot = _validate_snapshot(value.issue_snapshot)
    authority = snapshot.authority
    if (
        value.authority_kind,
        value.authority_ref,
        value.authority_generation,
        value.authority_receipt_ref,
    ) != (
        authority.kind,
        authority.authority_ref,
        authority.generation,
        authority.receipt_ref,
    ) or (
        authority.kind,
        authority.authority_ref,
        authority.generation,
        authority.receipt_ref,
    ) != (
        value.owner_observation.authority_kind,
        value.owner_observation.authority_ref,
        value.owner_observation.authority_generation,
        value.owner_observation.authority_receipt_ref,
    ):
        _fail("head_authority_mismatch")
    if (
        value.issue_ref,
        value.issue_revision,
        value.issue_revision_ref,
        value.lifecycle_state,
        value.owner_ref,
    ) != (
        snapshot.issue_ref,
        snapshot.revision,
        _issue_revision_ref(snapshot.issue_ref, snapshot.revision),
        snapshot.status,
        snapshot.owner_session_id,
    ):
        _fail("head_snapshot_mismatch")
    if value.issue_snapshot_digest != _snapshot_digest(snapshot):
        _fail("snapshot_digest_mismatch")
    return {
        "schema_version": value.schema_version,
        "owner_observation": _owner_wire(value.owner_observation),
        "authority_kind": value.authority_kind.value,
        "authority_ref": value.authority_ref,
        "authority_generation": value.authority_generation,
        "authority_receipt_ref": value.authority_receipt_ref,
        "issue_ref": value.issue_ref,
        "issue_revision": value.issue_revision,
        "issue_revision_ref": value.issue_revision_ref,
        "lifecycle_state": value.lifecycle_state.value,
        "owner_ref": value.owner_ref,
        "issue_snapshot": _snapshot_wire(snapshot),
        "issue_snapshot_digest": value.issue_snapshot_digest,
    }


def derive_workflow_issue_activity_head(
    *,
    owner_observation: WorkflowIssueActivityOwnerObservationV1,
    issue_snapshot: IssueSnapshot,
) -> WorkflowIssueActivityHeadV1:
    snapshot = _validate_snapshot(issue_snapshot)
    sd = _snapshot_digest(snapshot)
    base: dict[str, Any] = {
        "schema_version": WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
        "owner_observation": owner_observation,
        "authority_kind": snapshot.authority.kind,
        "authority_ref": snapshot.authority.authority_ref,
        "authority_generation": snapshot.authority.generation,
        "authority_receipt_ref": snapshot.authority.receipt_ref,
        "issue_ref": snapshot.issue_ref,
        "issue_revision": snapshot.revision,
        "issue_revision_ref": _issue_revision_ref(
            snapshot.issue_ref, snapshot.revision
        ),
        "lifecycle_state": snapshot.status,
        "owner_ref": snapshot.owner_session_id,
        "issue_snapshot": snapshot,
        "issue_snapshot_digest": sd,
    }
    seed = _unchecked(
        WorkflowIssueActivityHeadV1, {**base, "head_ref": "", "head_digest": ""}
    )
    body = _head_body(seed)
    digest = _digest("aware.workflow.issue-activity.head.v1", body)
    return _unchecked(
        WorkflowIssueActivityHeadV1,
        {
            **base,
            "head_ref": _ref("workflow-issue-activity-head:", digest),
            "head_digest": digest,
        },
    )


def _member_body(value: WorkflowIssueActivityMemberV1) -> dict[str, object]:
    _schema(value.schema_version)
    _exact_enum(value.event_kind, IssueEventKind)
    _exact_enum(value.lifecycle_state, IssueStatus)
    _exact_enum(value.activity_time_authority, IssueTimeAuthority)
    _validated_owner(value.owner_observation)
    snapshot = _validate_snapshot(value.issue_snapshot)
    event = _validate_event(value.event)
    if event.issue_ref is None or event.issue_revision is None:
        _fail("event_issue_unavailable")
    if (value.authority_ref, value.authority_generation) != (
        event.authority_ref,
        event.authority_generation,
    ) or (event.authority_ref, event.authority_generation) != (
        snapshot.authority.authority_ref,
        snapshot.authority.generation,
    ):
        _fail("event_authority_mismatch")
    if (
        value.authority_ref != value.owner_observation.authority_ref
        or value.authority_generation > value.owner_observation.authority_generation
        or value.journal_epoch != value.owner_observation.journal_epoch
    ):
        _fail("owner_epoch_mismatch")
    if (
        value.owner_observation.latest_cursor is None
        or not value.owner_observation.earliest_cursor
        <= event.cursor
        <= value.owner_observation.latest_cursor
    ):
        _fail("event_outside_horizon")
    if (
        value.event_ref,
        value.event_cursor,
        value.event_kind,
        value.issue_ref,
        value.issue_revision,
        value.source_receipt_ref,
        value.affected_refs,
    ) != (
        event.event_ref,
        event.cursor,
        event.kind,
        event.issue_ref,
        event.issue_revision,
        event.receipt_ref,
        event.affected_refs,
    ):
        _fail("event_mismatch")
    if (
        value.issue_ref,
        value.issue_revision,
        value.issue_revision_ref,
        value.lifecycle_state,
    ) != (
        snapshot.issue_ref,
        snapshot.revision,
        _issue_revision_ref(snapshot.issue_ref, snapshot.revision),
        snapshot.status,
    ):
        _fail("member_snapshot_mismatch")
    if value.issue_snapshot_digest != _snapshot_digest(snapshot):
        _fail("snapshot_digest_mismatch")
    _timestamp(value.activity_at)
    _exact_enum(value.activity_time_authority, IssueTimeAuthority)
    if value.activity_time_authority is IssueTimeAuthority.UNAVAILABLE:
        _fail("activity_time_unavailable")
    _text(value.actor_execution_ref, nullable=True)
    return {
        "schema_version": value.schema_version,
        "owner_observation": _owner_wire(value.owner_observation),
        "authority_ref": value.authority_ref,
        "authority_generation": value.authority_generation,
        "journal_epoch": value.journal_epoch,
        "event_ref": value.event_ref,
        "event_cursor": value.event_cursor,
        "event_kind": value.event_kind.value,
        "issue_ref": value.issue_ref,
        "issue_revision": value.issue_revision,
        "issue_revision_ref": value.issue_revision_ref,
        "lifecycle_state": value.lifecycle_state.value,
        "activity_at": value.activity_at,
        "activity_time_authority": value.activity_time_authority.value,
        "actor_execution_ref": value.actor_execution_ref,
        "source_receipt_ref": value.source_receipt_ref,
        "affected_refs": list(value.affected_refs),
        "issue_snapshot": _snapshot_wire(snapshot),
        "issue_snapshot_digest": value.issue_snapshot_digest,
        "event": _event_wire(event),
    }


def derive_workflow_issue_activity_member(
    *,
    owner_observation: WorkflowIssueActivityOwnerObservationV1,
    issue_snapshot: IssueSnapshot,
    event: IssueEvent,
    activity_at: str,
    activity_time_authority: IssueTimeAuthority,
    actor_execution_ref: str | None,
) -> WorkflowIssueActivityMemberV1:
    snapshot = _validate_snapshot(issue_snapshot)
    event = _validate_event(event)
    if event.issue_ref is None or event.issue_revision is None:
        _fail("event_issue_unavailable")
    event_issue_ref = cast(str, event.issue_ref)
    event_issue_revision = cast(int, event.issue_revision)
    base: dict[str, Any] = {
        "schema_version": WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
        "owner_observation": owner_observation,
        "authority_ref": event.authority_ref,
        "authority_generation": event.authority_generation,
        "journal_epoch": event.epoch,
        "event_ref": event.event_ref,
        "event_cursor": event.cursor,
        "event_kind": event.kind,
        "issue_ref": event_issue_ref,
        "issue_revision": event_issue_revision,
        "issue_revision_ref": _issue_revision_ref(
            event_issue_ref, event_issue_revision
        ),
        "lifecycle_state": snapshot.status,
        "activity_at": activity_at,
        "activity_time_authority": activity_time_authority,
        "actor_execution_ref": actor_execution_ref,
        "source_receipt_ref": event.receipt_ref,
        "affected_refs": event.affected_refs,
        "issue_snapshot": snapshot,
        "issue_snapshot_digest": _snapshot_digest(snapshot),
        "event": event,
    }
    seed = _unchecked(
        WorkflowIssueActivityMemberV1,
        {**base, "activity_ref": "", "activity_digest": ""},
    )
    body = _member_body(seed)
    digest = _digest("aware.workflow.issue-activity.member.v1", body)
    return _unchecked(
        WorkflowIssueActivityMemberV1,
        {
            **base,
            "activity_ref": _ref("workflow-issue-activity:", digest),
            "activity_digest": digest,
        },
    )


def _unavailable_body(value: WorkflowIssueActivityUnavailableV1) -> dict[str, object]:
    _schema(value.schema_version)
    _exact_enum(value.authority_kind, AuthorityKind)
    _validated_owner(value.owner_observation)
    _exact_enum(value.selection_kind, WorkflowIssueActivitySelectionKind)
    _exact_enum(value.reason, WorkflowIssueActivityUnavailableReason)
    owner = value.owner_observation
    if (
        value.authority_kind,
        value.authority_ref,
        value.authority_generation,
        value.authority_receipt_ref,
        value.store_generation,
        value.journal_epoch,
    ) != (
        owner.authority_kind,
        owner.authority_ref,
        owner.authority_generation,
        owner.authority_receipt_ref,
        owner.store_generation,
        owner.journal_epoch,
    ):
        _fail("owner_epoch_mismatch")
    if (value.selection_kind is WorkflowIssueActivitySelectionKind.CURRENT) != (
        value.requested_issue_revision_ref is None
    ):
        _fail("selection_request_mismatch")
    _text(value.issue_ref)
    _text(value.requested_issue_revision_ref, nullable=True)
    _text(value.detail)
    _timestamp(value.observed_at)
    return {
        "schema_version": value.schema_version,
        "owner_observation": _owner_wire(owner),
        "authority_kind": value.authority_kind.value,
        "authority_ref": value.authority_ref,
        "authority_generation": value.authority_generation,
        "authority_receipt_ref": value.authority_receipt_ref,
        "store_generation": value.store_generation,
        "journal_epoch": value.journal_epoch,
        "issue_ref": value.issue_ref,
        "selection_kind": value.selection_kind.value,
        "requested_issue_revision_ref": value.requested_issue_revision_ref,
        "reason": value.reason.value,
        "detail": value.detail,
        "observed_at": value.observed_at,
    }


def derive_workflow_issue_activity_unavailable(
    *,
    owner_observation: WorkflowIssueActivityOwnerObservationV1,
    issue_ref: str,
    selection_kind: WorkflowIssueActivitySelectionKind,
    requested_issue_revision_ref: str | None,
    reason: WorkflowIssueActivityUnavailableReason,
    detail: str,
    observed_at: str,
) -> WorkflowIssueActivityUnavailableV1:
    owner = owner_observation
    base: dict[str, Any] = {
        "schema_version": WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
        "owner_observation": owner,
        "authority_kind": owner.authority_kind,
        "authority_ref": owner.authority_ref,
        "authority_generation": owner.authority_generation,
        "authority_receipt_ref": owner.authority_receipt_ref,
        "store_generation": owner.store_generation,
        "journal_epoch": owner.journal_epoch,
        "issue_ref": issue_ref,
        "selection_kind": selection_kind,
        "requested_issue_revision_ref": requested_issue_revision_ref,
        "reason": reason,
        "detail": detail,
        "observed_at": observed_at,
    }
    seed = _unchecked(
        WorkflowIssueActivityUnavailableV1,
        {**base, "unavailable_ref": "", "unavailable_digest": ""},
    )
    body = _unavailable_body(seed)
    digest = _digest("aware.workflow.issue-activity.unavailable.v1", body)
    return _unchecked(
        WorkflowIssueActivityUnavailableV1,
        {
            **base,
            "unavailable_ref": _ref("workflow-issue-activity-unavailable:", digest),
            "unavailable_digest": digest,
        },
    )


def _outcome_identity(value: ActivityOutcome) -> tuple[str, str, str]:
    if type(value) is WorkflowIssueActivityMemberV1:
        body = _member_body(value)
        _check_identity(
            value,
            body,
            "aware.workflow.issue-activity.member.v1",
            "workflow-issue-activity:",
            "activity_ref",
            "activity_digest",
        )
        return ("selected", value.activity_ref, value.activity_digest)
    if type(value) is WorkflowIssueActivityUnavailableV1:
        body = _unavailable_body(value)
        _check_identity(
            value,
            body,
            "aware.workflow.issue-activity.unavailable.v1",
            "workflow-issue-activity-unavailable:",
            "unavailable_ref",
            "unavailable_digest",
        )
        return ("unavailable", value.unavailable_ref, value.unavailable_digest)
    _fail("foreign_outcome")


def _owner_wire(v: WorkflowIssueActivityOwnerObservationV1) -> dict[str, object]:
    body = _validated_owner(v)
    return {
        **body,
        "owner_observation_ref": v.owner_observation_ref,
        "owner_observation_digest": v.owner_observation_digest,
    }


def _head_wire(v: WorkflowIssueActivityHeadV1) -> dict[str, object]:
    body = _head_body(v)
    _check_identity(
        v,
        body,
        "aware.workflow.issue-activity.head.v1",
        "workflow-issue-activity-head:",
        "head_ref",
        "head_digest",
    )
    return {**body, "head_ref": v.head_ref, "head_digest": v.head_digest}


def _outcome_wire(v: ActivityOutcome) -> dict[str, object]:
    kind, ref, digest = _outcome_identity(v)
    body = (
        _member_body(v)
        if isinstance(v, WorkflowIssueActivityMemberV1)
        else _unavailable_body(v)
    )
    return {
        **body,
        ("activity_ref" if kind == "selected" else "unavailable_ref"): ref,
        ("activity_digest" if kind == "selected" else "unavailable_digest"): digest,
        "outcome_kind": kind,
    }


def _horizon_body(
    v: WorkflowIssueActivityHorizonV1, outcomes: tuple[ActivityOutcome, ...]
) -> dict[str, object]:
    _validated_owner(v.owner_observation)
    _timestamp(v.observed_at)
    if type(v.heads) is not tuple or type(v.outcome_coordinates) is not tuple:
        _fail("foreign_container")
    if any(type(item) is not WorkflowIssueActivityHeadV1 for item in v.heads):
        _fail("foreign_head")
    heads = tuple(
        sorted(
            v.heads,
            key=lambda x: (
                x.owner_observation.owner_observation_ref.encode(),
                x.issue_ref.encode(),
            ),
        )
    )
    if heads != v.heads or any(
        h.owner_observation != v.owner_observation for h in heads
    ):
        _fail("head_closure_mismatch")
    selected = tuple(o for o in outcomes if o.owner_observation == v.owner_observation)
    coords = tuple(
        sorted(((k, r) for k, r, _ in map(_outcome_identity, selected)), key=_canonical)
    )
    if coords != v.outcome_coordinates:
        _fail("outcome_closure_mismatch")
    head_digest = _digest(
        "aware.workflow.issue-activity.head-closure.v1",
        {"heads": [_head_wire(h) for h in heads]},
    )
    outcome_digest = _digest(
        "aware.workflow.issue-activity.outcome-closure.v1",
        {"outcomes": [_outcome_wire(o) for o in selected]},
    )
    if (v.head_closure_digest, v.outcome_closure_digest) != (
        head_digest,
        outcome_digest,
    ):
        _fail("closure_digest_mismatch")
    return {
        "schema_version": v.schema_version,
        "owner_observation": _owner_wire(v.owner_observation),
        "observed_at": v.observed_at,
        "heads": [_head_wire(h) for h in heads],
        "outcome_coordinates": [list(x) for x in coords],
        "head_closure_digest": head_digest,
        "outcome_closure_digest": outcome_digest,
    }


def _horizon_structural_body(v: WorkflowIssueActivityHorizonV1) -> dict[str, object]:
    _schema(v.schema_version)
    _validated_owner(v.owner_observation)
    _timestamp(v.observed_at)
    if type(v.heads) is not tuple or type(v.outcome_coordinates) is not tuple:
        _fail("foreign_container")
    if any(type(item) is not WorkflowIssueActivityHeadV1 for item in v.heads):
        _fail("foreign_head")
    heads = tuple(
        sorted(
            v.heads,
            key=lambda item: (
                item.owner_observation.owner_observation_ref.encode(),
                item.issue_ref.encode(),
            ),
        )
    )
    if heads != v.heads or any(
        item.owner_observation != v.owner_observation for item in heads
    ):
        _fail("head_closure_mismatch")
    coordinates: list[tuple[str, str]] = []
    for coordinate in v.outcome_coordinates:
        if type(coordinate) is not tuple or len(coordinate) != 2:
            _fail("foreign_coordinate")
        kind, ref = coordinate
        if kind not in {"selected", "unavailable"}:
            _fail("invalid_outcome_kind")
        coordinates.append((cast(str, _text(kind)), cast(str, _text(ref))))
    if tuple(coordinates) != tuple(sorted(coordinates, key=_canonical)) or len(
        set(coordinates)
    ) != len(coordinates):
        _fail("noncanonical_order")
    head_digest = _digest(
        "aware.workflow.issue-activity.head-closure.v1",
        {"heads": [_head_wire(item) for item in heads]},
    )
    if (
        v.head_closure_digest != head_digest
        or _DIGEST.fullmatch(v.outcome_closure_digest) is None
    ):
        _fail("closure_digest_mismatch")
    return {
        "schema_version": v.schema_version,
        "owner_observation": _owner_wire(v.owner_observation),
        "observed_at": v.observed_at,
        "heads": [_head_wire(item) for item in heads],
        "outcome_coordinates": [list(item) for item in coordinates],
        "head_closure_digest": head_digest,
        "outcome_closure_digest": v.outcome_closure_digest,
    }


def derive_workflow_issue_activity_horizon(
    *,
    owner_observation: WorkflowIssueActivityOwnerObservationV1,
    observed_at: str,
    heads: tuple[WorkflowIssueActivityHeadV1, ...],
    outcomes: tuple[ActivityOutcome, ...],
) -> WorkflowIssueActivityHorizonV1:
    selected = tuple(
        o
        for o in outcomes
        if type(o)
        in (WorkflowIssueActivityMemberV1, WorkflowIssueActivityUnavailableV1)
        and o.owner_observation == owner_observation
    )
    coords = tuple(
        sorted(((k, r) for k, r, _ in map(_outcome_identity, selected)), key=_canonical)
    )
    hd = _digest(
        "aware.workflow.issue-activity.head-closure.v1",
        {"heads": [_head_wire(h) for h in heads]},
    )
    od = _digest(
        "aware.workflow.issue-activity.outcome-closure.v1",
        {"outcomes": [_outcome_wire(o) for o in selected]},
    )
    base: dict[str, Any] = {
        "schema_version": WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
        "owner_observation": owner_observation,
        "observed_at": observed_at,
        "heads": heads,
        "outcome_coordinates": coords,
        "head_closure_digest": hd,
        "outcome_closure_digest": od,
    }
    seed = _unchecked(
        WorkflowIssueActivityHorizonV1,
        {**base, "horizon_ref": "", "horizon_digest": ""},
    )
    body = _horizon_body(seed, outcomes)
    digest = _digest("aware.workflow.issue-activity.horizon.v1", body)
    return _unchecked(
        WorkflowIssueActivityHorizonV1,
        {
            **base,
            "horizon_ref": _ref("workflow-issue-activity-horizon:", digest),
            "horizon_digest": digest,
        },
    )


def _selection_body(v: WorkflowIssueActivitySelectionV1) -> dict[str, object]:
    _schema(v.schema_version)
    _exact_enum(v.selection_kind, WorkflowIssueActivitySelectionKind)
    _exact_enum(v.outcome_kind, WorkflowIssueActivityOutcomeKind)
    if (v.selection_kind is WorkflowIssueActivitySelectionKind.CURRENT) != (
        v.requested_issue_revision_ref is None
    ):
        _fail("selection_request_mismatch")
    return {
        "schema_version": v.schema_version,
        "horizon_ref": v.horizon_ref,
        "horizon_digest": v.horizon_digest,
        "selection_kind": v.selection_kind.value,
        "issue_ref": v.issue_ref,
        "requested_issue_revision_ref": v.requested_issue_revision_ref,
        "outcome_kind": v.outcome_kind.value,
        "outcome_ref": v.outcome_ref,
        "outcome_digest": v.outcome_digest,
    }


def derive_workflow_issue_activity_selection(
    *,
    horizon: WorkflowIssueActivityHorizonV1,
    selection_kind: WorkflowIssueActivitySelectionKind,
    issue_ref: str,
    requested_issue_revision_ref: str | None,
    outcome: ActivityOutcome,
) -> WorkflowIssueActivitySelectionV1:
    kind, oref, odigest = _outcome_identity(outcome)
    if (
        kind,
        oref,
    ) not in horizon.outcome_coordinates or outcome.issue_ref != issue_ref:
        _fail("selection_outcome_mismatch")
    if selection_kind is WorkflowIssueActivitySelectionKind.HISTORICAL:
        revision = (
            outcome.issue_revision_ref
            if isinstance(outcome, WorkflowIssueActivityMemberV1)
            else outcome.requested_issue_revision_ref
        )
        if requested_issue_revision_ref != revision:
            _fail("selection_request_mismatch")
    base: dict[str, Any] = {
        "schema_version": WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
        "horizon_ref": horizon.horizon_ref,
        "horizon_digest": horizon.horizon_digest,
        "selection_kind": selection_kind,
        "issue_ref": issue_ref,
        "requested_issue_revision_ref": requested_issue_revision_ref,
        "outcome_kind": WorkflowIssueActivityOutcomeKind(kind),
        "outcome_ref": oref,
        "outcome_digest": odigest,
    }
    seed = _unchecked(
        WorkflowIssueActivitySelectionV1,
        {**base, "selection_ref": "", "selection_digest": ""},
    )
    body = _selection_body(seed)
    digest = _digest("aware.workflow.issue-activity.selection.v1", body)
    return _unchecked(
        WorkflowIssueActivitySelectionV1,
        {
            **base,
            "selection_ref": _ref("workflow-issue-activity-selection:", digest),
            "selection_digest": digest,
        },
    )


def _validated_closure_wires(
    *,
    heads: tuple[WorkflowIssueActivityHeadV1, ...],
    horizons: tuple[WorkflowIssueActivityHorizonV1, ...],
    outcomes: tuple[ActivityOutcome, ...],
    selections: tuple[WorkflowIssueActivitySelectionV1, ...],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    if any(type(x) is not tuple for x in (heads, horizons, outcomes, selections)):
        _fail("foreign_container")
    if any(type(x) is not WorkflowIssueActivityHeadV1 for x in heads):
        _fail("foreign_head")
    if any(type(x) is not WorkflowIssueActivityHorizonV1 for x in horizons):
        _fail("foreign_horizon")
    if any(
        type(x)
        not in (WorkflowIssueActivityMemberV1, WorkflowIssueActivityUnavailableV1)
        for x in outcomes
    ):
        _fail("foreign_outcome")
    if any(type(x) is not WorkflowIssueActivitySelectionV1 for x in selections):
        _fail("foreign_selection")
    if heads != tuple(
        sorted(
            heads,
            key=lambda x: (
                x.owner_observation.owner_observation_ref.encode(),
                x.issue_ref.encode(),
            ),
        )
    ):
        _fail("noncanonical_order")
    if horizons != tuple(
        sorted(
            horizons, key=lambda x: x.owner_observation.owner_observation_ref.encode()
        )
    ):
        _fail("noncanonical_order")
    outcome_evidence = tuple(
        (item, _outcome_identity(item), _outcome_wire(item)) for item in outcomes
    )
    if outcomes != tuple(
        item
        for item, identity, _ in sorted(
            outcome_evidence,
            key=lambda entry: (
                entry[0].owner_observation.owner_observation_ref.encode(),
                entry[0].issue_ref.encode(),
                entry[1][0].encode(),
                entry[1][1].encode(),
            ),
        )
    ):
        _fail("noncanonical_order")
    if selections != tuple(
        sorted(
            selections,
            key=lambda x: _canonical(
                [
                    x.horizon_ref,
                    x.issue_ref,
                    x.selection_kind.value,
                    x.requested_issue_revision_ref,
                ]
            ),
        )
    ):
        _fail("noncanonical_order")
    if len(
        {(h.owner_observation.owner_observation_ref, h.issue_ref) for h in heads}
    ) != len(heads):
        _fail("duplicate_head")
    if len({h.owner_observation.owner_observation_ref for h in horizons}) != len(
        horizons
    ):
        _fail("duplicate_horizon")
    outcome_map = {
        identity[1]: (item, identity) for item, identity, _ in outcome_evidence
    }
    if len(outcome_map) != len(outcomes):
        _fail("duplicate_outcome")
    horizon_map = {h.horizon_ref: h for h in horizons}
    outcome_groups: dict[
        str, list[tuple[ActivityOutcome, tuple[str, str, str], dict[str, object]]]
    ] = {}
    for evidence in outcome_evidence:
        outcome_groups.setdefault(
            evidence[0].owner_observation.owner_observation_ref, []
        ).append(evidence)
    horizon_wires: list[dict[str, object]] = []
    for h in horizons:
        body = _horizon_structural_body(h)
        group = outcome_groups.get(h.owner_observation.owner_observation_ref, [])
        expected_coordinates = tuple(
            sorted(
                ((identity[0], identity[1]) for _, identity, _ in group), key=_canonical
            )
        )
        expected_outcome_digest = _digest(
            "aware.workflow.issue-activity.outcome-closure.v1",
            {"outcomes": [wire for _, _, wire in group]},
        )
        if (
            h.outcome_coordinates != expected_coordinates
            or h.outcome_closure_digest != expected_outcome_digest
        ):
            _fail("outcome_closure_mismatch")
        _check_identity(
            h,
            body,
            "aware.workflow.issue-activity.horizon.v1",
            "workflow-issue-activity-horizon:",
            "horizon_ref",
            "horizon_digest",
        )
        horizon_wires.append(
            {**body, "horizon_ref": h.horizon_ref, "horizon_digest": h.horizon_digest}
        )
    seen = set()
    selection_wires: list[dict[str, object]] = []
    for s in selections:
        if (
            type(s) is not WorkflowIssueActivitySelectionV1
            or s.horizon_ref not in horizon_map
            or s.outcome_ref not in outcome_map
        ):
            _fail("selection_closure_mismatch")
        h = horizon_map[s.horizon_ref]
        o, identity = outcome_map[s.outcome_ref]
        selection_wires.append(_selection_wire(s))
        if (
            s.horizon_digest,
            s.outcome_kind.value,
            s.outcome_ref,
            s.outcome_digest,
            s.issue_ref,
        ) != (h.horizon_digest, identity[0], identity[1], identity[2], o.issue_ref):
            _fail("selection_mismatch")
        if s.selection_kind is WorkflowIssueActivitySelectionKind.HISTORICAL:
            revision = (
                o.issue_revision_ref
                if isinstance(o, WorkflowIssueActivityMemberV1)
                else o.requested_issue_revision_ref
            )
            if s.requested_issue_revision_ref != revision:
                _fail("selection_request_mismatch")
        key = (s.horizon_ref, s.outcome_ref)
        if key in seen:
            _fail("duplicate_selection")
        seen.add(key)
        if (
            s.selection_kind is WorkflowIssueActivitySelectionKind.CURRENT
            and type(o) is WorkflowIssueActivityMemberV1
        ):
            matching = [head for head in h.heads if head.issue_ref == s.issue_ref]
            if (
                len(matching) != 1
                or (o.issue_revision_ref, o.issue_snapshot_digest)
                != (matching[0].issue_revision_ref, matching[0].issue_snapshot_digest)
                or o.authority_generation != h.owner_observation.authority_generation
                or o.issue_snapshot.authority.kind
                is not h.owner_observation.authority_kind
                or o.issue_snapshot.authority.receipt_ref
                != h.owner_observation.authority_receipt_ref
            ):
                _fail("current_member_mismatch")
    expected = {
        (h.horizon_ref, ref) for h in horizons for _, ref in h.outcome_coordinates
    }
    if seen != expected:
        _fail("selection_completeness_mismatch")
    nested_heads = {
        (h.owner_observation.owner_observation_ref, item.head_ref)
        for h in horizons
        for item in h.heads
    }
    aggregate_heads = {
        (item.owner_observation.owner_observation_ref, item.head_ref) for item in heads
    }
    if nested_heads != aggregate_heads:
        _fail("head_completeness_mismatch")
    return (
        [_head_wire(item) for item in heads],
        horizon_wires,
        [wire for _, _, wire in outcome_evidence],
        selection_wires,
    )


def validate_workflow_issue_activity_observation_closure(
    *,
    heads: tuple[WorkflowIssueActivityHeadV1, ...],
    horizons: tuple[WorkflowIssueActivityHorizonV1, ...],
    outcomes: tuple[ActivityOutcome, ...],
    selections: tuple[WorkflowIssueActivitySelectionV1, ...],
) -> None:
    _validated_closure_wires(
        heads=heads, horizons=horizons, outcomes=outcomes, selections=selections
    )


def _horizon_wire(
    value: WorkflowIssueActivityHorizonV1, outcomes: tuple[ActivityOutcome, ...]
) -> dict[str, object]:
    body = _horizon_body(value, outcomes)
    _check_identity(
        value,
        body,
        "aware.workflow.issue-activity.horizon.v1",
        "workflow-issue-activity-horizon:",
        "horizon_ref",
        "horizon_digest",
    )
    return {
        **body,
        "horizon_ref": value.horizon_ref,
        "horizon_digest": value.horizon_digest,
    }


def _selection_wire(value: WorkflowIssueActivitySelectionV1) -> dict[str, object]:
    if type(value) is not WorkflowIssueActivitySelectionV1:
        _fail("foreign_selection")
    body = _selection_body(value)
    _check_identity(
        value,
        body,
        "aware.workflow.issue-activity.selection.v1",
        "workflow-issue-activity-selection:",
        "selection_ref",
        "selection_digest",
    )
    return {
        **body,
        "selection_ref": value.selection_ref,
        "selection_digest": value.selection_digest,
    }
