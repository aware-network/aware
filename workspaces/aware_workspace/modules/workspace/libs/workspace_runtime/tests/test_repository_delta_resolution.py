from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aware_workspace_runtime import (
    WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
    ObservationChangeKind,
    RepositoryContentDeltaResolutionState,
    RepositoryEvidenceCoordinateKind,
    RepositoryEvidencePosture,
    RepositoryEvidenceResolutionState,
    RepositoryObservationChange,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryChangedEntry,
    WorkspaceRepositoryChangeEvidence,
    WorkspaceRepositoryContentDeltaResolver,
    WorkspaceRepositoryDeltaCaptureCoordinator,
    WorkspaceRepositoryDeltaCapturePolicy,
    WorkspaceRepositoryEvidenceCoordinate,
    WorkspaceRepositoryObservationBatch,
    WorkspaceRepositoryObservationSnapshot,
    repository_change_evidence_ref,
    repository_changed_entry_ref,
    repository_content_delta_resolution_from_payload,
    repository_content_delta_resolution_payload,
    repository_snapshot_digest,
)
from test_repository_delta_retention_client import retained


def _entry(root: Path, path: str) -> RepositorySnapshotEntry:
    metadata = (root / path).stat()
    return RepositorySnapshotEntry(
        path=path,
        size_bytes=metadata.st_size,
        modified_ns=metadata.st_mtime_ns,
    )


def _snapshot(
    binding: WorkspaceRepositoryBinding,
    *,
    cursor: int,
    entries: tuple[RepositorySnapshotEntry, ...],
) -> WorkspaceRepositoryObservationSnapshot:
    return WorkspaceRepositoryObservationSnapshot(
        binding_key=binding.binding_key or "",
        epoch="epoch:one",
        cursor=cursor,
        observed_at=datetime.now(UTC),
        snapshot_digest=repository_snapshot_digest(entries),
        entries=entries,
    )


def _batch(
    binding: WorkspaceRepositoryBinding,
    before: WorkspaceRepositoryObservationSnapshot,
    after: WorkspaceRepositoryObservationSnapshot,
    entry: RepositorySnapshotEntry,
) -> WorkspaceRepositoryObservationBatch:
    return WorkspaceRepositoryObservationBatch(
        binding_key=binding.binding_key or "",
        epoch=before.epoch,
        cursor=after.cursor,
        observed_at=after.observed_at,
        before_snapshot_digest=before.snapshot_digest,
        after_snapshot_digest=after.snapshot_digest,
        changes=(
            RepositoryObservationChange(
                kind=ObservationChangeKind.UPDATE,
                path=entry.path,
                entry=entry,
            ),
        ),
    )


def _batch_many(
    binding: WorkspaceRepositoryBinding,
    before: WorkspaceRepositoryObservationSnapshot,
    after: WorkspaceRepositoryObservationSnapshot,
    entries: tuple[RepositorySnapshotEntry, ...],
) -> WorkspaceRepositoryObservationBatch:
    return WorkspaceRepositoryObservationBatch(
        binding_key=binding.binding_key or "",
        epoch=before.epoch,
        cursor=after.cursor,
        observed_at=after.observed_at,
        before_snapshot_digest=before.snapshot_digest,
        after_snapshot_digest=after.snapshot_digest,
        changes=tuple(
            RepositoryObservationChange(
                kind=ObservationChangeKind.UPDATE,
                path=entry.path,
                entry=entry,
            )
            for entry in entries
        ),
    )


def _evidence(
    binding: WorkspaceRepositoryBinding,
    batch: WorkspaceRepositoryObservationBatch,
) -> WorkspaceRepositoryChangeEvidence:
    from aware_workspace_runtime import (
        RepositoryChangedEntryKind,
        RepositoryObservationCoordinate,
    )

    before_observation = RepositoryObservationCoordinate(
        repository_binding_ref=binding.binding_key or "",
        epoch=batch.epoch,
        cursor=batch.cursor - 1,
        snapshot_digest=batch.before_snapshot_digest,
        visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
        visibility_policy_version=binding.filter_version,
    )
    after_observation = RepositoryObservationCoordinate(
        repository_binding_ref=binding.binding_key or "",
        epoch=batch.epoch,
        cursor=batch.cursor,
        snapshot_digest=batch.after_snapshot_digest,
        visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
        visibility_policy_version=binding.filter_version,
    )
    before = WorkspaceRepositoryEvidenceCoordinate(
        kind=RepositoryEvidenceCoordinateKind.OBSERVATION,
        repository_binding_ref=binding.binding_key or "",
        state_digest=batch.before_snapshot_digest,
        observation=before_observation,
    )
    after = WorkspaceRepositoryEvidenceCoordinate(
        kind=RepositoryEvidenceCoordinateKind.OBSERVATION,
        repository_binding_ref=binding.binding_key or "",
        state_digest=batch.after_snapshot_digest,
        observation=after_observation,
    )
    entries = tuple(
        WorkspaceRepositoryChangedEntry(
            changed_entry_ref=repository_changed_entry_ref(
                repository_binding_ref=binding.binding_key or "",
                before_coordinate=before,
                after_coordinate=after,
                kind=RepositoryChangedEntryKind.UPDATE,
                old_path=change.path,
                new_path=change.path,
            ),
            kind=RepositoryChangedEntryKind.UPDATE,
            posture=RepositoryEvidencePosture.PROVIDER_CORRELATED,
            before_coordinate=before,
            after_coordinate=after,
            old_path=change.path,
            new_path=change.path,
        )
        for change in batch.changes
    )
    now = datetime.now(UTC)
    evidence_key = "external:edit:one"
    return WorkspaceRepositoryChangeEvidence(
        evidence_ref=repository_change_evidence_ref(
            repository_binding_ref=binding.binding_key or "",
            evidence_key=evidence_key,
        ),
        evidence_key=evidence_key,
        revision=1,
        repository_binding_ref=binding.binding_key or "",
        posture=RepositoryEvidencePosture.PROVIDER_CORRELATED,
        resolution_state=RepositoryEvidenceResolutionState.RESOLVED,
        observed_at=now,
        before_coordinate=before,
        after_coordinate=after,
        changed_entries=entries,
        external_evidence_refs=("edit:one",),
        resolved_at=now,
    )


def _runtime(
    tmp_path: Path,
    *,
    body_capacity: int = 256,
) -> tuple[
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryDeltaCaptureCoordinator,
]:
    binding = WorkspaceRepositoryBinding(tmp_path)
    store = retained(
        repository_binding_ref=binding.binding_key or "",
        state_root=tmp_path / ".state",
        body_capacity=body_capacity,
    )
    return (
        binding,
        store,
        WorkspaceRepositoryDeltaCaptureCoordinator(binding=binding, store=store),
    )


def test_exact_evidence_resolves_delta_refs_without_body_reads(tmp_path: Path) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    binding, store, coordinator = _runtime(tmp_path)
    before = _snapshot(binding, cursor=0, entries=(_entry(tmp_path, source.name),))
    capture = coordinator.prepare(
        snapshot=before,
        selected_paths=(source.name,),
        context_refs=("issue:one",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    source.write_bytes(b"after\n")
    target = _entry(tmp_path, source.name)
    after = _snapshot(binding, cursor=1, entries=(target,))
    batch = _batch(binding, before, after, target)
    deltas = coordinator.observe(batch)
    body_reads = store.snapshot().metrics.body_read_count

    resolution = WorkspaceRepositoryContentDeltaResolver(store=store).resolve(
        _evidence(binding, batch),
        context_refs=("issue:one",),
        observed_epoch=batch.epoch,
        observed_cursor=batch.cursor,
    )

    assert resolution.state is RepositoryContentDeltaResolutionState.AVAILABLE
    assert resolution.capture_ref == capture.capture_ref
    assert resolution.delta_refs == (deltas[0].delta_ref,)
    assert store.snapshot().metrics.body_read_count == body_reads == 0
    assert (
        repository_content_delta_resolution_from_payload(
            repository_content_delta_resolution_payload(resolution)
        )
        == resolution
    )


def test_exact_evidence_resolves_across_disjoint_bounded_captures(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_bytes(b"first before\n")
    second.write_bytes(b"second before\n")
    binding, store, coordinator = _runtime(tmp_path)
    before = _snapshot(
        binding,
        cursor=0,
        entries=(_entry(tmp_path, first.name), _entry(tmp_path, second.name)),
    )
    captures = tuple(
        coordinator.prepare(
            snapshot=before,
            selected_paths=(path,),
            context_refs=("issue:one",),
            policy=WorkspaceRepositoryDeltaCapturePolicy(),
        )
        for path in (first.name, second.name)
    )
    first.write_bytes(b"first after\n")
    second.write_bytes(b"second after\n")
    targets = (_entry(tmp_path, first.name), _entry(tmp_path, second.name))
    after = _snapshot(binding, cursor=1, entries=targets)
    batch = _batch_many(binding, before, after, targets)
    deltas = coordinator.observe(batch)
    body_reads = store.snapshot().metrics.body_read_count

    resolution = WorkspaceRepositoryContentDeltaResolver(store=store).resolve(
        _evidence(binding, batch),
        context_refs=("issue:one",),
        observed_epoch=batch.epoch,
        observed_cursor=batch.cursor,
    )

    assert len({value.capture_ref for value in captures}) == 2
    assert resolution.state is RepositoryContentDeltaResolutionState.AVAILABLE
    assert resolution.capture_ref is None
    assert resolution.delta_refs == tuple(value.delta_ref for value in deltas)
    assert store.snapshot().metrics.body_read_count == body_reads == 0
    assert (
        repository_content_delta_resolution_from_payload(
            repository_content_delta_resolution_payload(resolution)
        )
        == resolution
    )


def test_cross_capture_evidence_fails_when_one_entry_has_no_preimage(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_bytes(b"first before\n")
    second.write_bytes(b"second before\n")
    binding, store, coordinator = _runtime(tmp_path)
    before = _snapshot(
        binding,
        cursor=0,
        entries=(_entry(tmp_path, first.name), _entry(tmp_path, second.name)),
    )
    coordinator.prepare(
        snapshot=before,
        selected_paths=(first.name,),
        context_refs=("issue:one",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    first.write_bytes(b"first after\n")
    second.write_bytes(b"second after\n")
    targets = (_entry(tmp_path, first.name), _entry(tmp_path, second.name))
    after = _snapshot(binding, cursor=1, entries=targets)
    batch = _batch_many(binding, before, after, targets)
    coordinator.observe(batch)

    resolution = WorkspaceRepositoryContentDeltaResolver(store=store).resolve(
        _evidence(binding, batch),
        context_refs=("issue:one",),
        observed_epoch=batch.epoch,
        observed_cursor=batch.cursor,
    )

    assert resolution.state is RepositoryContentDeltaResolutionState.MISSING_CAPTURE
    assert resolution.capture_ref is None
    assert resolution.delta_refs == ()


def test_context_mismatch_never_borrows_another_issue_capture(tmp_path: Path) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    binding, store, coordinator = _runtime(tmp_path)
    before = _snapshot(binding, cursor=0, entries=(_entry(tmp_path, source.name),))
    coordinator.prepare(
        snapshot=before,
        selected_paths=(source.name,),
        context_refs=("issue:one",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    source.write_bytes(b"after\n")
    target = _entry(tmp_path, source.name)
    after = _snapshot(binding, cursor=1, entries=(target,))
    batch = _batch(binding, before, after, target)
    coordinator.observe(batch)

    resolution = WorkspaceRepositoryContentDeltaResolver(store=store).resolve(
        _evidence(binding, batch),
        context_refs=("issue:two",),
        observed_epoch=batch.epoch,
        observed_cursor=batch.cursor,
    )

    assert resolution.state is RepositoryContentDeltaResolutionState.MISSING_CAPTURE
    assert resolution.delta_refs == ()


def test_resolver_reports_pending_before_resident_reaches_target_cursor(
    tmp_path: Path,
) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    binding, store, coordinator = _runtime(tmp_path)
    before = _snapshot(binding, cursor=0, entries=(_entry(tmp_path, source.name),))
    coordinator.prepare(
        snapshot=before,
        selected_paths=(source.name,),
        context_refs=("issue:one",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    source.write_bytes(b"after\n")
    target = _entry(tmp_path, source.name)
    after = _snapshot(binding, cursor=1, entries=(target,))
    batch = _batch(binding, before, after, target)

    resolution = WorkspaceRepositoryContentDeltaResolver(store=store).resolve(
        _evidence(binding, batch),
        context_refs=("issue:one",),
        observed_epoch=batch.epoch,
        observed_cursor=0,
    )

    assert resolution.state is RepositoryContentDeltaResolutionState.PENDING


def test_multiple_compatible_captures_fail_ambiguous(tmp_path: Path) -> None:
    selected = tmp_path / "selected.txt"
    selected.write_bytes(b"before\n")
    other = tmp_path / "other.txt"
    other.write_bytes(b"other\n")
    binding, store, coordinator = _runtime(tmp_path)
    before = _snapshot(
        binding,
        cursor=0,
        entries=(_entry(tmp_path, other.name), _entry(tmp_path, selected.name)),
    )
    for paths in ((selected.name,), (other.name, selected.name)):
        coordinator.prepare(
            snapshot=before,
            selected_paths=paths,
            context_refs=("issue:one",),
            policy=WorkspaceRepositoryDeltaCapturePolicy(),
        )
    selected.write_bytes(b"after\n")
    target = _entry(tmp_path, selected.name)
    after = _snapshot(
        binding,
        cursor=1,
        entries=(_entry(tmp_path, other.name), target),
    )
    batch = _batch(binding, before, after, target)
    coordinator.observe(batch)

    resolution = WorkspaceRepositoryContentDeltaResolver(store=store).resolve(
        _evidence(binding, batch),
        context_refs=("issue:one",),
        observed_epoch=batch.epoch,
        observed_cursor=batch.cursor,
    )

    assert resolution.state is RepositoryContentDeltaResolutionState.AMBIGUOUS
    assert resolution.delta_refs == ()


def test_evicted_body_and_resident_gap_remain_typed(tmp_path: Path) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    binding, store, coordinator = _runtime(tmp_path, body_capacity=2)
    before = _snapshot(binding, cursor=0, entries=(_entry(tmp_path, source.name),))
    coordinator.prepare(
        snapshot=before,
        selected_paths=(source.name,),
        context_refs=("issue:one",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    source.write_bytes(b"after\n")
    target = _entry(tmp_path, source.name)
    after = _snapshot(binding, cursor=1, entries=(target,))
    batch = _batch(binding, before, after, target)
    coordinator.observe(batch)
    store.record_body(b"force one referenced body out of the bounded CAS")
    resolver = WorkspaceRepositoryContentDeltaResolver(store=store)

    evicted = resolver.resolve(
        _evidence(binding, batch),
        context_refs=("issue:one",),
        observed_epoch=batch.epoch,
        observed_cursor=batch.cursor,
    )
    assert evicted.state is RepositoryContentDeltaResolutionState.EVICTED

    empty_root = tmp_path / "gap"
    empty_root.mkdir()
    gap_source = empty_root / "selected.txt"
    gap_source.write_bytes(b"before\n")
    gap_binding, gap_store, gap_coordinator = _runtime(empty_root)
    gap_before = _snapshot(
        gap_binding,
        cursor=0,
        entries=(_entry(empty_root, gap_source.name),),
    )
    gap_coordinator.prepare(
        snapshot=gap_before,
        selected_paths=(gap_source.name,),
        context_refs=("issue:one",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    gap_source.write_bytes(b"after\n")
    gap_target = _entry(empty_root, gap_source.name)
    gap_after = _snapshot(gap_binding, cursor=1, entries=(gap_target,))
    gap_batch = _batch(gap_binding, gap_before, gap_after, gap_target)
    gap = WorkspaceRepositoryContentDeltaResolver(store=gap_store).resolve(
        _evidence(gap_binding, gap_batch),
        context_refs=("issue:one",),
        observed_epoch=gap_batch.epoch,
        observed_cursor=0,
        resident_error="workspace_repository_delta_observation_gap:retention",
    )
    assert gap.state is RepositoryContentDeltaResolutionState.GAP
