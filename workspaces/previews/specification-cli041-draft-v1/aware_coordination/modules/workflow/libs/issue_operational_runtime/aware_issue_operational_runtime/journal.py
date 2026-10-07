from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from .contracts import IssueOperationalState, JsonObject
from .identity import nonnegative, required_token, stable_local_ref


class IssueEventKind(StrEnum):
    AUTHORITY_ADMITTED = "issue_authority_admitted"
    ISSUE_ENSURED = "issue_ensured"
    LIFECYCLE_CHANGED = "issue_lifecycle_changed"
    SCOPE_BOUND = "issue_scope_bound"
    UPDATE_APPENDED = "issue_update_appended"
    EVIDENCE_APPENDED = "issue_evidence_appended"
    RECONCILIATION_CHANGED = "issue_reconciliation_changed"


class ReplayOutcome(StrEnum):
    EVENTS = "events"
    GAP = "gap"
    RESET = "reset"
    AHEAD = "ahead"


@dataclass(frozen=True, slots=True)
class IssueEvent:
    event_ref: str
    authority_ref: str
    epoch: str
    cursor: int
    kind: IssueEventKind
    authority_generation: int
    issue_ref: str | None
    issue_revision: int | None
    receipt_ref: str
    affected_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("event_ref", "authority_ref", "epoch", "receipt_ref"):
            required_token(getattr(self, name), name)
        if nonnegative(self.cursor, "cursor") < 1:
            raise ValueError("cursor must be positive")
        nonnegative(self.authority_generation, "authority_generation")
        if not isinstance(self.kind, IssueEventKind):
            raise TypeError("kind must be IssueEventKind")
        if self.issue_ref is not None:
            required_token(self.issue_ref, "issue_ref")
        if self.issue_revision is not None:
            nonnegative(self.issue_revision, "issue_revision")
        if (self.issue_ref is None) != (self.issue_revision is None):
            raise ValueError("issue_ref and issue_revision must be present together")
        if len(self.affected_refs) != len(set(self.affected_refs)):
            raise ValueError("affected_refs must be unique")

    def to_wire(self) -> JsonObject:
        return {
            "event_ref": self.event_ref,
            "authority_ref": self.authority_ref,
            "epoch": self.epoch,
            "cursor": self.cursor,
            "kind": self.kind.value,
            "authority_generation": self.authority_generation,
            "issue_ref": self.issue_ref,
            "issue_revision": self.issue_revision,
            "receipt_ref": self.receipt_ref,
            "affected_refs": list(self.affected_refs),
        }


@dataclass(frozen=True, slots=True)
class IssueJournal:
    epoch: str
    retention_limit: int
    next_cursor: int = 1
    events: tuple[IssueEvent, ...] = ()

    def __post_init__(self) -> None:
        required_token(self.epoch, "epoch")
        if isinstance(self.retention_limit, bool) or self.retention_limit < 1:
            raise ValueError("retention_limit must be positive")
        if nonnegative(self.next_cursor, "next_cursor") < 1:
            raise ValueError("next_cursor must be positive")
        if len(self.events) > self.retention_limit:
            raise ValueError("journal exceeds retention_limit")
        cursors = tuple(item.cursor for item in self.events)
        if cursors and cursors != tuple(range(cursors[0], self.next_cursor)):
            raise ValueError("journal events must be a contiguous retained suffix")
        if any(item.epoch != self.epoch for item in self.events):
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
            "events": [item.to_wire() for item in self.events],
        }


@dataclass(frozen=True, slots=True)
class IssueOperationalRecord:
    authority_ref: str
    state: IssueOperationalState
    journal: IssueJournal

    def __post_init__(self) -> None:
        required_token(self.authority_ref, "authority_ref")
        if self.state.authority.authority_ref != self.authority_ref:
            raise ValueError("record key must equal issue authority ref")
        if any(
            item.authority_ref != self.authority_ref for item in self.journal.events
        ):
            raise ValueError("journal contains an event for another authority")


@dataclass(frozen=True, slots=True)
class ReplayResult:
    outcome: ReplayOutcome
    epoch: str
    earliest_cursor: int
    latest_cursor: int | None
    events: tuple[IssueEvent, ...] = ()
    reset_state: IssueOperationalState | None = None


def append_event(
    journal: IssueJournal,
    *,
    authority_ref: str,
    kind: IssueEventKind,
    authority_generation: int,
    issue_ref: str | None,
    issue_revision: int | None,
    receipt_ref: str,
    affected_refs: tuple[str, ...],
) -> tuple[IssueJournal, IssueEvent]:
    cursor = journal.next_cursor
    event = IssueEvent(
        event_ref=stable_local_ref(
            authority_ref=authority_ref,
            kind="event",
            semantic_key=f"{journal.epoch}:{cursor}:{receipt_ref}",
        ),
        authority_ref=authority_ref,
        epoch=journal.epoch,
        cursor=cursor,
        kind=kind,
        authority_generation=authority_generation,
        issue_ref=issue_ref,
        issue_revision=issue_revision,
        receipt_ref=receipt_ref,
        affected_refs=affected_refs,
    )
    retained = (*journal.events, event)[-journal.retention_limit :]
    return replace(journal, next_cursor=cursor + 1, events=retained), event


def replay_journal(
    record: IssueOperationalRecord,
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
            reset_state=record.state,
        )
    latest = journal.latest_cursor
    if latest is None:
        outcome = ReplayOutcome.AHEAD if after_cursor > 0 else ReplayOutcome.EVENTS
        return ReplayResult(
            outcome,
            epoch=journal.epoch,
            earliest_cursor=journal.earliest_cursor,
            latest_cursor=latest,
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
            reset_state=record.state,
        )
    return ReplayResult(
        ReplayOutcome.EVENTS,
        epoch=journal.epoch,
        earliest_cursor=journal.earliest_cursor,
        latest_cursor=latest,
        events=tuple(item for item in journal.events if item.cursor > after_cursor),
    )
