from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from threading import BoundedSemaphore, Event, Lock, RLock

from .contracts import (
    AppendGoalLaneIssueIntent,
    AppendGoalUpdateIntent,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalIntent,
    GoalOperationalState,
    LinkGoalLaneIssueIntent,
    SyncGoalLaneIssueIntent,
    TransitionOutcome,
    TransitionResult,
)
from .identity import (
    fingerprint,
    nonnegative,
    optional_token,
    required_token,
    stable_ref,
)
from .observation import (
    GoalObservation,
    GoalObservationQuery,
    resolve_goal_observation,
)
from .persistence import (
    GoalEventKind,
    GoalJournal,
    GoalJournalEvent,
    GoalOperationalRecord,
    GoalStateStore,
    ReplayResult,
    append_journal_event,
    decode_goal_operational_record,
    encode_goal_operational_record,
    replay_journal,
)
from .reconciliation import (
    GoalReconciliationIntent,
    ReconciliationResult,
    apply_reconciliation_intent,
)
from .state_machine import apply_goal_intent


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
class GoalOperationReceipt:
    receipt_ref: str
    authority_ref: str
    client_intent_id: str
    authority_generation: int
    store_generation: int
    observation_cursor: int
    state_digest: str
    goal_ref: str | None = None
    lane_ref: str | None = None
    row_ref: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "receipt_ref",
            "authority_ref",
            "client_intent_id",
            "state_digest",
        ):
            required_token(getattr(self, field), field)
        nonnegative(self.authority_generation, "authority_generation")
        if nonnegative(self.store_generation, "store_generation") < 1:
            raise ValueError("store_generation must be positive")
        if nonnegative(self.observation_cursor, "observation_cursor") < 1:
            raise ValueError("observation_cursor must be positive")
        for field in ("goal_ref", "lane_ref", "row_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        if self.row_ref is not None and self.lane_ref is None:
            raise ValueError("row_ref requires lane_ref")


@dataclass(frozen=True, slots=True)
class HostResult:
    outcome: HostOutcome
    transition: TransitionResult | None = None
    reconciliation: ReconciliationResult | None = None
    receipt: GoalOperationReceipt | None = None
    blocker_code: str | None = None


class GoalOperationalRuntimeHost:
    """Bounded persistence-first owner for the neutral Workflow Goal reducer."""

    def __init__(
        self,
        store: GoalStateStore,
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
        state: GoalOperationalState,
        *,
        epoch: str,
    ) -> bool:
        required_token(authority_ref, "authority_ref")
        required_token(epoch, "epoch")
        if self.is_closed or state.authority.authority_ref != authority_ref:
            return False
        record = GoalOperationalRecord(
            authority_ref=authority_ref,
            state=state,
            journal=GoalJournal(epoch=epoch, retention_limit=self._journal_retention),
        )
        return self._store.create(
            authority_ref,
            encode_goal_operational_record(record),
        ).applied

    def read(self, authority_ref: str) -> GoalOperationalRecord | None:
        persisted = self._store.read(authority_ref)
        return (
            None
            if persisted is None
            else decode_goal_operational_record(persisted.payload)
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

    def observe(
        self,
        authority_ref: str,
        query: GoalObservationQuery,
    ) -> GoalObservation | None:
        persisted = self._store.read(authority_ref)
        if persisted is None:
            return None
        record = decode_goal_operational_record(persisted.payload)
        return resolve_goal_observation(
            record.state,
            query,
            store_generation=persisted.generation,
            epoch=record.journal.epoch,
            journal_cursor=record.journal.latest_cursor or 0,
            state_digest=_record_digest(record),
        )

    def submit(
        self,
        authority_ref: str,
        intent: GoalIntent,
        *,
        cancellation: CancellationToken | None = None,
    ) -> HostResult:
        return self._admit(
            authority_ref,
            cancellation,
            lambda: self._submit_locked(authority_ref, intent, cancellation),
        )

    def reconcile(
        self,
        authority_ref: str,
        intent: GoalReconciliationIntent,
        *,
        cancellation: CancellationToken | None = None,
    ) -> HostResult:
        return self._admit(
            authority_ref,
            cancellation,
            lambda: self._reconcile_locked(authority_ref, intent, cancellation),
        )

    def _admit(
        self,
        authority_ref: str,
        cancellation: CancellationToken | None,
        operation,
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
                return operation()
        finally:
            self._admission.release()

    def _submit_locked(
        self,
        authority_ref: str,
        intent: GoalIntent,
        cancellation: CancellationToken | None,
    ) -> HostResult:
        persisted, record, early = self._read_for_mutation(authority_ref, cancellation)
        if early is not None:
            return early
        assert persisted is not None and record is not None
        result = apply_goal_intent(record.state, intent)
        if not result.changed:
            receipt = (
                _receipt_from_event(
                    record,
                    intent.context.client_intent_id,
                )
                if result.outcome is TransitionOutcome.IDEMPOTENT
                else None
            )
            return HostResult(HostOutcome.COMPLETED, transition=result, receipt=receipt)
        if cancellation is not None and cancellation.is_cancelled:
            return HostResult(HostOutcome.CANCELLED, blocker_code="cancelled")
        proposed = replace(record, state=result.state)
        return self._persist_transition(
            persisted_generation=persisted.generation,
            record=proposed,
            kind=_event_kind(intent),
            client_intent_id=intent.context.client_intent_id,
            goal_ref=result.goal_ref,
            lane_ref=result.lane_ref,
            row_ref=result.row_ref,
            transition=result,
            reconciliation=None,
            cancellation=cancellation,
        )

    def _reconcile_locked(
        self,
        authority_ref: str,
        intent: GoalReconciliationIntent,
        cancellation: CancellationToken | None,
    ) -> HostResult:
        persisted, record, early = self._read_for_mutation(authority_ref, cancellation)
        if early is not None:
            return early
        assert persisted is not None and record is not None
        result = apply_reconciliation_intent(
            record.reconciliation,
            intent,
            authority_generation=record.state.authority.generation,
        )
        if not result.changed:
            receipt = (
                _receipt_from_event(record, intent.context.client_intent_id)
                if result.outcome is TransitionOutcome.IDEMPOTENT
                else None
            )
            return HostResult(
                HostOutcome.COMPLETED,
                reconciliation=result,
                receipt=receipt,
            )
        if cancellation is not None and cancellation.is_cancelled:
            return HostResult(HostOutcome.CANCELLED, blocker_code="cancelled")
        return self._persist_transition(
            persisted_generation=persisted.generation,
            record=replace(record, reconciliation=result.state),
            kind=GoalEventKind.RECONCILIATION_CHANGED,
            client_intent_id=intent.context.client_intent_id,
            goal_ref=None,
            lane_ref=None,
            row_ref=None,
            transition=None,
            reconciliation=result,
            cancellation=cancellation,
        )

    def _persist_transition(
        self,
        *,
        persisted_generation: int,
        record: GoalOperationalRecord,
        kind: GoalEventKind,
        client_intent_id: str,
        goal_ref: str | None,
        lane_ref: str | None,
        row_ref: str | None,
        transition: TransitionResult | None,
        reconciliation: ReconciliationResult | None,
        cancellation: CancellationToken | None,
    ) -> HostResult:
        store_generation = persisted_generation + 1
        cursor = record.journal.next_cursor
        digest = _record_digest(record)
        receipt = _receipt(
            authority_ref=record.authority_ref,
            client_intent_id=client_intent_id,
            authority_generation=record.state.authority.generation,
            store_generation=store_generation,
            observation_cursor=cursor,
            state_digest=digest,
            goal_ref=goal_ref,
            lane_ref=lane_ref,
            row_ref=row_ref,
        )
        proposed = append_journal_event(
            record,
            kind=kind,
            client_intent_id=client_intent_id,
            store_generation=store_generation,
            receipt_ref=receipt.receipt_ref,
            state_digest=digest,
            goal_ref=goal_ref,
            lane_ref=lane_ref,
            row_ref=row_ref,
        )
        if cancellation is not None and cancellation.is_cancelled:
            return HostResult(HostOutcome.CANCELLED, blocker_code="cancelled")
        write = self._store.compare_and_set(
            record.authority_ref,
            expected_generation=persisted_generation,
            payload=encode_goal_operational_record(proposed),
        )
        if not write.applied:
            return HostResult(
                HostOutcome.PERSISTENCE_CONFLICT,
                blocker_code="persistence_generation_conflict",
            )
        return HostResult(
            HostOutcome.COMPLETED,
            transition=transition,
            reconciliation=reconciliation,
            receipt=receipt,
        )

    def _read_for_mutation(
        self,
        authority_ref: str,
        cancellation: CancellationToken | None,
    ):
        if self.is_closed:
            return (
                None,
                None,
                HostResult(
                    HostOutcome.REJECTED,
                    blocker_code="host_closed",
                ),
            )
        if cancellation is not None and cancellation.is_cancelled:
            return (
                None,
                None,
                HostResult(
                    HostOutcome.CANCELLED,
                    blocker_code="cancelled",
                ),
            )
        persisted = self._store.read(authority_ref)
        if persisted is None:
            return (
                None,
                None,
                HostResult(
                    HostOutcome.UNRESOLVED,
                    blocker_code="authority_unresolved",
                ),
            )
        return persisted, decode_goal_operational_record(persisted.payload), None

    def _lock_for(self, authority_ref: str) -> Lock:
        with self._catalog_lock:
            return self._authority_locks.setdefault(authority_ref, Lock())


def _record_digest(record: GoalOperationalRecord) -> str:
    return fingerprint(
        {
            "state": record.state.to_wire(),
            "reconciliation": record.reconciliation.to_wire(),
        }
    )


def _receipt(
    *,
    authority_ref: str,
    client_intent_id: str,
    authority_generation: int,
    store_generation: int,
    observation_cursor: int,
    state_digest: str,
    goal_ref: str | None,
    lane_ref: str | None,
    row_ref: str | None,
) -> GoalOperationReceipt:
    receipt_ref = stable_ref(
        kind="goal-operation-receipt",
        authority_ref=authority_ref,
        coordinates=(
            client_intent_id,
            str(authority_generation),
            str(store_generation),
            str(observation_cursor),
            state_digest,
        ),
    )
    return GoalOperationReceipt(
        receipt_ref=receipt_ref,
        authority_ref=authority_ref,
        client_intent_id=client_intent_id,
        authority_generation=authority_generation,
        store_generation=store_generation,
        observation_cursor=observation_cursor,
        state_digest=state_digest,
        goal_ref=goal_ref,
        lane_ref=lane_ref,
        row_ref=row_ref,
    )


def _receipt_from_event(
    record: GoalOperationalRecord,
    client_intent_id: str,
) -> GoalOperationReceipt | None:
    event = next(
        (
            item
            for item in reversed(record.journal.events)
            if item.client_intent_id == client_intent_id
        ),
        None,
    )
    if event is None:
        return None
    return _receipt_from_journal_event(event)


def _receipt_from_journal_event(event: GoalJournalEvent) -> GoalOperationReceipt:
    return GoalOperationReceipt(
        receipt_ref=event.receipt_ref,
        authority_ref=event.authority_ref,
        client_intent_id=event.client_intent_id,
        authority_generation=event.authority_generation,
        store_generation=event.store_generation,
        observation_cursor=event.cursor,
        state_digest=event.state_digest,
        goal_ref=event.goal_ref,
        lane_ref=event.lane_ref,
        row_ref=event.row_ref,
    )


def _event_kind(intent: GoalIntent) -> GoalEventKind:
    if isinstance(intent, (EnsureGoalIntent,)):
        return GoalEventKind.GOAL_CHANGED
    if isinstance(intent, EnsureGoalLaneIntent):
        return GoalEventKind.LANE_CHANGED
    if isinstance(
        intent,
        (
            AppendGoalLaneIssueIntent,
            LinkGoalLaneIssueIntent,
            SyncGoalLaneIssueIntent,
        ),
    ):
        return GoalEventKind.ROW_CHANGED
    if isinstance(intent, AppendGoalUpdateIntent):
        return GoalEventKind.UPDATE_APPENDED
    return GoalEventKind.GOAL_CHANGED
