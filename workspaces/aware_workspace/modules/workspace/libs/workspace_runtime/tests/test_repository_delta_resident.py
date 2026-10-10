from __future__ import annotations

import asyncio
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aware_workspace_runtime import (
    ObservationChangeKind,
    RepositoryDeltaResidentState,
    RepositoryObservationChange,
    RepositoryProviderObservation,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryDeltaResident,
    WorkspaceRepositoryObservationSession,
)
from test_repository_delta_retention_client import retained


class _Provider:
    def __init__(
        self,
        root_path: Path,
        initial: RepositoryProviderObservation,
    ) -> None:
        self._root_path = root_path.resolve()
        self.initial = initial
        self.polls: deque[RepositoryProviderObservation] = deque()
        self.poll_calls = 0

    @property
    def root_path(self) -> Path:
        return self._root_path

    async def initialize(self) -> RepositoryProviderObservation:
        return self.initial

    async def poll(self) -> RepositoryProviderObservation:
        self.poll_calls += 1
        return self.polls.popleft()


def _entry(root: Path, path: str) -> RepositorySnapshotEntry:
    metadata = (root / path).stat()
    return RepositorySnapshotEntry(
        path=path,
        size_bytes=metadata.st_size,
        modified_ns=metadata.st_mtime_ns,
    )


def _observation(
    entries: tuple[RepositorySnapshotEntry, ...],
    changes: tuple[RepositoryObservationChange, ...] = (),
) -> RepositoryProviderObservation:
    return RepositoryProviderObservation(
        observed_at=datetime.now(UTC),
        entries=entries,
        changes=changes,
    )


def _resident(
    tmp_path: Path,
    provider: _Provider,
) -> tuple[
    WorkspaceRepositoryObservationSession,
    WorkspaceRepositoryDeltaResident,
]:
    binding = WorkspaceRepositoryBinding(tmp_path)
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=provider,
        poll_interval=60,
    )
    store = retained(
        repository_binding_ref=binding.binding_key or "",
        state_root=tmp_path / ".state",
    )
    return session, WorkspaceRepositoryDeltaResident(session=session, store=store)


@pytest.mark.asyncio
async def test_resident_prepares_large_scope_as_one_snapshot_bounded_batch(
    tmp_path: Path,
) -> None:
    paths = tuple(f"path-{index:03d}.txt" for index in range(88, -1, -1))
    for path in paths:
        (tmp_path / path).write_bytes(path.encode("utf-8"))
    entries = tuple(_entry(tmp_path, path) for path in sorted(paths))
    provider = _Provider(tmp_path, _observation(entries))
    session, resident = _resident(tmp_path, provider)

    captures = await resident.prepare_batch(
        selected_paths=paths,
        context_refs=("issue:large",),
    )

    assert tuple(len(capture.selected_paths) for capture in captures) == (64, 25)
    assert len({capture.admitted_coordinate for capture in captures}) == 1
    assert tuple(
        path for capture in captures for path in capture.selected_paths
    ) == tuple(sorted(paths))
    assert provider.poll_calls == 0
    assert resident.snapshot().capture.selected_body_read_count == 89

    await resident.stop()
    await session.stop()


@pytest.mark.asyncio
async def test_resident_consumes_published_batch_without_a_second_scan(
    tmp_path: Path,
) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    before_entry = _entry(tmp_path, "selected.txt")
    provider = _Provider(tmp_path, _observation((before_entry,)))
    session, resident = _resident(tmp_path, provider)
    await session.start(background=False)
    capture = await resident.prepare(
        selected_paths=("selected.txt",),
        context_refs=("issue:one",),
    )
    assert provider.poll_calls == 0

    source.write_bytes(b"after\n")
    after_entry = _entry(tmp_path, "selected.txt")
    provider.polls.append(
        _observation(
            (after_entry,),
            (
                RepositoryObservationChange(
                    kind=ObservationChangeKind.UPDATE,
                    path="selected.txt",
                    entry=after_entry,
                ),
            ),
        )
    )
    assert await session.poll_once() is not None
    assert provider.poll_calls == 1

    async def resolved() -> bool:
        for _ in range(100):
            snapshot = resident.snapshot()
            if (
                snapshot.store.retained_delta_count == 1
                and snapshot.observed_cursor == 1
            ):
                return True
            await asyncio.sleep(0.005)
        return False

    assert await resolved()
    snapshot = resident.snapshot()
    assert snapshot.state is RepositoryDeltaResidentState.FOLLOWING
    assert snapshot.observed_cursor == 1
    assert snapshot.capture.observed_batch_count == 1
    assert snapshot.capture.changed_body_read_count == 1
    assert snapshot.store.retained_capture_count == 1
    assert resident.store.resolve_capture(capture.capture_ref) is not None

    await resident.stop()
    await session.stop()


@pytest.mark.asyncio
async def test_observer_publication_does_not_wait_for_delta_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    before_entry = _entry(tmp_path, "selected.txt")
    provider = _Provider(tmp_path, _observation((before_entry,)))
    session, resident = _resident(tmp_path, provider)
    await session.start(background=False)
    await resident.prepare(selected_paths=("selected.txt",))

    capture_started = asyncio.Event()
    allow_capture = asyncio.Event()
    original = resident.coordinator.observe_async

    async def held(batch: object) -> object:
        capture_started.set()
        await allow_capture.wait()
        return await original(batch)  # type: ignore[arg-type]

    monkeypatch.setattr(resident.coordinator, "observe_async", held)
    source.write_bytes(b"after\n")
    after_entry = _entry(tmp_path, "selected.txt")
    provider.polls.append(
        _observation(
            (after_entry,),
            (
                RepositoryObservationChange(
                    kind=ObservationChangeKind.UPDATE,
                    path="selected.txt",
                    entry=after_entry,
                ),
            ),
        )
    )

    batch = await asyncio.wait_for(session.poll_once(), timeout=0.1)
    assert batch is not None
    await asyncio.wait_for(capture_started.wait(), timeout=0.1)
    assert resident.snapshot().store.retained_delta_count == 0
    allow_capture.set()

    for _ in range(100):
        if resident.snapshot().store.retained_delta_count == 1:
            break
        await asyncio.sleep(0.005)
    assert resident.snapshot().store.retained_delta_count == 1

    await resident.stop()
    await session.stop()


@pytest.mark.asyncio
async def test_restart_reuses_capture_metadata_without_loading_body(
    tmp_path: Path,
) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    entry = _entry(tmp_path, "selected.txt")
    provider = _Provider(tmp_path, _observation((entry,)))
    binding = WorkspaceRepositoryBinding(tmp_path)
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=provider,
    )
    state_root = tmp_path / ".state"
    first_store = retained(
        repository_binding_ref=binding.binding_key or "",
        state_root=state_root,
    )
    first = WorkspaceRepositoryDeltaResident(session=session, store=first_store)
    await session.start(background=False)
    capture = await first.prepare(selected_paths=("selected.txt",))
    await first.stop()

    restarted_store = retained(
        repository_binding_ref=binding.binding_key or "",
        state_root=state_root,
    )
    restarted = WorkspaceRepositoryDeltaResident(
        session=session,
        store=restarted_store,
    )
    restored = await restarted.prepare(selected_paths=("selected.txt",))

    assert restored == capture
    snapshot = restarted.snapshot()
    assert snapshot.store.retained_capture_count == 1
    assert snapshot.store.metrics.body_read_count == 0
    assert snapshot.capture.selected_body_read_count == 0

    await restarted.stop()
    await session.stop()
