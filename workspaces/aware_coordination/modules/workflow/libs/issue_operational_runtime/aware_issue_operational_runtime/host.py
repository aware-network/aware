from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from threading import BoundedSemaphore, Event, Lock, RLock
from typing import cast

from .codec import decode_operational_record, encode_operational_record
from .contracts import (
    AcceptAuthorityMappingIntent,
    AmendIssueScopePathsIntent,
    AppendIssueEvidenceIntent,
    AppendIssueUpdateIntent,
    BindIssueScopePathsIntent,
    EnsureIssueIntent,
    IssueIntent,
    IssueOperationalState,
    IssueSnapshot,
    PrepareAuthorityReconciliationIntent,
    RejectAuthorityMappingIntent,
    TransitionOutcome,
    TransitionResult,
)
from .identity import nonnegative, required_token, stable_local_ref
from .journal import (
    IssueEventKind,
    IssueJournal,
    IssueOperationalRecord,
    ReplayResult,
    append_event,
    replay_journal,
)
from .persistence import (
    IssueIndexedStateStore,
    IssueStateStore,
)
from .state_machine import apply_issue_intent


class HostOutcome(StrEnum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"
    PERSISTENCE_CONFLICT = "persistence_conflict"


class CancellationToken:
    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True, slots=True)
class OperationReceipt:
    receipt_ref: str
    authority_ref: str
    client_intent_id: str
    authority_generation: int
    store_generation: int
    affected_refs: tuple[str, ...]
    issue_ref: str | None = None
    issue_revision: int | None = None
    observation_cursor: int | None = None

    def __post_init__(self) -> None:
        for name in ("receipt_ref", "authority_ref", "client_intent_id"):
            required_token(getattr(self, name), name)
        nonnegative(self.authority_generation, "authority_generation")
        nonnegative(self.store_generation, "store_generation")
        if self.issue_ref is not None:
            required_token(self.issue_ref, "issue_ref")
        if self.issue_revision is not None:
            nonnegative(self.issue_revision, "issue_revision")
        if (self.issue_ref is None) != (self.issue_revision is None):
            raise ValueError("issue_ref and issue_revision must be present together")
        if self.observation_cursor is not None:
            nonnegative(self.observation_cursor, "observation_cursor")


@dataclass(frozen=True, slots=True)
class HostResult:
    outcome: HostOutcome
    transition: TransitionResult | None = None
    receipt: OperationReceipt | None = None
    blocker_code: str | None = None


class IssueOperationalRuntimeHost:
    """Bounded persistence-first owner for the neutral Workflow Issue reducer."""

    def __init__(
        self,
        store: IssueStateStore,
        *,
        max_in_flight: int = 64,
        journal_retention: int = 256,
    ) -> None:
        if isinstance(max_in_flight, bool) or max_in_flight < 1:
            raise ValueError("max_in_flight must be positive")
        if isinstance(journal_retention, bool) or journal_retention < 1:
            raise ValueError("journal_retention must be positive")
        self._store = store
        self._admission = BoundedSemaphore(max_in_flight)
        self._journal_retention = journal_retention
        self._authority_locks: dict[str, Lock] = {}
        self._catalog_lock = RLock()
        self._closed = False

    def close(self) -> None:
        with self._catalog_lock:
            self._closed = True

    @property
    def is_closed(self) -> bool:
        with self._catalog_lock:
            return self._closed

    def admit_authority(
        self,
        authority_ref: str,
        state: IssueOperationalState,
        *,
        epoch: str,
    ) -> bool:
        required_token(authority_ref, "authority_ref")
        if self.is_closed:
            return False
        record = IssueOperationalRecord(
            authority_ref=authority_ref,
            state=state,
            journal=IssueJournal(
                epoch=epoch,
                retention_limit=self._journal_retention,
            ),
        )
        return self._store.create(
            authority_ref,
            encode_operational_record(record),
        ).applied

    def read(self, authority_ref: str) -> IssueOperationalRecord | None:
        persisted = self._store.read(authority_ref)
        return (
            None if persisted is None else decode_operational_record(persisted.payload)
        )

    def read_head(self, authority_ref: str) -> IssueOperationalRecord | None:
        """Read bounded authority/journal coordinates when the store indexes them."""

        if isinstance(self._store, IssueIndexedStateStore):
            return self._store.read_head_record(authority_ref)
        return self.read(authority_ref)

    def resolve_issue(
        self,
        authority_ref: str,
        *,
        issue_ref: str | None = None,
        issue_tag: str | None = None,
    ) -> IssueSnapshot | None:
        """Resolve one Issue without materializing the authority catalog."""

        if (issue_ref is None) == (issue_tag is None):
            raise ValueError("exactly one Issue ref or tag is required")
        if issue_ref is not None:
            if isinstance(self._store, IssueIndexedStateStore):
                return self._store.read_issue_by_ref(authority_ref, issue_ref)
        else:
            if isinstance(self._store, IssueIndexedStateStore):
                assert issue_tag is not None
                return self._store.read_issue_by_tag(authority_ref, issue_tag)
        record = self.read(authority_ref)
        if record is None:
            return None
        return (
            record.state.issue_by_ref(issue_ref)
            if issue_ref is not None
            else record.state.issue_by_tag(cast(str, issue_tag))
        )

    def replay(
        self,
        authority_ref: str,
        *,
        epoch: str,
        after_cursor: int,
    ) -> ReplayResult | None:
        record = self.read(authority_ref)
        return (
            None
            if record is None
            else replay_journal(record, epoch=epoch, after_cursor=after_cursor)
        )

    def submit(
        self,
        authority_ref: str,
        intent: IssueIntent,
        *,
        cancellation: CancellationToken | None = None,
    ) -> HostResult:
        required_token(authority_ref, "authority_ref")
        if self.is_closed:
            return HostResult(HostOutcome.REJECTED, blocker_code="host_closed")
        if cancellation is not None and cancellation.is_cancelled:
            return HostResult(HostOutcome.CANCELLED, blocker_code="cancelled")
        if not self._admission.acquire(blocking=False):
            return HostResult(HostOutcome.REJECTED, blocker_code="host_capacity")
        try:
            with self._lock_for(authority_ref):
                return self._submit_locked(authority_ref, intent, cancellation)
        finally:
            self._admission.release()

    def _submit_locked(
        self,
        authority_ref: str,
        intent: IssueIntent,
        cancellation: CancellationToken | None,
    ) -> HostResult:
        if self.is_closed:
            return HostResult(HostOutcome.REJECTED, blocker_code="host_closed")
        if cancellation is not None and cancellation.is_cancelled:
            return HostResult(HostOutcome.CANCELLED, blocker_code="cancelled")
        delta_store = self._delta_store(intent)
        persisted = (
            self._store.read(authority_ref)
            if delta_store is None
            else delta_store.read_mutation_record(authority_ref, intent)
        )
        if persisted is None:
            return HostResult(
                HostOutcome.UNRESOLVED, blocker_code="authority_unresolved"
            )
        record = decode_operational_record(persisted.payload)
        result = apply_issue_intent(record.state, intent)
        if not result.changed:
            receipt = None
            if result.outcome is TransitionOutcome.IDEMPOTENT:
                receipt = self._receipt(
                    authority_ref=authority_ref,
                    intent=intent,
                    result=result,
                    store_generation=persisted.generation,
                    observation_cursor=None,
                )
            return HostResult(HostOutcome.COMPLETED, transition=result, receipt=receipt)
        if cancellation is not None and cancellation.is_cancelled:
            return HostResult(HostOutcome.CANCELLED, blocker_code="cancelled")
        receipt = self._receipt(
            authority_ref=authority_ref,
            intent=intent,
            result=result,
            store_generation=persisted.generation + 1,
            observation_cursor=record.journal.next_cursor,
        )
        journal, _ = append_event(
            record.journal,
            authority_ref=authority_ref,
            kind=_event_kind(intent),
            authority_generation=result.state.authority.generation,
            issue_ref=result.issue_ref,
            issue_revision=result.issue_revision,
            receipt_ref=receipt.receipt_ref,
            affected_refs=result.affected_refs,
        )
        proposed = IssueOperationalRecord(
            authority_ref=authority_ref,
            state=result.state,
            journal=journal,
        )
        if cancellation is not None and cancellation.is_cancelled:
            return HostResult(HostOutcome.CANCELLED, blocker_code="cancelled")
        encoded = encode_operational_record(proposed)
        write = (
            self._store.compare_and_set(
                authority_ref,
                expected_generation=persisted.generation,
                payload=encoded,
            )
            if delta_store is None
            else delta_store.compare_and_set_delta(
                authority_ref,
                expected_generation=persisted.generation,
                payload=encoded,
            )
        )
        if not write.applied:
            current = decode_operational_record(write.current.payload)
            conflict = TransitionResult(
                TransitionOutcome.CONFLICT,
                current.state,
                blocker_code="persistence_generation_conflict",
            )
            return HostResult(
                HostOutcome.PERSISTENCE_CONFLICT,
                transition=conflict,
                blocker_code="persistence_generation_conflict",
            )
        return HostResult(HostOutcome.COMPLETED, transition=result, receipt=receipt)

    def _delta_store(self, intent: IssueIntent) -> IssueIndexedStateStore | None:
        if isinstance(
            intent,
            (
                PrepareAuthorityReconciliationIntent,
                AcceptAuthorityMappingIntent,
                RejectAuthorityMappingIntent,
            ),
        ):
            return None
        if not isinstance(self._store, IssueIndexedStateStore):
            return None
        return self._store

    def _lock_for(self, authority_ref: str) -> Lock:
        with self._catalog_lock:
            return self._authority_locks.setdefault(authority_ref, Lock())

    @staticmethod
    def _receipt(
        *,
        authority_ref: str,
        intent: IssueIntent,
        result: TransitionResult,
        store_generation: int,
        observation_cursor: int | None,
    ) -> OperationReceipt:
        semantic_key = (
            f"{intent.context.client_intent_id}:"
            f"{result.state.authority.generation}:{result.issue_revision}:"
            f"{store_generation}"
        )
        return OperationReceipt(
            receipt_ref=stable_local_ref(
                authority_ref=authority_ref,
                kind="operation-receipt",
                semantic_key=semantic_key,
            ),
            authority_ref=authority_ref,
            client_intent_id=intent.context.client_intent_id,
            authority_generation=result.state.authority.generation,
            store_generation=store_generation,
            affected_refs=result.affected_refs,
            issue_ref=result.issue_ref,
            issue_revision=result.issue_revision,
            observation_cursor=observation_cursor,
        )


def _event_kind(intent: IssueIntent) -> IssueEventKind:
    if isinstance(intent, EnsureIssueIntent):
        return IssueEventKind.ISSUE_ENSURED
    if isinstance(intent, (BindIssueScopePathsIntent, AmendIssueScopePathsIntent)):
        return IssueEventKind.SCOPE_BOUND
    if isinstance(intent, AppendIssueUpdateIntent):
        return IssueEventKind.UPDATE_APPENDED
    if isinstance(intent, AppendIssueEvidenceIntent):
        return IssueEventKind.EVIDENCE_APPENDED
    if intent.to_wire()["kind"] in {
        "prepare_authority_reconciliation",
        "accept_authority_mapping",
        "reject_authority_mapping",
    }:
        return IssueEventKind.RECONCILIATION_CHANGED
    return IssueEventKind.LIFECYCLE_CHANGED
