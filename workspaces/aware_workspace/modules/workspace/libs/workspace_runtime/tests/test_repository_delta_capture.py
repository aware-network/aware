from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aware_workspace_runtime import (
    ObservationChangeKind,
    RepositoryContentDeltaState,
    RepositoryDeltaCapturePathState,
    RepositoryObservationChange,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryDeltaCaptureCoordinator,
    WorkspaceRepositoryDeltaCapturePolicy,
    WorkspaceRepositoryObservationBatch,
    WorkspaceRepositoryObservationSnapshot,
    repository_snapshot_digest,
)
from test_repository_delta_retention_client import retained


def _entry(root: Path, path: str) -> RepositorySnapshotEntry:
    source = root / path
    metadata = source.stat()
    return RepositorySnapshotEntry(
        path=path,
        size_bytes=metadata.st_size,
        modified_ns=metadata.st_mtime_ns,
    )


def _snapshot(
    binding: WorkspaceRepositoryBinding,
    *,
    epoch: str,
    cursor: int,
    entries: tuple[RepositorySnapshotEntry, ...],
) -> WorkspaceRepositoryObservationSnapshot:
    return WorkspaceRepositoryObservationSnapshot(
        binding_key=binding.binding_key or "",
        epoch=epoch,
        cursor=cursor,
        observed_at=datetime.now(UTC),
        snapshot_digest=repository_snapshot_digest(entries),
        entries=entries,
    )


def _batch(
    binding: WorkspaceRepositoryBinding,
    *,
    before: WorkspaceRepositoryObservationSnapshot,
    after: WorkspaceRepositoryObservationSnapshot,
    changes: tuple[RepositoryObservationChange, ...],
) -> WorkspaceRepositoryObservationBatch:
    return WorkspaceRepositoryObservationBatch(
        binding_key=binding.binding_key or "",
        epoch=before.epoch,
        cursor=after.cursor,
        observed_at=after.observed_at,
        before_snapshot_digest=before.snapshot_digest,
        after_snapshot_digest=after.snapshot_digest,
        changes=changes,
    )


def _coordinator(
    tmp_path: Path,
) -> tuple[
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryDeltaCaptureCoordinator,
]:
    binding = WorkspaceRepositoryBinding(tmp_path)
    store = retained(
        repository_binding_ref=binding.binding_key or "",
        state_root=tmp_path / ".state",
    )
    return (
        binding,
        store,
        WorkspaceRepositoryDeltaCaptureCoordinator(binding=binding, store=store),
    )


def test_prepare_reads_only_selected_present_paths_and_records_absence(
    tmp_path: Path,
) -> None:
    (tmp_path / "selected.txt").write_bytes(b"selected\n")
    (tmp_path / "unselected.txt").write_bytes(b"unselected\n")
    binding, store, coordinator = _coordinator(tmp_path)
    snapshot = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=0,
        entries=(_entry(tmp_path, "selected.txt"), _entry(tmp_path, "unselected.txt")),
    )

    capture = coordinator.prepare(
        snapshot=snapshot,
        selected_paths=("selected.txt", "future.txt"),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
        context_refs=("work:one",),
    )

    assert capture.selected_paths == ("future.txt", "selected.txt")
    assert capture.path_states[0].state is RepositoryDeltaCapturePathState.ABSENT
    assert capture.path_states[1].state is RepositoryDeltaCapturePathState.COVERED
    metrics = coordinator.metrics()
    assert metrics.selected_body_read_count == 1
    assert metrics.selected_body_read_bytes == len(b"selected\n")
    assert store.snapshot().retained_body_count == 1
    assert store.snapshot().metrics.body_read_count == 0


def test_no_change_and_unrelated_batches_add_zero_body_io(tmp_path: Path) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"selected\n")
    other = tmp_path / "other.txt"
    other.write_bytes(b"one\n")
    binding, store, coordinator = _coordinator(tmp_path)
    before = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=0,
        entries=(_entry(tmp_path, "other.txt"), _entry(tmp_path, "selected.txt")),
    )
    coordinator.prepare(
        snapshot=before,
        selected_paths=("selected.txt",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    initial_store = store.snapshot().metrics

    assert coordinator.observe(None) == ()
    other.write_bytes(b"two and changed\n")
    after = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=1,
        entries=(_entry(tmp_path, "other.txt"), _entry(tmp_path, "selected.txt")),
    )
    unrelated = _batch(
        binding,
        before=before,
        after=after,
        changes=(
            RepositoryObservationChange(
                ObservationChangeKind.UPDATE,
                "other.txt",
                _entry(tmp_path, "other.txt"),
            ),
        ),
    )
    assert coordinator.observe(unrelated) == ()
    final_store = store.snapshot().metrics
    assert final_store.body_hash_count == initial_store.body_hash_count
    assert final_store.body_write_count == initial_store.body_write_count
    assert final_store.body_read_count == initial_store.body_read_count == 0
    assert coordinator.metrics().no_change_count == 1


def test_changed_selected_path_reads_and_hashes_target_once(tmp_path: Path) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    binding, store, coordinator = _coordinator(tmp_path)
    before = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=0,
        entries=(_entry(tmp_path, "selected.txt"),),
    )
    capture = coordinator.prepare(
        snapshot=before,
        selected_paths=("selected.txt",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    initial_hashes = store.snapshot().metrics.body_hash_count
    source.write_bytes(b"after and changed\n")
    after_entry = _entry(tmp_path, "selected.txt")
    after = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=1,
        entries=(after_entry,),
    )
    batch = _batch(
        binding,
        before=before,
        after=after,
        changes=(
            RepositoryObservationChange(
                ObservationChangeKind.UPDATE, "selected.txt", after_entry
            ),
        ),
    )

    deltas = coordinator.observe(batch)
    assert len(deltas) == 1
    delta = deltas[0]
    assert delta.capture_ref == capture.capture_ref
    assert delta.state is RepositoryContentDeltaState.AVAILABLE
    assert store.snapshot().metrics.body_hash_count == initial_hashes + 1
    assert store.resolve_body(delta.old_body_ref or "") == b"before\n"
    assert store.resolve_body(delta.new_body_ref or "") == b"after and changed\n"
    metrics = coordinator.metrics()
    assert metrics.changed_body_read_count == 1
    assert metrics.changed_body_read_bytes == len(b"after and changed\n")


def test_repeated_context_preparation_and_batch_share_capture_and_delta(
    tmp_path: Path,
) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    binding, store, coordinator = _coordinator(tmp_path)
    before = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=0,
        entries=(_entry(tmp_path, "selected.txt"),),
    )
    captures = tuple(
        coordinator.prepare(
            snapshot=before,
            selected_paths=("selected.txt",),
            policy=WorkspaceRepositoryDeltaCapturePolicy(),
            context_refs=(f"work:{index}",),
        )
        for index in range(10)
    )
    assert len({value.capture_ref for value in captures}) == 1
    assert coordinator.metrics().selected_body_read_count == 1

    source.write_bytes(b"after\n")
    target = _entry(tmp_path, "selected.txt")
    after = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=1,
        entries=(target,),
    )
    batch = _batch(
        binding,
        before=before,
        after=after,
        changes=(
            RepositoryObservationChange(
                ObservationChangeKind.UPDATE, "selected.txt", target
            ),
        ),
    )
    first = coordinator.observe(batch)
    repeated = coordinator.observe(batch)
    assert repeated == first
    assert len(first) == 1
    assert coordinator.metrics().changed_body_read_count == 1
    assert store.snapshot().retained_delta_count == 1


def test_disappearing_target_is_typed_missing_target_without_false_body(
    tmp_path: Path,
) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    binding, store, coordinator = _coordinator(tmp_path)
    before = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=0,
        entries=(_entry(tmp_path, "selected.txt"),),
    )
    coordinator.prepare(
        snapshot=before,
        selected_paths=("selected.txt",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(maximum_read_attempts=1),
    )
    source.write_bytes(b"reported target\n")
    target = _entry(tmp_path, "selected.txt")
    after = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=1,
        entries=(target,),
    )
    source.unlink()
    batch = _batch(
        binding,
        before=before,
        after=after,
        changes=(
            RepositoryObservationChange(
                ObservationChangeKind.UPDATE, "selected.txt", target
            ),
        ),
    )

    delta = coordinator.observe(batch)[0]
    assert delta.state is RepositoryContentDeltaState.MISSING_TARGET
    assert delta.new_body_ref is None
    assert coordinator.metrics().unstable_body_count == 1


def test_per_capture_budget_can_reject_shared_target_without_second_read(
    tmp_path: Path,
) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"old\n")
    binding, _store, coordinator = _coordinator(tmp_path)
    before = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=0,
        entries=(_entry(tmp_path, "selected.txt"),),
    )
    coordinator.prepare(
        snapshot=before,
        selected_paths=("selected.txt",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(
            maximum_selected_bytes=8,
            maximum_body_bytes=8,
        ),
    )
    source.write_bytes(b"0123456789\n")
    target = _entry(tmp_path, "selected.txt")
    after = _snapshot(
        binding,
        epoch="epoch:one",
        cursor=1,
        entries=(target,),
    )
    batch = _batch(
        binding,
        before=before,
        after=after,
        changes=(
            RepositoryObservationChange(
                ObservationChangeKind.UPDATE, "selected.txt", target
            ),
        ),
    )

    delta = coordinator.observe(batch)[0]
    assert delta.state is RepositoryContentDeltaState.OVER_BUDGET
    assert delta.new_body_ref is None
    assert coordinator.metrics().changed_body_read_count == 0
