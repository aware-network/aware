from __future__ import annotations

import asyncio
import sys
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from aware_file_system.native_observation_service import (
    RustObservationServiceBuildConfig,
    prepare_rust_observation_service_binary,
)
from aware_file_system.native_snapshot import WorkspaceSnapshot
from aware_file_system.observation_backend import (
    BackendObservation,
    ObservationBackendMode,
    RustShadowObservationBackend,
    build_observation_backend,
)
from aware_workspace_runtime import (
    FileSystemBackendObservationProvider,
    FileSystemIndexObservationProvider,
    ObservationChangeKind,
    ObservationRuntimeState,
    RepositoryObservationChange,
    RepositoryProviderObservation,
    RepositorySnapshotEntry,
    WorkspaceObservationCheckpointError,
    WorkspaceObservationLeaseUnavailable,
    WorkspaceObservationNotStartedError,
    WorkspaceObservationProviderInvariantError,
    WorkspaceObservationRegistryConflict,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationRegistry,
    WorkspaceRepositoryObservationSession,
    WorkspaceRepositorySerializedEffect,
)
from aware_workspace_runtime.observation import _background_poll_delay


@pytest.fixture(scope="module")
def observation_service_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(
            target_dir=tmp_path_factory.mktemp("workspace-shadow-target")
        )
    )


class FakeProvider:
    def __init__(
        self,
        root_path: Path,
        initial: RepositoryProviderObservation,
    ) -> None:
        self._root_path = root_path.resolve()
        self.initial = initial
        self.polls: deque[RepositoryProviderObservation | Exception] = deque()
        self.initialize_calls = 0
        self.poll_calls = 0

    @property
    def root_path(self) -> Path:
        return self._root_path

    async def initialize(self) -> RepositoryProviderObservation:
        self.initialize_calls += 1
        return self.initial

    async def poll(self) -> RepositoryProviderObservation:
        self.poll_calls += 1
        value = self.polls.popleft()
        if isinstance(value, Exception):
            raise value
        return value


class RetryInitializeProvider(FakeProvider):
    def __init__(self, root_path: Path, initial: RepositoryProviderObservation) -> None:
        super().__init__(root_path, initial)
        self.fail_next_initialize = True

    async def initialize(self) -> RepositoryProviderObservation:
        self.initialize_calls += 1
        if self.fail_next_initialize:
            self.fail_next_initialize = False
            raise RuntimeError("initial scan unavailable")
        return self.initial


@pytest.mark.asyncio
async def test_workspace_session_authority_is_admitted_epoch_fenced_and_local(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )

    with pytest.raises(
        WorkspaceObservationNotStartedError,
        match="session authority is not admitted",
    ):
        session.observe_workspace_session(
            execution_id="codex:one",
            actor_ref="actor:one",
        )

    await session.admit()
    first = session.observe_workspace_session(
        execution_id="codex:one",
        actor_ref="actor:one",
    )
    assert first.startswith(f"workspace-session:{session.epoch}:")
    assert (
        session.observe_workspace_session(
            execution_id="codex:one",
            actor_ref="actor:one",
        )
        == first
    )
    assert (
        session.observe_workspace_session(
            execution_id="codex:two",
            actor_ref="actor:two",
        )
        != first
    )
    live_actor_ref = "535b4715-5861-59c6-b358-c250841182b2"
    live = session.observe_workspace_session(
        execution_id="codex-01a04187-a06c-7783-b6ff-02efd8582e7f",
        actor_ref=live_actor_ref,
    )
    assert live.startswith(f"workspace-session:{session.epoch}:")
    assert (
        session.observe_workspace_session(
            execution_id="codex-01a04187-a06c-7783-b6ff-02efd8582e7f",
            actor_ref=live_actor_ref,
        )
        == live
    )
    with pytest.raises(ValueError, match="workspace_session_participant_invalid"):
        session.observe_workspace_session(execution_id="codex:one", actor_ref="one")
    session.require_workspace_session_current(
        workspace_session_ref=first,
        execution_id="codex:one",
        actor_ref="actor:one",
    )

    await session.stop()
    with pytest.raises(
        WorkspaceObservationNotStartedError,
        match="session authority is stale",
    ):
        session.require_workspace_session_current(
            workspace_session_ref=first,
            execution_id="codex:one",
            actor_ref="actor:one",
        )
    await session.admit()
    replacement = session.observe_workspace_session(
        execution_id="codex:one",
        actor_ref="actor:one",
    )
    assert replacement != first
    with pytest.raises(
        WorkspaceObservationNotStartedError,
        match="session authority is stale",
    ):
        session.require_workspace_session_current(
            workspace_session_ref=first,
            execution_id="codex:one",
            actor_ref="actor:one",
        )


class SlowPollingProvider(FakeProvider):
    async def poll(self) -> RepositoryProviderObservation:
        self.poll_calls += 1
        await asyncio.sleep(0.02)
        return self.initial


class TargetedFakeProvider(FakeProvider):
    def __init__(
        self,
        root_path: Path,
        initial: RepositoryProviderObservation,
    ) -> None:
        super().__init__(root_path, initial)
        self.targeted: deque[RepositoryProviderObservation] = deque()
        self.observed_paths: list[tuple[str, ...]] = []

    async def observe_paths(
        self, paths: tuple[str, ...]
    ) -> RepositoryProviderObservation:
        self.observed_paths.append(paths)
        return self.targeted.popleft()


class GatedTargetedProvider(TargetedFakeProvider):
    def __init__(
        self,
        root_path: Path,
        initial: RepositoryProviderObservation,
    ) -> None:
        super().__init__(root_path, initial)
        self.targeted_started = asyncio.Event()
        self.release_targeted = asyncio.Event()

    async def observe_paths(
        self, paths: tuple[str, ...]
    ) -> RepositoryProviderObservation:
        self.observed_paths.append(paths)
        self.targeted_started.set()
        await self.release_targeted.wait()
        return self.targeted.popleft()


class StaticBackend:
    mode = ObservationBackendMode.PYTHON_REFERENCE

    def __init__(self, result: BackendObservation) -> None:
        self.result = result
        self.close_calls = 0

    def initialize(self, _request_id: str) -> BackendObservation:
        return self.result

    def poll(self, _request_id: str) -> BackendObservation:
        return self.result

    def close(self) -> None:
        self.close_calls += 1


class ScriptedIndex:
    def __init__(
        self, root_path: Path, observations: list[tuple[object, dict]]
    ) -> None:
        self.root_path = root_path.resolve()
        self._observations = deque(observations)

    def refresh_relative_metadata(self) -> tuple[object, dict]:
        return self._observations.popleft()


def _entry(path: str, version: int = 1) -> RepositorySnapshotEntry:
    return RepositorySnapshotEntry(
        path=path,
        size_bytes=version,
        modified_ns=version,
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


def _create(entry: RepositorySnapshotEntry) -> RepositoryObservationChange:
    return RepositoryObservationChange(
        kind=ObservationChangeKind.CREATE,
        path=entry.path,
        entry=entry,
    )


@pytest.mark.asyncio
async def test_empty_poll_does_not_advance_cursor_or_journal(tmp_path: Path) -> None:
    initial = _observation(())
    provider = FakeProvider(tmp_path, initial)
    provider.polls.append(initial)
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )

    first = await session.start(background=False)
    same = await session.start(background=False)
    assert first == same
    assert await session.poll_once() is None
    assert session.current_snapshot.cursor == 0
    assert session.health.journal_size == 0
    assert provider.initialize_calls == 1

    await session.stop()
    await session.stop()
    assert session.health.state is ObservationRuntimeState.STOPPED


@pytest.mark.asyncio
async def test_failed_initialization_can_retry_without_false_running_state(
    tmp_path: Path,
) -> None:
    provider = RetryInitializeProvider(tmp_path, _observation(()))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )

    with pytest.raises(RuntimeError, match="initial scan unavailable"):
        await session.start(background=False)
    assert session.health.state is ObservationRuntimeState.DEGRADED

    snapshot = await session.start(background=False)
    assert snapshot.cursor == 0
    assert session.health.state is ObservationRuntimeState.RUNNING
    assert provider.initialize_calls == 2


@pytest.mark.asyncio
async def test_poll_publishes_atomic_batch_and_many_readers_replay_independently(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    created = _entry("created.txt")
    provider.polls.append(_observation((created,), (_create(created),)))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
        journal_capacity=8,
    )
    await session.start(background=False)

    readers = [
        asyncio.create_task(
            session.replay(after_cursor=0, epoch=session.epoch, wait_timeout=1)
        )
        for _ in range(64)
    ]
    await asyncio.sleep(0)
    batch = await session.poll_once()
    replays = await asyncio.gather(*readers)

    assert batch is not None and batch.cursor == 1
    assert session.current_snapshot.entries == (created,)
    assert all([item.cursor for item in replay.batches] == [1] for replay in replays)


@pytest.mark.asyncio
async def test_serialized_effect_holds_writer_through_convergence_poll(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    created = _entry("created.txt")
    provider.polls.extend(
        (
            _observation((created,), (_create(created),)),
            _observation((created,)),
        )
    )
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)
    effect_started = asyncio.Event()
    release_effect = asyncio.Event()

    async def effect(snapshot):
        assert snapshot.cursor == 0
        effect_started.set()
        await release_effect.wait()
        return WorkspaceRepositorySerializedEffect(value="applied", poll_after=True)

    transition_task = asyncio.create_task(session.run_serialized_transition(effect))
    await effect_started.wait()
    competing_poll = asyncio.create_task(session.poll_once())
    await asyncio.sleep(0)
    assert provider.poll_calls == 0
    release_effect.set()

    transition = await transition_task
    await competing_poll
    assert transition.effect == "applied"
    assert transition.before.cursor == 0
    assert transition.batch is not None and transition.batch.cursor == 1
    assert transition.after.cursor == 1
    assert provider.poll_calls == 2


@pytest.mark.asyncio
async def test_serialized_effect_can_fail_admission_without_polling(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)

    transition = await session.run_serialized_transition(
        lambda _snapshot: WorkspaceRepositorySerializedEffect(
            value="stale",
            poll_after=False,
        )
    )

    assert transition.before == transition.after
    assert transition.batch is None
    assert provider.poll_calls == 0


@pytest.mark.asyncio
async def test_poll_failure_is_visible_and_does_not_publish(tmp_path: Path) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    provider.polls.append(RuntimeError("disk unavailable"))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)

    with pytest.raises(RuntimeError, match="disk unavailable"):
        await session.poll_once()

    assert session.current_snapshot.cursor == 0
    assert session.health.state is ObservationRuntimeState.DEGRADED
    assert session.health.consecutive_failures == 1
    assert session.health.last_error and "disk unavailable" in session.health.last_error


@pytest.mark.asyncio
async def test_background_loop_retries_failure_and_recovers_health(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    created = _entry("recovered.txt")
    provider.polls.extend(
        [
            RuntimeError("transient failure"),
            _observation((created,), (_create(created),)),
        ]
    )
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
        poll_interval=0.01,
    )
    await session.start(background=True)
    try:
        for _ in range(100):
            if session.current_snapshot.cursor == 1:
                break
            await asyncio.sleep(0.005)
        assert session.current_snapshot.cursor == 1
        assert session.health.state is ObservationRuntimeState.RUNNING
        assert session.health.consecutive_failures == 0
        assert session.health.last_error is None
    finally:
        await session.stop()


def test_background_poll_delay_caps_reference_scan_duty_cycle(
    tmp_path: Path,
) -> None:
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=FakeProvider(tmp_path, _observation(())),
        poll_interval=1.0,
        max_background_poll_duty_cycle=0.10,
    )

    assert session.next_background_poll_delay == 1.0
    assert (
        _background_poll_delay(
            minimum_interval=1.0,
            maximum_duty_cycle=0.10,
            poll_duration=0.01,
        )
        == 1.0
    )
    assert _background_poll_delay(
        minimum_interval=1.0,
        maximum_duty_cycle=0.10,
        poll_duration=16.0,
    ) == pytest.approx(144.0)


@pytest.mark.asyncio
async def test_background_loop_applies_measured_poll_cost_to_next_delay(
    tmp_path: Path,
) -> None:
    provider = SlowPollingProvider(tmp_path, _observation(()))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
        poll_interval=0.001,
        max_background_poll_duty_cycle=0.10,
    )
    await session.start(background=True)
    try:
        for _ in range(100):
            if session.next_background_poll_delay >= 0.15:
                break
            await asyncio.sleep(0.002)

        assert provider.poll_calls == 1
        assert session.next_background_poll_delay >= 0.15
    finally:
        await session.stop()


@pytest.mark.parametrize("maximum_duty_cycle", (0.0, -0.1, 1.01))
def test_background_poll_duty_cycle_must_be_bounded(
    tmp_path: Path, maximum_duty_cycle: float
) -> None:
    with pytest.raises(ValueError, match="duty cycle"):
        WorkspaceRepositoryObservationSession(
            binding=WorkspaceRepositoryBinding(tmp_path),
            provider=FakeProvider(tmp_path, _observation(())),
            max_background_poll_duty_cycle=maximum_duty_cycle,
        )


@pytest.mark.asyncio
async def test_concurrent_polls_serialize_as_one_monotonic_writer(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    entries: list[RepositorySnapshotEntry] = []
    for index in range(32):
        entry = _entry(f"file-{index}.txt", index + 1)
        entries.append(entry)
        provider.polls.append(_observation(tuple(entries), (_create(entry),)))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
        journal_capacity=32,
    )
    await session.start(background=False)

    batches = await asyncio.gather(*(session.poll_once() for _ in range(32)))

    assert [batch.cursor for batch in batches if batch is not None] == list(
        range(1, 33)
    )
    replay = await session.replay(after_cursor=0, epoch=session.epoch)
    assert [batch.cursor for batch in replay.batches] == list(range(1, 33))
    assert len(session.current_snapshot.entries) == 32


@pytest.mark.asyncio
async def test_provider_delta_must_exactly_reproduce_snapshot(tmp_path: Path) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    unreported = _entry("unreported.txt")
    provider.polls.append(_observation((unreported,)))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)

    with pytest.raises(
        WorkspaceObservationProviderInvariantError,
        match="changed without an explicit delta",
    ):
        await session.poll_once()
    assert session.current_snapshot.cursor == 0


@pytest.mark.asyncio
async def test_checkpoints_are_independent_monotonic_and_epoch_bound(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    created = _entry("created.txt")
    provider.polls.append(_observation((created,), (_create(created),)))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)
    await session.poll_once()

    issue = session.acknowledge(consumer_key="issue", epoch=session.epoch, cursor=1)
    agent = session.acknowledge(consumer_key="agent", epoch=session.epoch, cursor=0)
    assert issue.cursor == 1 and agent.cursor == 0
    assert session.checkpoint_for("issue") == issue

    with pytest.raises(WorkspaceObservationCheckpointError, match="backwards"):
        session.acknowledge(consumer_key="issue", epoch=session.epoch, cursor=0)
    with pytest.raises(WorkspaceObservationCheckpointError, match="epoch"):
        session.acknowledge(consumer_key="other", epoch="old", cursor=0)
    with pytest.raises(WorkspaceObservationCheckpointError, match="range"):
        session.acknowledge(consumer_key="other", epoch=session.epoch, cursor=2)


@pytest.mark.asyncio
async def test_registry_returns_singleton_and_rejects_incompatible_config(
    tmp_path: Path,
) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    registry = WorkspaceRepositoryObservationRegistry()
    providers: list[FakeProvider] = []

    def factory() -> FakeProvider:
        provider = FakeProvider(tmp_path, _observation(()))
        providers.append(provider)
        return provider

    first = await registry.acquire(binding=binding, provider_factory=factory)
    second = await registry.acquire(binding=binding, provider_factory=factory)
    assert first is second
    assert len(providers) == 1

    with pytest.raises(WorkspaceObservationRegistryConflict, match="incompatible"):
        await registry.acquire(
            binding=binding,
            provider_factory=factory,
            journal_capacity=1,
        )
    with pytest.raises(WorkspaceObservationRegistryConflict, match="incompatible"):
        await registry.acquire(
            binding=binding,
            provider_factory=factory,
            max_background_poll_duty_cycle=0.20,
        )

    other_root = tmp_path / "other"
    other_root.mkdir()
    colliding_binding = WorkspaceRepositoryBinding(
        other_root,
        binding_key=str(binding.binding_key),
    )
    with pytest.raises(WorkspaceObservationRegistryConflict, match="incompatible"):
        await registry.acquire(
            binding=colliding_binding,
            provider_factory=lambda: FakeProvider(other_root, _observation(())),
        )

    await registry.release(binding_key=str(binding.binding_key))


@pytest.mark.asyncio
async def test_os_writer_lease_rejects_competing_maintained_session(
    tmp_path: Path,
) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    first = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FakeProvider(tmp_path, _observation(())),
    )
    second = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FakeProvider(tmp_path, _observation(())),
    )
    await first.start(background=False)
    try:
        cold_snapshot = await FileSystemIndexObservationProvider(
            binding=binding
        ).initialize()
        assert cold_snapshot.entries == ()
        with pytest.raises(
            WorkspaceObservationLeaseUnavailable,
            match="already owns repository root",
        ):
            await second.start(background=False)
        assert second.health.state is ObservationRuntimeState.DEGRADED
    finally:
        await first.stop()

    recovered = await second.start(background=False)
    assert recovered.cursor == 0
    await second.stop()


@pytest.mark.asyncio
async def test_os_writer_lease_excludes_a_second_process(tmp_path: Path) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FakeProvider(tmp_path, _observation(())),
    )
    await session.start(background=False)
    script = """
from pathlib import Path
import sys
from aware_workspace_runtime import (
    FileWorkspaceRepositoryObservationLease,
    WorkspaceObservationLeaseUnavailable,
    WorkspaceRepositoryBinding,
)
lease = FileWorkspaceRepositoryObservationLease(
    binding=WorkspaceRepositoryBinding(Path(sys.argv[1]))
)
try:
    lease.acquire()
except WorkspaceObservationLeaseUnavailable:
    raise SystemExit(23)
raise SystemExit(0)
"""
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            script,
            str(tmp_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await process.communicate()
        assert process.returncode == 23, stderr.decode("utf-8")
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_restart_uses_a_new_epoch_and_invalidates_old_cursor(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)
    old_epoch = session.epoch
    await session.stop()
    await session.start(background=False)

    assert session.epoch != old_epoch
    gap = (await session.replay(after_cursor=0, epoch=old_epoch)).gap
    assert gap is not None
    assert gap.reset_snapshot.epoch == session.epoch


@pytest.mark.asyncio
async def test_real_filesystem_provider_create_update_delete(tmp_path: Path) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    provider = FileSystemIndexObservationProvider(binding=binding)
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=provider,
    )
    await session.start(background=False)

    target = tmp_path / "live.txt"
    target.write_text("one", encoding="utf-8")
    created = await session.poll_once()
    assert created and created.changes[0].kind is ObservationChangeKind.CREATE

    target.write_text("two-two", encoding="utf-8")
    updated = await session.poll_once()
    assert updated and updated.changes[0].kind is ObservationChangeKind.UPDATE

    target.unlink()
    deleted = await session.poll_once()
    assert deleted and deleted.changes[0].kind is ObservationChangeKind.DELETE
    assert session.current_snapshot.entries == ()
    await session.stop()


@pytest.mark.asyncio
async def test_restart_publishes_persisted_checkpoint_delta_without_second_scan(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    target = repository / "live.txt"
    target.write_text("before\n", encoding="utf-8")
    cache_dir = tmp_path / "source-index"
    binding = WorkspaceRepositoryBinding(repository)

    first = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FileSystemIndexObservationProvider(
            binding=binding,
            cache_dir=cache_dir,
        ),
    )
    cold = await first.start(background=False)
    assert cold.cursor == 0
    await first.stop()

    target.write_text("after with a different size\n", encoding="utf-8")
    provider = FileSystemIndexObservationProvider(
        binding=binding,
        cache_dir=cache_dir,
    )
    refresh = provider.index.refresh_relative_metadata
    scan_calls = 0

    def counted_refresh():
        nonlocal scan_calls
        scan_calls += 1
        return refresh()

    provider.index.refresh_relative_metadata = counted_refresh  # type: ignore[method-assign]
    restarted = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=provider,
    )
    advanced = await restarted.start(background=False)

    assert scan_calls == 1
    assert advanced.cursor == 1
    replay = await restarted.replay(after_cursor=0)
    assert len(replay.batches) == 1
    assert replay.batches[0].changes[0].path == "live.txt"
    assert replay.batches[0].changes[0].kind is ObservationChangeKind.UPDATE
    assert restarted.baseline_observed_at is not None
    assert restarted.baseline_observed_at < replay.batches[0].observed_at
    await restarted.stop()


@pytest.mark.asyncio
async def test_exact_path_observation_avoids_full_scan_and_deduplicates_reconcile(
    tmp_path: Path,
) -> None:
    target = tmp_path / "selected.txt"
    target.write_text("before", encoding="utf-8")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    for index in range(512):
        (unrelated / f"{index:04d}.txt").write_text("stable", encoding="utf-8")

    binding = WorkspaceRepositoryBinding(tmp_path)
    provider = FileSystemIndexObservationProvider(binding=binding)
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=provider,
    )
    await session.start(background=False)
    original_refresh = provider.index.refresh_relative_metadata
    full_scan_calls = 0

    def counted_refresh():
        nonlocal full_scan_calls
        full_scan_calls += 1
        return original_refresh()

    provider.index.refresh_relative_metadata = counted_refresh  # type: ignore[method-assign]
    target.write_text("after-with-a-different-size", encoding="utf-8")

    batch = await session.observe_paths_once(("selected.txt",))

    assert batch is not None
    assert [(change.kind, change.path) for change in batch.changes] == [
        (ObservationChangeKind.UPDATE, "selected.txt")
    ]
    assert full_scan_calls == 0
    assert session.current_snapshot.cursor == 1

    target.unlink()
    deleted = await session.observe_paths_once(("selected.txt",))
    assert deleted is not None
    assert [(change.kind, change.path) for change in deleted.changes] == [
        (ObservationChangeKind.DELETE, "selected.txt")
    ]
    assert full_scan_calls == 0

    created_path = tmp_path / "created.txt"
    created_path.write_text("created", encoding="utf-8")
    created = await session.observe_paths_once(("created.txt",))
    assert created is not None
    assert [(change.kind, change.path) for change in created.changes] == [
        (ObservationChangeKind.CREATE, "created.txt")
    ]
    assert full_scan_calls == 0
    assert await session.observe_paths_once(("created.txt",)) is None
    assert full_scan_calls == 0

    assert await session.poll_once() is None
    assert full_scan_calls == 1
    assert session.current_snapshot.cursor == 3
    assert session.health.journal_size == 3
    await session.stop()


@pytest.mark.asyncio
async def test_exact_path_observation_is_validated_and_published_normally(
    tmp_path: Path,
) -> None:
    initial = _observation(())
    created = _entry("lib/new.dart")
    provider = TargetedFakeProvider(tmp_path, initial)
    provider.targeted.append(_observation((created,), (_create(created),)))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)

    batch = await session.observe_paths_once(("lib/new.dart",))

    assert batch is not None and batch.cursor == 1
    assert provider.observed_paths == [("lib/new.dart",)]
    replay = await session.replay(after_cursor=0, epoch=session.epoch)
    assert replay.batches == (batch,)
    with pytest.raises(ValueError, match="must be unique"):
        await session.observe_paths_once(("lib/new.dart", "lib/new.dart"))
    with pytest.raises(ValueError, match="not confined"):
        await session.observe_paths_once(("../outside",))


@pytest.mark.asyncio
async def test_exact_path_and_full_poll_share_one_serial_writer(
    tmp_path: Path,
) -> None:
    initial = _observation(())
    created = _entry("lib/new.dart")
    provider = GatedTargetedProvider(tmp_path, initial)
    provider.targeted.append(_observation((created,), (_create(created),)))
    provider.polls.append(_observation((created,)))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)

    targeted = asyncio.create_task(session.observe_paths_once(("lib/new.dart",)))
    await provider.targeted_started.wait()
    reconcile = asyncio.create_task(session.poll_once())
    await asyncio.sleep(0)
    assert provider.poll_calls == 0

    provider.release_targeted.set()
    targeted_batch, reconcile_batch = await asyncio.gather(targeted, reconcile)

    assert targeted_batch is not None and targeted_batch.cursor == 1
    assert reconcile_batch is None
    assert provider.poll_calls == 1
    assert session.current_snapshot.cursor == 1
    assert session.health.journal_size == 1


@pytest.mark.asyncio
async def test_filesystem_provider_drops_transient_delete_absent_from_snapshots(
    tmp_path: Path,
) -> None:
    unchanged = SimpleNamespace(added={}, modified={}, deleted=set())
    transient_delete = SimpleNamespace(
        added={},
        modified={},
        deleted={"transient-test-artifact.png"},
    )
    index = ScriptedIndex(
        tmp_path,
        [(unchanged, {}), (transient_delete, {})],
    )
    provider = FileSystemIndexObservationProvider(
        binding=WorkspaceRepositoryBinding(tmp_path),
        index=index,  # type: ignore[arg-type]
    )
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )

    await session.start(background=False)

    assert await session.poll_once() is None
    assert session.current_snapshot.cursor == 0
    assert session.health.journal_size == 0
    await session.stop()


@pytest.mark.asyncio
async def test_backend_provider_rejects_root_mismatch_and_closes_candidate(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    result = BackendObservation(
        mode=ObservationBackendMode.PYTHON_REFERENCE,
        report={"added": [], "modified": [], "deleted": []},
        snapshot=WorkspaceSnapshot(
            backend_kind="python",
            benchmark_version="test",
            operation="test",
            root_path=other.as_posix(),
            entries=(),
        ),
    )
    backend = StaticBackend(result)
    provider = FileSystemBackendObservationProvider(
        binding=WorkspaceRepositoryBinding(root),
        backend_factory=lambda: backend,
    )

    with pytest.raises(ValueError, match="root does not match"):
        await provider.initialize()

    assert backend.close_calls == 1
    assert provider.mode is None


@pytest.mark.asyncio
async def test_backend_provider_reuses_validated_unchanged_snapshot(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    result = BackendObservation(
        mode=ObservationBackendMode.RUST_PRIMARY,
        report={"added": [], "modified": [], "deleted": []},
        snapshot=WorkspaceSnapshot(
            backend_kind="rust",
            benchmark_version="test",
            operation="maintained",
            root_path=root.as_posix(),
            entries=(),
            inventory_digest=(
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            ),
        ),
    )
    provider = FileSystemBackendObservationProvider(
        binding=WorkspaceRepositoryBinding(root),
        backend_factory=lambda: StaticBackend(result),
    )

    initial = await provider.initialize()
    maintained = await provider.poll()

    assert maintained.entries is initial.entries
    assert maintained.snapshot_digest == initial.snapshot_digest
    assert maintained.observed_at >= initial.observed_at
    assert maintained.changes == ()
    await provider.close()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux shadow gate only")
@pytest.mark.asyncio
async def test_explicit_rust_shadow_runs_beneath_workspace_lease_and_journal(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "source.txt").write_text("source\n", encoding="utf-8")
    binding = WorkspaceRepositoryBinding(root)
    created_backends: list[RustShadowObservationBackend] = []

    def backend_factory() -> RustShadowObservationBackend:
        backend = build_observation_backend(
            mode=ObservationBackendMode.RUST_SHADOW,
            workspace_root=root,
            cache_path=tmp_path / "native.cache",
            binary_path=observation_service_binary,
            shadow_sample_every=1,
        )
        assert isinstance(backend, RustShadowObservationBackend)
        created_backends.append(backend)
        return backend

    provider = FileSystemBackendObservationProvider(
        binding=binding,
        backend_factory=backend_factory,
    )
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=provider,
    )
    first = await session.start(background=False)
    first_epoch = session.epoch
    assert [entry.path for entry in first.entries] == ["source.txt"]
    assert provider.mode is ObservationBackendMode.RUST_SHADOW
    assert provider.last_backend_observation is not None
    assert provider.last_backend_observation.shadow_receipt is not None
    assert (
        provider.last_backend_observation.shadow_receipt["second_watcher_started"]
        is False
    )

    first_backend = created_backends[0]
    for _ in range(300):
        watcher = first_backend.service.health()["watcher"]
        if watcher["state"] == "active":
            break
        await asyncio.sleep(0.01)
    assert watcher["state"] == "active"
    assert watcher["watched_directory_count"] == 1
    first_process = first_backend.service._process

    competing_factory_calls = 0

    def competing_backend_factory() -> RustShadowObservationBackend:
        nonlocal competing_factory_calls
        competing_factory_calls += 1
        return backend_factory()

    competing = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FileSystemBackendObservationProvider(
            binding=binding,
            backend_factory=competing_backend_factory,
        ),
    )
    with pytest.raises(WorkspaceObservationLeaseUnavailable):
        await competing.start(background=False)
    assert competing_factory_calls == 0
    await competing.stop()

    live = root / "live.txt"
    live.write_text("one\n", encoding="utf-8")
    created = await session.poll_once()
    assert created is not None
    assert created.cursor == 1
    assert [(change.kind, change.path) for change in created.changes] == [
        (ObservationChangeKind.CREATE, "live.txt")
    ]

    live.write_text("two-with-new-size\n", encoding="utf-8")
    updated = await session.poll_once()
    assert updated is not None
    assert updated.cursor == 2
    assert [(change.kind, change.path) for change in updated.changes] == [
        (ObservationChangeKind.UPDATE, "live.txt")
    ]

    live.unlink()
    deleted = await session.poll_once()
    assert deleted is not None
    assert deleted.cursor == 3
    assert [(change.kind, change.path) for change in deleted.changes] == [
        (ObservationChangeKind.DELETE, "live.txt")
    ]
    replay = await session.replay(after_cursor=0, epoch=session.epoch)
    assert [batch.cursor for batch in replay.batches] == [1, 2, 3]

    await session.stop()
    assert first_process.poll() is not None
    assert provider.mode is None
    assert provider.last_backend_observation is None
    await session.stop()

    restarted = await session.start(background=False)
    assert session.epoch != first_epoch
    assert [entry.path for entry in restarted.entries] == ["source.txt"]
    assert len(created_backends) == 2
    assert created_backends[1].service.process_id != first_process.pid
    await session.stop()
    assert created_backends[1].service._process.poll() is not None
