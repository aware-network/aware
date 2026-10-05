from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from threading import RLock
from typing import Protocol, cast

from .codec import decode_goal_operational_state, encode_goal_operational_state
from .contracts import GoalOperationalState, JsonObject
from .identity import nonnegative, optional_token, required_token, stable_ref
from .reconciliation import (
    GoalReconciliationState,
    ReconciliationIntentRecord,
    ReconciliationStatus,
)

RECORD_CODEC_NAME = "aware.workflow.goal-operational-record"
RECORD_CODEC_VERSION = 1


class GoalEventKind(StrEnum):
    GOAL_CHANGED = "goal_changed"
    LANE_CHANGED = "goal_lane_changed"
    ROW_CHANGED = "goal_lane_issue_changed"
    UPDATE_APPENDED = "goal_update_appended"
    RECONCILIATION_CHANGED = "goal_reconciliation_changed"


class ReplayOutcome(StrEnum):
    EVENTS = "events"
    GAP = "gap"
    RESET = "reset"
    AHEAD = "ahead"


@dataclass(frozen=True, slots=True)
class GoalJournalEvent:
    event_ref: str
    authority_ref: str
    epoch: str
    cursor: int
    kind: GoalEventKind
    client_intent_id: str
    authority_generation: int
    store_generation: int
    receipt_ref: str
    state_digest: str
    goal_ref: str | None = None
    lane_ref: str | None = None
    row_ref: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "event_ref",
            "authority_ref",
            "epoch",
            "client_intent_id",
            "receipt_ref",
            "state_digest",
        ):
            required_token(getattr(self, field_name), field_name)
        if nonnegative(self.cursor, "cursor") < 1:
            raise ValueError("cursor must be positive")
        nonnegative(self.authority_generation, "authority_generation")
        if nonnegative(self.store_generation, "store_generation") < 1:
            raise ValueError("store_generation must be positive")
        if not isinstance(self.kind, GoalEventKind):
            raise TypeError("kind must be GoalEventKind")
        for field_name in ("goal_ref", "lane_ref", "row_ref"):
            object.__setattr__(
                self,
                field_name,
                optional_token(getattr(self, field_name), field_name),
            )
        if self.row_ref is not None and self.lane_ref is None:
            raise ValueError("row_ref requires lane_ref")

    def to_wire(self) -> JsonObject:
        return {
            "event_ref": self.event_ref,
            "authority_ref": self.authority_ref,
            "epoch": self.epoch,
            "cursor": self.cursor,
            "kind": self.kind.value,
            "client_intent_id": self.client_intent_id,
            "authority_generation": self.authority_generation,
            "store_generation": self.store_generation,
            "receipt_ref": self.receipt_ref,
            "state_digest": self.state_digest,
            "goal_ref": self.goal_ref,
            "lane_ref": self.lane_ref,
            "row_ref": self.row_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalJournal:
    epoch: str
    retention_limit: int
    next_cursor: int = 1
    events: tuple[GoalJournalEvent, ...] = ()

    def __post_init__(self) -> None:
        required_token(self.epoch, "epoch")
        if isinstance(self.retention_limit, bool) or self.retention_limit < 1:
            raise ValueError("retention_limit must be positive")
        if nonnegative(self.next_cursor, "next_cursor") < 1:
            raise ValueError("next_cursor must be positive")
        if len(self.events) > self.retention_limit:
            raise ValueError("journal exceeds retention_limit")
        cursors = tuple(event.cursor for event in self.events)
        if cursors and cursors != tuple(range(cursors[0], self.next_cursor)):
            raise ValueError("journal events must be a contiguous retained suffix")
        if any(event.epoch != self.epoch for event in self.events):
            raise ValueError("journal event epoch mismatch")

    @property
    def earliest_cursor(self) -> int:
        return self.events[0].cursor if self.events else self.next_cursor

    @property
    def latest_cursor(self) -> int | None:
        return self.events[-1].cursor if self.events else None

    def to_wire(self) -> JsonObject:
        return {
            "epoch": self.epoch,
            "retention_limit": self.retention_limit,
            "next_cursor": self.next_cursor,
            "events": [event.to_wire() for event in self.events],
        }


@dataclass(frozen=True, slots=True)
class GoalOperationalRecord:
    authority_ref: str
    state: GoalOperationalState
    journal: GoalJournal
    reconciliation: GoalReconciliationState = field(
        default_factory=GoalReconciliationState
    )

    def __post_init__(self) -> None:
        required_token(self.authority_ref, "authority_ref")
        if self.state.authority.authority_ref != self.authority_ref:
            raise ValueError("record key must equal Goal authority ref")
        if any(
            event.authority_ref != self.authority_ref for event in self.journal.events
        ):
            raise ValueError("journal contains an event for another authority")


@dataclass(frozen=True, slots=True)
class ReplayResult:
    outcome: ReplayOutcome
    epoch: str
    earliest_cursor: int
    latest_cursor: int | None
    events: tuple[GoalJournalEvent, ...] = ()
    reset_record: GoalOperationalRecord | None = None


@dataclass(frozen=True, slots=True)
class PersistedGoalRecord:
    authority_ref: str
    generation: int
    payload: str

    def __post_init__(self) -> None:
        required_token(self.authority_ref, "authority_ref")
        nonnegative(self.generation, "generation")
        if not isinstance(self.payload, str) or not self.payload:
            raise ValueError("payload must be non-empty JSON text")


@dataclass(frozen=True, slots=True)
class PersistenceWriteResult:
    applied: bool
    current: PersistedGoalRecord


class GoalStateStore(Protocol):
    def read(self, authority_ref: str) -> PersistedGoalRecord | None: ...

    def create(self, authority_ref: str, payload: str) -> PersistenceWriteResult: ...

    def compare_and_set(
        self,
        authority_ref: str,
        *,
        expected_generation: int,
        payload: str,
    ) -> PersistenceWriteResult: ...


class InMemoryGoalStateStore:
    """Atomic generation-CAS reference provider for neutral conformance."""

    def __init__(self) -> None:
        self._records: dict[str, PersistedGoalRecord] = {}
        self._lock = RLock()

    def read(self, authority_ref: str) -> PersistedGoalRecord | None:
        required_token(authority_ref, "authority_ref")
        with self._lock:
            return self._records.get(authority_ref)

    def create(self, authority_ref: str, payload: str) -> PersistenceWriteResult:
        proposed = PersistedGoalRecord(authority_ref, 0, payload)
        with self._lock:
            current = self._records.get(authority_ref)
            if current is not None:
                return PersistenceWriteResult(False, current)
            self._records[authority_ref] = proposed
            return PersistenceWriteResult(True, proposed)

    def compare_and_set(
        self,
        authority_ref: str,
        *,
        expected_generation: int,
        payload: str,
    ) -> PersistenceWriteResult:
        required_token(authority_ref, "authority_ref")
        nonnegative(expected_generation, "expected_generation")
        with self._lock:
            current = self._records.get(authority_ref)
            if current is None:
                raise KeyError(authority_ref)
            if current.generation != expected_generation:
                return PersistenceWriteResult(False, current)
            proposed = PersistedGoalRecord(
                authority_ref,
                expected_generation + 1,
                payload,
            )
            self._records[authority_ref] = proposed
            return PersistenceWriteResult(True, proposed)


def append_journal_event(
    record: GoalOperationalRecord,
    *,
    kind: GoalEventKind,
    client_intent_id: str,
    store_generation: int,
    receipt_ref: str,
    state_digest: str,
    goal_ref: str | None = None,
    lane_ref: str | None = None,
    row_ref: str | None = None,
) -> GoalOperationalRecord:
    cursor = record.journal.next_cursor
    event = GoalJournalEvent(
        event_ref=stable_ref(
            kind="goal-event",
            authority_ref=record.authority_ref,
            coordinates=(record.journal.epoch, str(cursor), receipt_ref),
        ),
        authority_ref=record.authority_ref,
        epoch=record.journal.epoch,
        cursor=cursor,
        kind=kind,
        client_intent_id=client_intent_id,
        authority_generation=record.state.authority.generation,
        store_generation=store_generation,
        receipt_ref=receipt_ref,
        state_digest=state_digest,
        goal_ref=goal_ref,
        lane_ref=lane_ref,
        row_ref=row_ref,
    )
    events = (*record.journal.events, event)[-record.journal.retention_limit :]
    return replace(
        record,
        journal=replace(
            record.journal,
            next_cursor=cursor + 1,
            events=events,
        ),
    )


def replay_journal(
    record: GoalOperationalRecord,
    *,
    epoch: str,
    after_cursor: int,
) -> ReplayResult:
    required_token(epoch, "epoch")
    nonnegative(after_cursor, "after_cursor")
    journal = record.journal
    if epoch != journal.epoch:
        return ReplayResult(
            ReplayOutcome.RESET,
            epoch=journal.epoch,
            earliest_cursor=journal.earliest_cursor,
            latest_cursor=journal.latest_cursor,
            reset_record=record,
        )
    latest = journal.latest_cursor
    if latest is None:
        outcome = ReplayOutcome.AHEAD if after_cursor > 0 else ReplayOutcome.EVENTS
        return ReplayResult(
            outcome,
            epoch=journal.epoch,
            earliest_cursor=journal.earliest_cursor,
            latest_cursor=None,
        )
    if after_cursor > latest:
        return ReplayResult(
            ReplayOutcome.AHEAD,
            epoch=journal.epoch,
            earliest_cursor=journal.earliest_cursor,
            latest_cursor=latest,
        )
    if after_cursor < journal.earliest_cursor - 1:
        return ReplayResult(
            ReplayOutcome.GAP,
            epoch=journal.epoch,
            earliest_cursor=journal.earliest_cursor,
            latest_cursor=latest,
            reset_record=record,
        )
    return ReplayResult(
        ReplayOutcome.EVENTS,
        epoch=journal.epoch,
        earliest_cursor=journal.earliest_cursor,
        latest_cursor=latest,
        events=tuple(event for event in journal.events if event.cursor > after_cursor),
    )


def encode_goal_operational_record(record: GoalOperationalRecord) -> str:
    payload = {
        "codec": RECORD_CODEC_NAME,
        "version": RECORD_CODEC_VERSION,
        "authority_ref": record.authority_ref,
        "state_json": encode_goal_operational_state(record.state),
        "journal": record.journal.to_wire(),
        "reconciliation": record.reconciliation.to_wire(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def decode_goal_operational_record(payload: str) -> GoalOperationalRecord:
    if not isinstance(payload, str) or not payload:
        raise ValueError("payload must be non-empty JSON text")
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid Goal operational record JSON") from exc
    root = _object(raw, "record")
    _keys(
        root,
        {
            "codec",
            "version",
            "authority_ref",
            "state_json",
            "journal",
            "reconciliation",
        },
        "record",
    )
    if root["codec"] != RECORD_CODEC_NAME or root["version"] != RECORD_CODEC_VERSION:
        raise ValueError("unsupported Goal operational record codec")
    return GoalOperationalRecord(
        authority_ref=_string(root["authority_ref"], "authority_ref"),
        state=decode_goal_operational_state(_string(root["state_json"], "state_json")),
        journal=_journal(_object(root["journal"], "journal")),
        reconciliation=_reconciliation(
            _object(root["reconciliation"], "reconciliation")
        ),
    )


def _journal(raw: Mapping[str, object]) -> GoalJournal:
    _keys(raw, {"epoch", "retention_limit", "next_cursor", "events"}, "journal")
    return GoalJournal(
        epoch=_string(raw["epoch"], "epoch"),
        retention_limit=_integer(raw["retention_limit"], "retention_limit"),
        next_cursor=_integer(raw["next_cursor"], "next_cursor"),
        events=tuple(
            _event(_object(item, "event")) for item in _list(raw["events"], "events")
        ),
    )


def _event(raw: Mapping[str, object]) -> GoalJournalEvent:
    expected = {
        "event_ref",
        "authority_ref",
        "epoch",
        "cursor",
        "kind",
        "client_intent_id",
        "authority_generation",
        "store_generation",
        "receipt_ref",
        "state_digest",
        "goal_ref",
        "lane_ref",
        "row_ref",
    }
    _keys(raw, expected, "event")
    return GoalJournalEvent(
        event_ref=_string(raw["event_ref"], "event_ref"),
        authority_ref=_string(raw["authority_ref"], "authority_ref"),
        epoch=_string(raw["epoch"], "epoch"),
        cursor=_integer(raw["cursor"], "cursor"),
        kind=GoalEventKind(_string(raw["kind"], "kind")),
        client_intent_id=_string(raw["client_intent_id"], "client_intent_id"),
        authority_generation=_integer(
            raw["authority_generation"], "authority_generation"
        ),
        store_generation=_integer(raw["store_generation"], "store_generation"),
        receipt_ref=_string(raw["receipt_ref"], "receipt_ref"),
        state_digest=_string(raw["state_digest"], "state_digest"),
        goal_ref=_nullable_string(raw["goal_ref"], "goal_ref"),
        lane_ref=_nullable_string(raw["lane_ref"], "lane_ref"),
        row_ref=_nullable_string(raw["row_ref"], "row_ref"),
    )


def _reconciliation(raw: Mapping[str, object]) -> GoalReconciliationState:
    _keys(
        raw,
        {
            "status",
            "revision",
            "canonical_authority_ref",
            "evidence_ref",
            "reason",
            "intent_records",
        },
        "reconciliation",
    )
    return GoalReconciliationState(
        status=ReconciliationStatus(_string(raw["status"], "status")),
        revision=_integer(raw["revision"], "revision"),
        canonical_authority_ref=_nullable_string(
            raw["canonical_authority_ref"], "canonical_authority_ref"
        ),
        evidence_ref=_nullable_string(raw["evidence_ref"], "evidence_ref"),
        reason=_nullable_string(raw["reason"], "reason"),
        intent_records=tuple(
            _reconciliation_intent_record(_object(item, "reconciliation_intent"))
            for item in _list(raw["intent_records"], "intent_records")
        ),
    )


def _reconciliation_intent_record(
    raw: Mapping[str, object],
) -> ReconciliationIntentRecord:
    _keys(raw, {"client_intent_id", "fingerprint"}, "reconciliation_intent")
    return ReconciliationIntentRecord(
        client_intent_id=_string(raw["client_intent_id"], "client_intent_id"),
        fingerprint=_string(raw["fingerprint"], "fingerprint"),
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
