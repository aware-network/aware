from __future__ import annotations

from collections import deque

from .contracts import (
    ObservationGapReason,
    WorkspaceRepositoryObservationBatch,
    WorkspaceRepositoryObservationGap,
    WorkspaceRepositoryObservationReplay,
    WorkspaceRepositoryObservationSnapshot,
)


class WorkspaceRepositoryObservationJournal:
    """Bounded monotonic in-memory journal for one observation epoch."""

    def __init__(
        self,
        *,
        epoch: str,
        binding_key: str,
        initial_snapshot_digest: str,
        capacity: int,
    ) -> None:
        if capacity <= 0:
            raise ValueError("Observation journal capacity must be positive")
        self._epoch = epoch
        self._binding_key = binding_key
        self._capacity = capacity
        self._batches: deque[WorkspaceRepositoryObservationBatch] = deque(
            maxlen=capacity
        )
        self._current_cursor = 0
        self._current_snapshot_digest = initial_snapshot_digest

    @property
    def epoch(self) -> str:
        return self._epoch

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def current_cursor(self) -> int:
        return self._current_cursor

    @property
    def current_snapshot_digest(self) -> str:
        return self._current_snapshot_digest

    @property
    def oldest_available_cursor(self) -> int:
        if self._batches:
            return self._batches[0].cursor
        return self._current_cursor + 1

    def __len__(self) -> int:
        return len(self._batches)

    def append(self, batch: WorkspaceRepositoryObservationBatch) -> None:
        if batch.binding_key != self._binding_key or batch.epoch != self._epoch:
            raise ValueError("Observation batch authority does not match journal")
        if batch.cursor != self._current_cursor + 1:
            raise ValueError("Observation batch cursor is not the next journal cursor")
        if batch.before_snapshot_digest != self._current_snapshot_digest:
            raise ValueError("Observation batch pre-snapshot does not match journal")
        self._batches.append(batch)
        self._current_cursor = batch.cursor
        self._current_snapshot_digest = batch.after_snapshot_digest

    def replay(
        self,
        *,
        requested_epoch: str | None,
        after_cursor: int,
        snapshot: WorkspaceRepositoryObservationSnapshot,
    ) -> WorkspaceRepositoryObservationReplay:
        if after_cursor < 0:
            raise ValueError("Replay cursor must be non-negative")
        if snapshot.epoch != self._epoch or snapshot.cursor != self._current_cursor:
            raise ValueError("Replay snapshot does not match journal head")

        reason: ObservationGapReason | None = None
        if requested_epoch is not None and requested_epoch != self._epoch:
            reason = ObservationGapReason.EPOCH_MISMATCH
        elif after_cursor > self._current_cursor:
            reason = ObservationGapReason.CURSOR_AHEAD
        elif self._batches and after_cursor < self.oldest_available_cursor - 1:
            reason = ObservationGapReason.RETENTION_EXCEEDED

        if reason is not None:
            gap = WorkspaceRepositoryObservationGap(
                reason=reason,
                requested_epoch=requested_epoch,
                available_epoch=self._epoch,
                requested_after_cursor=after_cursor,
                oldest_available_cursor=self.oldest_available_cursor,
                current_cursor=self._current_cursor,
                reset_snapshot=snapshot,
            )
            return WorkspaceRepositoryObservationReplay(
                epoch=self._epoch,
                after_cursor=after_cursor,
                current_cursor=self._current_cursor,
                gap=gap,
            )

        batches = tuple(batch for batch in self._batches if batch.cursor > after_cursor)
        return WorkspaceRepositoryObservationReplay(
            epoch=self._epoch,
            after_cursor=after_cursor,
            current_cursor=self._current_cursor,
            batches=batches,
        )
