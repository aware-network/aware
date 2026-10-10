from __future__ import annotations

from datetime import UTC, datetime

from aware_workspace_runtime import (
    ObservationChangeKind,
    ObservationGapReason,
    RepositoryObservationChange,
    RepositorySnapshotEntry,
    WorkspaceRepositoryObservationBatch,
    WorkspaceRepositoryObservationJournal,
    WorkspaceRepositoryObservationSnapshot,
    repository_snapshot_digest,
)


def _entry(index: int) -> RepositorySnapshotEntry:
    return RepositorySnapshotEntry(
        path=f"file-{index}.txt",
        size_bytes=index,
        modified_ns=index,
    )


def _append(
    journal: WorkspaceRepositoryObservationJournal,
    entries: list[RepositorySnapshotEntry],
) -> None:
    cursor = journal.current_cursor + 1
    entry = _entry(cursor)
    entries.append(entry)
    journal.append(
        WorkspaceRepositoryObservationBatch(
            binding_key="binding",
            epoch="epoch",
            cursor=cursor,
            observed_at=datetime.now(UTC),
            before_snapshot_digest=journal.current_snapshot_digest,
            after_snapshot_digest=repository_snapshot_digest(tuple(entries)),
            changes=(
                RepositoryObservationChange(
                    kind=ObservationChangeKind.CREATE,
                    path=entry.path,
                    entry=entry,
                ),
            ),
        )
    )


def _snapshot(
    journal: WorkspaceRepositoryObservationJournal,
    entries: list[RepositorySnapshotEntry],
) -> WorkspaceRepositoryObservationSnapshot:
    return WorkspaceRepositoryObservationSnapshot(
        binding_key="binding",
        epoch="epoch",
        cursor=journal.current_cursor,
        observed_at=datetime.now(UTC),
        snapshot_digest=journal.current_snapshot_digest,
        entries=tuple(entries),
    )


def test_journal_replay_and_retention_gap_are_explicit() -> None:
    journal = WorkspaceRepositoryObservationJournal(
        epoch="epoch",
        binding_key="binding",
        initial_snapshot_digest=repository_snapshot_digest(()),
        capacity=2,
    )
    entries: list[RepositorySnapshotEntry] = []
    for _ in range(3):
        _append(journal, entries)

    current = _snapshot(journal, entries)
    replay = journal.replay(requested_epoch="epoch", after_cursor=1, snapshot=current)
    assert [batch.cursor for batch in replay.batches] == [2, 3]

    gap = journal.replay(requested_epoch="epoch", after_cursor=0, snapshot=current).gap
    assert gap is not None
    assert gap.reason is ObservationGapReason.RETENTION_EXCEEDED
    assert gap.oldest_available_cursor == 2
    assert gap.reset_snapshot == current


def test_journal_epoch_and_ahead_cursor_return_reset_snapshot() -> None:
    journal = WorkspaceRepositoryObservationJournal(
        epoch="epoch",
        binding_key="binding",
        initial_snapshot_digest=repository_snapshot_digest(()),
        capacity=2,
    )
    current = _snapshot(journal, [])

    mismatch = journal.replay(
        requested_epoch="old", after_cursor=0, snapshot=current
    ).gap
    ahead = journal.replay(
        requested_epoch="epoch", after_cursor=1, snapshot=current
    ).gap

    assert mismatch and mismatch.reason is ObservationGapReason.EPOCH_MISMATCH
    assert ahead and ahead.reason is ObservationGapReason.CURSOR_AHEAD


def test_journal_rejects_non_monotonic_or_wrong_prestate() -> None:
    journal = WorkspaceRepositoryObservationJournal(
        epoch="epoch",
        binding_key="binding",
        initial_snapshot_digest=repository_snapshot_digest(()),
        capacity=2,
    )
    entry = _entry(1)
    invalid = WorkspaceRepositoryObservationBatch(
        binding_key="binding",
        epoch="epoch",
        cursor=2,
        observed_at=datetime.now(UTC),
        before_snapshot_digest="wrong",
        after_snapshot_digest=repository_snapshot_digest((entry,)),
        changes=(
            RepositoryObservationChange(
                kind=ObservationChangeKind.CREATE,
                path=entry.path,
                entry=entry,
            ),
        ),
    )
    try:
        journal.append(invalid)
    except ValueError as exc:
        assert "next journal cursor" in str(exc)
    else:
        raise AssertionError("invalid journal append unexpectedly succeeded")
