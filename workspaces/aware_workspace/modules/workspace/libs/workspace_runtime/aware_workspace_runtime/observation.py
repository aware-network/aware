from __future__ import annotations

import asyncio
import inspect
import logging
import threading
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import cast
from uuid import UUID, uuid4

from .contracts import (
    ObservationChangeKind,
    ObservationRuntimeState,
    RepositoryPathQuery,
    RepositoryProviderObservation,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationBatch,
    WorkspaceRepositoryObservationCheckpoint,
    WorkspaceRepositoryObservationHealth,
    WorkspaceRepositoryObservationReplay,
    WorkspaceRepositoryObservationSnapshot,
    WorkspaceRepositoryQuerySnapshot,
    repository_snapshot_digest,
)
from .journal import WorkspaceRepositoryObservationJournal
from .lease import (
    FileWorkspaceRepositoryObservationLease,
    WorkspaceRepositoryObservationLease,
)
from .provider import WorkspaceRepositoryObservationProvider

logger = logging.getLogger(__name__)

WORKSPACE_BACKGROUND_POLL_POLICY = "cost_governed_v1"
DEFAULT_MAX_BACKGROUND_POLL_DUTY_CYCLE = 0.10
MAX_EXACT_OBSERVATION_PATHS = 512


def _actor_ref_is_canonical(value: str) -> bool:
    if ":" in value:
        return True
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class WorkspaceRepositorySerializedEffect[EffectValue]:
    value: EffectValue
    poll_after: bool
    observation_paths: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.observation_paths is not None:
            if not self.poll_after:
                raise ValueError("Serialized effect paths require convergence polling")
            object.__setattr__(
                self,
                "observation_paths",
                _exact_observation_paths(self.observation_paths),
            )


@dataclass(frozen=True, slots=True)
class WorkspaceRepositorySerializedTransition[EffectValue]:
    before: WorkspaceRepositoryObservationSnapshot
    effect: EffectValue
    batch: WorkspaceRepositoryObservationBatch | None
    after: WorkspaceRepositoryObservationSnapshot


class WorkspaceObservationError(RuntimeError):
    pass


class WorkspaceObservationNotStartedError(WorkspaceObservationError):
    pass


class WorkspaceObservationProviderInvariantError(WorkspaceObservationError):
    pass


class WorkspaceObservationCheckpointError(WorkspaceObservationError):
    pass


class WorkspaceObservationRegistryConflict(WorkspaceObservationError):
    pass


class WorkspaceRepositoryObservationSession:
    """Single-writer, many-reader maintained repository observation session."""

    def __init__(
        self,
        *,
        binding: WorkspaceRepositoryBinding,
        provider: WorkspaceRepositoryObservationProvider,
        poll_interval: float = 1.0,
        max_background_poll_duty_cycle: float = (
            DEFAULT_MAX_BACKGROUND_POLL_DUTY_CYCLE
        ),
        journal_capacity: int = 256,
        lease: WorkspaceRepositoryObservationLease | None = None,
    ) -> None:
        if provider.root_path.resolve() != binding.root_path:
            raise ValueError(
                "Observation provider root does not match repository binding"
            )
        if poll_interval <= 0:
            raise ValueError("Observation poll interval must be positive")
        if not 0 < max_background_poll_duty_cycle <= 1:
            raise ValueError("Maximum background poll duty cycle must be within (0, 1]")
        if journal_capacity <= 0:
            raise ValueError("Observation journal capacity must be positive")
        self.binding = binding
        self.provider = provider
        self.poll_interval = poll_interval
        self.max_background_poll_duty_cycle = max_background_poll_duty_cycle
        self.journal_capacity = journal_capacity
        self._lease = lease or FileWorkspaceRepositoryObservationLease(binding=binding)
        self._epoch = uuid4().hex
        self._workspace_session_lock = threading.RLock()
        self._workspace_sessions: dict[tuple[str, str], str] = {}
        self._state = ObservationRuntimeState.NEW
        self._snapshot: WorkspaceRepositoryObservationSnapshot | None = None
        self._journal: WorkspaceRepositoryObservationJournal | None = None
        self._baseline_observed_at: datetime | None = None
        self._checkpoints: dict[str, WorkspaceRepositoryObservationCheckpoint] = {}
        self._writer_lock = asyncio.Lock()
        self._lifecycle_lock = asyncio.Lock()
        self._published = asyncio.Condition()
        self._watch_task: asyncio.Task[None] | None = None
        self._next_background_poll_delay = poll_interval
        self._consecutive_failures = 0
        self._last_error: str | None = None
        self._last_observed_at: datetime | None = None
        self._authority_admitted = False
        self._query_cursor = 0
        self._query_snapshots: dict[str, WorkspaceRepositoryQuerySnapshot] = {}

    @property
    def epoch(self) -> str:
        return self._epoch

    def observe_workspace_session(self, *, execution_id: str, actor_ref: str) -> str:
        """Return Workspace-owned participant authority for this runtime session."""

        if (
            not execution_id
            or execution_id != execution_id.strip()
            or not actor_ref
            or actor_ref != actor_ref.strip()
            or not _actor_ref_is_canonical(actor_ref)
        ):
            raise ValueError("workspace_session_participant_invalid")
        key = (execution_id, actor_ref)
        with self._workspace_session_lock:
            if not self._authority_admitted or self._state not in {
                ObservationRuntimeState.RUNNING,
                ObservationRuntimeState.DEGRADED,
            }:
                raise WorkspaceObservationNotStartedError(
                    "Workspace session authority is not admitted"
                )
            retained = self._workspace_sessions.get(key)
            if retained is None:
                retained = f"workspace-session:{self._epoch}:{uuid4().hex}"
                self._workspace_sessions[key] = retained
            return retained

    def require_workspace_session_current(
        self,
        *,
        workspace_session_ref: str,
        execution_id: str,
        actor_ref: str,
    ) -> None:
        """Reject authority retained across a Workspace epoch replacement."""

        with self._workspace_session_lock:
            if (
                not self._authority_admitted
                or self._state
                not in {ObservationRuntimeState.RUNNING, ObservationRuntimeState.DEGRADED}
                or self._workspace_sessions.get((execution_id, actor_ref))
                != workspace_session_ref
            ):
                raise WorkspaceObservationNotStartedError(
                    "Workspace session authority is stale"
                )

    @property
    def current_snapshot(self) -> WorkspaceRepositoryObservationSnapshot:
        return self._require_snapshot()

    @property
    def observation_initialized(self) -> bool:
        return self._snapshot is not None and self._journal is not None

    @property
    def baseline_observed_at(self) -> datetime | None:
        """Return the cursor-0 completion fence for external evidence admission."""

        return self._baseline_observed_at

    @property
    def authority_admitted(self) -> bool:
        return self._authority_admitted

    @property
    def query_cursor(self) -> int:
        return self._query_cursor

    @property
    def health(self) -> WorkspaceRepositoryObservationHealth:
        snapshot = self._snapshot
        journal = self._journal
        return WorkspaceRepositoryObservationHealth(
            state=self._state,
            epoch=self._epoch,
            cursor=snapshot.cursor if snapshot is not None else 0,
            files_tracked=len(snapshot.entries) if snapshot is not None else 0,
            journal_size=len(journal) if journal is not None else 0,
            consecutive_failures=self._consecutive_failures,
            last_error=self._last_error,
            last_observed_at=self._last_observed_at,
        )

    @property
    def configuration_signature(self) -> tuple[str, str, str, float, float, int]:
        return (
            cast(str, self.binding.binding_key),
            str(self.binding.root_path),
            self.binding.filter_version,
            self.poll_interval,
            self.max_background_poll_duty_cycle,
            self.journal_capacity,
        )

    @property
    def next_background_poll_delay(self) -> float:
        return self._next_background_poll_delay

    async def start(
        self, *, background: bool = True
    ) -> WorkspaceRepositoryObservationSnapshot:
        async with self._lifecycle_lock:
            if self._snapshot is not None and (
                self._state is ObservationRuntimeState.RUNNING
                or (self._state is ObservationRuntimeState.DEGRADED)
            ):
                return self._require_snapshot()
            if self._state is ObservationRuntimeState.STOPPED:
                self._reset_authority_locked()
            acquired_here = False
            if not self._authority_admitted:
                try:
                    self._lease.acquire()
                    self._authority_admitted = True
                    acquired_here = True
                except Exception as exc:
                    self._record_failure(exc)
                    raise
            self._state = ObservationRuntimeState.STARTING
            try:
                observation = await self.provider.initialize()
                binding_key = cast(str, self.binding.binding_key)
                baseline_entries = observation.baseline_entries
                baseline_digest = (
                    observation.snapshot_digest
                    if baseline_entries is None
                    else repository_snapshot_digest(baseline_entries)
                )
                self._journal = WorkspaceRepositoryObservationJournal(
                    epoch=self._epoch,
                    binding_key=binding_key,
                    initial_snapshot_digest=baseline_digest,
                    capacity=self.journal_capacity,
                )
                cursor = 0
                if baseline_entries is not None and observation.changes:
                    baseline = WorkspaceRepositoryObservationSnapshot(
                        binding_key=binding_key,
                        epoch=self._epoch,
                        cursor=0,
                        observed_at=cast(datetime, observation.baseline_observed_at),
                        snapshot_digest=baseline_digest,
                        entries=baseline_entries,
                    )
                    _validate_provider_transition(baseline, observation)
                    batch = WorkspaceRepositoryObservationBatch(
                        binding_key=binding_key,
                        epoch=self._epoch,
                        cursor=1,
                        observed_at=observation.observed_at,
                        before_snapshot_digest=baseline_digest,
                        after_snapshot_digest=observation.snapshot_digest,
                        changes=observation.changes,
                    )
                    self._journal.append(batch)
                    cursor = 1
                elif baseline_entries is not None and (
                    baseline_digest != observation.snapshot_digest
                ):
                    raise WorkspaceObservationProviderInvariantError(
                        "Provider initialization snapshot changed without a delta"
                    )
                snapshot = WorkspaceRepositoryObservationSnapshot(
                    binding_key=binding_key,
                    epoch=self._epoch,
                    cursor=cursor,
                    observed_at=observation.observed_at,
                    snapshot_digest=observation.snapshot_digest,
                    entries=observation.entries,
                )
                self._snapshot = snapshot
                self._baseline_observed_at = (
                    observation.observed_at
                    if observation.baseline_observed_at is None
                    else observation.baseline_observed_at
                )
                self._state = ObservationRuntimeState.RUNNING
                self._consecutive_failures = 0
                self._last_error = None
                self._last_observed_at = observation.observed_at
                self._next_background_poll_delay = self.poll_interval
                if background:
                    self._watch_task = asyncio.create_task(self._watch_loop())
                return snapshot
            except Exception as exc:
                if acquired_here:
                    self._lease.release()
                    self._authority_admitted = False
                self._record_failure(exc)
                raise

    async def admit(self) -> None:
        """Admit the one authority without scanning the repository."""

        async with self._lifecycle_lock:
            if self._state is ObservationRuntimeState.STOPPED:
                self._reset_authority_locked()
            if not self._authority_admitted:
                try:
                    self._lease.acquire()
                    self._authority_admitted = True
                except Exception as exc:
                    self._record_failure(exc)
                    raise
            if self._snapshot is None:
                self._state = ObservationRuntimeState.RUNNING

    async def query(
        self, request: RepositoryPathQuery
    ) -> WorkspaceRepositoryQuerySnapshot:
        """Observe a bounded projection through this session's single authority."""

        await self.admit()
        async with self._writer_lock:
            previous = self._query_snapshots.get(request.query_ref)
            if previous is not None and previous.query_digest != request.query_digest:
                raise WorkspaceObservationProviderInvariantError(
                    "Repository query ref cannot change its query contract"
                )
            query_method = getattr(self.provider, "query", None)
            if query_method is None:
                raise WorkspaceObservationProviderInvariantError(
                    "Repository observation provider does not support bounded query"
                )
            observation = await query_method(request)
            if observation.query_digest != request.query_digest:
                raise WorkspaceObservationProviderInvariantError(
                    "Provider query digest does not match the requested query"
                )
            changed_paths = _changed_query_paths(previous, observation.entries)
            if previous is not None and changed_paths:
                self._query_cursor += 1
            snapshot = WorkspaceRepositoryQuerySnapshot(
                binding_key=cast(str, self.binding.binding_key),
                epoch=self._epoch,
                cursor=self._query_cursor
                if previous is None
                else (self._query_cursor if changed_paths else previous.cursor),
                query_ref=request.query_ref,
                query_digest=request.query_digest,
                observed_at=observation.observed_at,
                snapshot_digest=observation.snapshot_digest,
                entries=observation.entries,
                examined_count=observation.examined_count,
                truncated=observation.truncated,
                inaccessible_count=observation.inaccessible_count,
                changed_paths=changed_paths,
            )
            self._query_snapshots[request.query_ref] = snapshot
            self._record_success(observation.observed_at)
            return snapshot

    def query_snapshot(self, query_ref: str) -> WorkspaceRepositoryQuerySnapshot:
        try:
            return self._query_snapshots[query_ref]
        except KeyError as error:
            raise WorkspaceObservationNotStartedError(
                f"Repository query snapshot is unavailable: {query_ref}"
            ) from error

    async def stop(self) -> None:
        async with self._lifecycle_lock:
            if self._state is ObservationRuntimeState.STOPPED:
                return
            task = self._watch_task
            self._watch_task = None
            self._state = ObservationRuntimeState.STOPPED
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            try:
                await _close_provider(self.provider)
            finally:
                if self._authority_admitted:
                    self._lease.release()
                    self._authority_admitted = False
                async with self._published:
                    self._published.notify_all()

    async def poll_once(self) -> WorkspaceRepositoryObservationBatch | None:
        self._ensure_started()
        async with self._writer_lock:
            batch = await self._poll_once_locked()

        if batch is not None:
            await self._notify_published()
        return batch

    async def observe_paths_once(
        self, paths: tuple[str, ...]
    ) -> WorkspaceRepositoryObservationBatch | None:
        """Advance the canonical journal from bounded exact path metadata."""

        selected_paths = _exact_observation_paths(paths)
        self._ensure_started()
        async with self._writer_lock:
            batch = await self._poll_once_locked(selected_paths=selected_paths)
        if batch is not None:
            await self._notify_published()
        return batch

    async def run_serialized_transition[EffectValue](
        self,
        effect: Callable[
            [WorkspaceRepositoryObservationSnapshot],
            WorkspaceRepositorySerializedEffect[EffectValue]
            | Awaitable[WorkspaceRepositorySerializedEffect[EffectValue]],
        ],
    ) -> WorkspaceRepositorySerializedTransition[EffectValue]:
        """Serialize one admitted effect and its convergence poll.

        The effect receives the exact current snapshot while the observer
        writer lock is held. It may decline polling when admission failed
        before any filesystem effect. This is not a general transaction or a
        repository mutation API; Workspace mutation admission owns that layer.
        """

        self._ensure_started()
        async with self._writer_lock:
            before = self._require_snapshot()
            candidate = effect(before)
            resolved = await candidate if inspect.isawaitable(candidate) else candidate
            if not isinstance(resolved, WorkspaceRepositorySerializedEffect):
                raise TypeError("Serialized transition effect returned invalid value")
            batch = (
                await self._poll_once_locked(
                    selected_paths=resolved.observation_paths,
                )
                if resolved.poll_after
                else None
            )
            after = self._require_snapshot()
        if batch is not None:
            await self._notify_published()
        return WorkspaceRepositorySerializedTransition(
            before=before,
            effect=resolved.value,
            batch=batch,
            after=after,
        )

    async def _poll_once_locked(
        self,
        *,
        selected_paths: tuple[str, ...] | None = None,
    ) -> WorkspaceRepositoryObservationBatch | None:
        before = self._require_snapshot()
        try:
            if selected_paths is None:
                observation = await self.provider.poll()
            else:
                observe_paths = getattr(self.provider, "observe_paths", None)
                observation = (
                    await observe_paths(selected_paths)
                    if observe_paths is not None
                    else await self.provider.poll()
                )
            if not observation.changes:
                if observation.snapshot_digest != before.snapshot_digest:
                    raise WorkspaceObservationProviderInvariantError(
                        "Provider snapshot changed without an explicit delta"
                    )
                self._snapshot = WorkspaceRepositoryObservationSnapshot(
                    binding_key=before.binding_key,
                    epoch=before.epoch,
                    cursor=before.cursor,
                    observed_at=observation.observed_at,
                    snapshot_digest=before.snapshot_digest,
                    entries=before.entries,
                )
                self._record_success(observation.observed_at)
                return None

            _validate_provider_transition(before, observation)
            batch = WorkspaceRepositoryObservationBatch(
                binding_key=before.binding_key,
                epoch=before.epoch,
                cursor=before.cursor + 1,
                observed_at=observation.observed_at,
                before_snapshot_digest=before.snapshot_digest,
                after_snapshot_digest=observation.snapshot_digest,
                changes=observation.changes,
            )
            snapshot = WorkspaceRepositoryObservationSnapshot(
                binding_key=before.binding_key,
                epoch=before.epoch,
                cursor=batch.cursor,
                observed_at=observation.observed_at,
                snapshot_digest=observation.snapshot_digest,
                entries=observation.entries,
            )
            self._require_journal().append(batch)
            self._snapshot = snapshot
            self._record_success(observation.observed_at)
            return batch
        except Exception as exc:
            self._record_failure(exc)
            raise

    async def _notify_published(self) -> None:
        async with self._published:
            self._published.notify_all()

    async def replay(
        self,
        *,
        after_cursor: int,
        epoch: str | None = None,
        wait_timeout: float | None = None,
    ) -> WorkspaceRepositoryObservationReplay:
        self._ensure_started()
        replay = self._replay_now(after_cursor=after_cursor, epoch=epoch)
        if replay.gap is not None or replay.batches or not wait_timeout:
            return replay
        if wait_timeout < 0:
            raise ValueError("Replay wait timeout must be non-negative")
        observed_cursor = replay.current_cursor
        async with self._published:
            try:
                await asyncio.wait_for(
                    self._published.wait_for(
                        lambda: (
                            self._state is ObservationRuntimeState.STOPPED
                            or self._require_snapshot().cursor > observed_cursor
                        )
                    ),
                    timeout=wait_timeout,
                )
            except TimeoutError:
                pass
        return self._replay_now(after_cursor=after_cursor, epoch=epoch)

    def acknowledge(
        self,
        *,
        consumer_key: str,
        epoch: str,
        cursor: int,
        projection_digest: str | None = None,
    ) -> WorkspaceRepositoryObservationCheckpoint:
        snapshot = self._require_snapshot()
        if epoch != snapshot.epoch:
            raise WorkspaceObservationCheckpointError(
                "Checkpoint epoch does not match observation epoch"
            )
        if cursor < 0 or cursor > snapshot.cursor:
            raise WorkspaceObservationCheckpointError(
                "Checkpoint cursor is outside the published range"
            )
        previous = self._checkpoints.get(consumer_key.strip())
        if previous is not None and cursor < previous.cursor:
            raise WorkspaceObservationCheckpointError(
                "Checkpoint cursor cannot move backwards"
            )
        checkpoint = WorkspaceRepositoryObservationCheckpoint(
            consumer_key=consumer_key,
            epoch=epoch,
            cursor=cursor,
            accepted_at=datetime.now(UTC),
            projection_digest=projection_digest,
        )
        self._checkpoints[checkpoint.consumer_key] = checkpoint
        return checkpoint

    def checkpoint_for(
        self, consumer_key: str
    ) -> WorkspaceRepositoryObservationCheckpoint | None:
        return self._checkpoints.get(consumer_key.strip())

    async def _watch_loop(self) -> None:
        loop = asyncio.get_running_loop()
        while self._state in {
            ObservationRuntimeState.RUNNING,
            ObservationRuntimeState.DEGRADED,
        }:
            started: float | None = None
            try:
                await asyncio.sleep(self._next_background_poll_delay)
                if self._state is ObservationRuntimeState.STOPPED:
                    return
                started = loop.time()
                await self.poll_once()
            except asyncio.CancelledError:
                return
            except Exception as exc:
                # Health carries the failure. The maintained loop retries on the
                # next interval and never fabricates an empty published batch.
                logger.warning(
                    "Workspace repository observation poll failed; retrying",
                    exc_info=exc,
                )
            finally:
                if started is not None:
                    poll_duration = max(0.0, loop.time() - started)
                    self._next_background_poll_delay = _background_poll_delay(
                        minimum_interval=self.poll_interval,
                        maximum_duty_cycle=self.max_background_poll_duty_cycle,
                        poll_duration=poll_duration,
                    )

    def _replay_now(
        self, *, after_cursor: int, epoch: str | None
    ) -> WorkspaceRepositoryObservationReplay:
        return self._require_journal().replay(
            requested_epoch=epoch,
            after_cursor=after_cursor,
            snapshot=self._require_snapshot(),
        )

    def _ensure_started(self) -> None:
        if self._state not in {
            ObservationRuntimeState.RUNNING,
            ObservationRuntimeState.DEGRADED,
        }:
            raise WorkspaceObservationNotStartedError(
                "Workspace repository observation session is not running"
            )

    def _require_snapshot(self) -> WorkspaceRepositoryObservationSnapshot:
        if self._snapshot is None:
            raise WorkspaceObservationNotStartedError(
                "Workspace repository observation snapshot is unavailable"
            )
        return self._snapshot

    def _require_journal(self) -> WorkspaceRepositoryObservationJournal:
        if self._journal is None:
            raise WorkspaceObservationNotStartedError(
                "Workspace repository observation journal is unavailable"
            )
        return self._journal

    def _record_success(self, observed_at: datetime) -> None:
        self._state = ObservationRuntimeState.RUNNING
        self._consecutive_failures = 0
        self._last_error = None
        self._last_observed_at = observed_at

    def _record_failure(self, exc: Exception) -> None:
        self._state = ObservationRuntimeState.DEGRADED
        self._consecutive_failures += 1
        self._last_error = f"{type(exc).__name__}: {exc}"

    def _reset_authority_locked(self) -> None:
        self._epoch = uuid4().hex
        with self._workspace_session_lock:
            self._workspace_sessions.clear()
        self._checkpoints.clear()
        self._snapshot = None
        self._journal = None
        self._baseline_observed_at = None
        self._query_cursor = 0
        self._query_snapshots.clear()
        self._state = ObservationRuntimeState.NEW


def _changed_query_paths(
    previous: WorkspaceRepositoryQuerySnapshot | None,
    entries: tuple[RepositorySnapshotEntry, ...],
) -> tuple[str, ...]:
    if previous is None:
        return ()
    before = {entry.path: entry for entry in previous.entries}
    after = {entry.path: entry for entry in entries}
    return tuple(
        sorted(
            path
            for path in before.keys() | after.keys()
            if before.get(path) != after.get(path)
        )
    )


def _exact_observation_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    if not paths:
        raise ValueError("Exact repository observation requires at least one path")
    if len(paths) > MAX_EXACT_OBSERVATION_PATHS:
        raise ValueError("Exact repository observation path count exceeds policy")
    normalized: list[str] = []
    for value in paths:
        candidate = value.strip().replace("\\", "/")
        path = PurePosixPath(candidate)
        if (
            not candidate
            or path.is_absolute()
            or ".." in path.parts
            or "." in path.parts
        ):
            raise ValueError(
                f"Exact repository observation path is not confined: {value!r}"
            )
        normalized.append(path.as_posix())
    if len(normalized) != len(set(normalized)):
        raise ValueError("Exact repository observation paths must be unique")
    return tuple(sorted(normalized))


def _background_poll_delay(
    *,
    minimum_interval: float,
    maximum_duty_cycle: float,
    poll_duration: float,
) -> float:
    required_idle = poll_duration * ((1.0 - maximum_duty_cycle) / maximum_duty_cycle)
    return max(minimum_interval, required_idle)


class WorkspaceRepositoryObservationRegistry:
    """Process-local singleton registry for maintained repository sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, WorkspaceRepositoryObservationSession] = {}
        self._lock = asyncio.Lock()

    async def acquire(
        self,
        *,
        binding: WorkspaceRepositoryBinding,
        provider_factory: Callable[[], WorkspaceRepositoryObservationProvider],
        poll_interval: float = 1.0,
        max_background_poll_duty_cycle: float = (
            DEFAULT_MAX_BACKGROUND_POLL_DUTY_CYCLE
        ),
        journal_capacity: int = 256,
    ) -> WorkspaceRepositoryObservationSession:
        binding_key = cast(str, binding.binding_key)
        signature = (
            binding_key,
            str(binding.root_path),
            binding.filter_version,
            poll_interval,
            max_background_poll_duty_cycle,
            journal_capacity,
        )
        async with self._lock:
            existing = self._sessions.get(binding_key)
            if existing is not None:
                if existing.configuration_signature != signature:
                    raise WorkspaceObservationRegistryConflict(
                        "Repository binding already has an incompatible maintained session"
                    )
                return existing
            session = WorkspaceRepositoryObservationSession(
                binding=binding,
                provider=provider_factory(),
                poll_interval=poll_interval,
                max_background_poll_duty_cycle=max_background_poll_duty_cycle,
                journal_capacity=journal_capacity,
            )
            self._sessions[binding_key] = session
            return session

    async def release(self, *, binding_key: str, stop: bool = True) -> None:
        async with self._lock:
            session = self._sessions.pop(binding_key, None)
        if stop and session is not None:
            await session.stop()


def _validate_provider_transition(
    before: WorkspaceRepositoryObservationSnapshot,
    observation: RepositoryProviderObservation,
) -> None:
    projected: dict[str, RepositorySnapshotEntry] = {
        entry.path: entry for entry in before.entries
    }
    for change in observation.changes:
        if change.kind is ObservationChangeKind.CREATE:
            if change.path in projected:
                raise WorkspaceObservationProviderInvariantError(
                    f"Provider create already exists: {change.path}"
                )
            projected[change.path] = cast(RepositorySnapshotEntry, change.entry)
        elif change.kind is ObservationChangeKind.UPDATE:
            if change.path not in projected:
                raise WorkspaceObservationProviderInvariantError(
                    f"Provider update does not exist: {change.path}"
                )
            projected[change.path] = cast(RepositorySnapshotEntry, change.entry)
        else:
            if change.path not in projected:
                raise WorkspaceObservationProviderInvariantError(
                    f"Provider delete does not exist: {change.path}"
                )
            del projected[change.path]
    expected = tuple(sorted(projected.values(), key=lambda item: item.path))
    if expected != observation.entries:
        raise WorkspaceObservationProviderInvariantError(
            "Provider delta does not reproduce its advertised snapshot"
        )


async def _close_provider(provider: WorkspaceRepositoryObservationProvider) -> None:
    close = getattr(provider, "close", None)
    if close is None:
        return
    result = close()
    if inspect.isawaitable(result):
        await result
