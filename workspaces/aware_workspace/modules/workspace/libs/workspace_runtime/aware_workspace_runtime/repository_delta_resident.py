from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum

from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionClient,
)

from .change_evidence import WorkspaceRepositoryChangeEvidence
from .observation import WorkspaceRepositoryObservationSession
from .repository_delta import (
    WorkspaceRepositoryDeltaCapture,
    WorkspaceRepositoryDeltaCapturePolicy,
    repository_delta_selection_shards,
)
from .repository_delta_capture import (
    WorkspaceRepositoryDeltaCaptureCoordinator,
    WorkspaceRepositoryDeltaCaptureMetrics,
)
from .repository_delta_resolution import (
    WorkspaceRepositoryContentDeltaResolution,
    WorkspaceRepositoryContentDeltaResolver,
)
from .repository_delta_store_contract import WorkspaceRepositoryDeltaStoreSnapshot

WORKSPACE_REPOSITORY_DELTA_RESIDENT_CONTRACT_REF = (
    "aware.workspace.repository-delta-resident.v1"
)


class RepositoryDeltaResidentState(StrEnum):
    IDLE = "idle"
    FOLLOWING = "following"
    DEGRADED = "degraded"
    STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaResidentSnapshot:
    repository_binding_ref: str
    state: RepositoryDeltaResidentState
    epoch: str | None
    observed_cursor: int | None
    last_error: str | None
    store: WorkspaceRepositoryDeltaStoreSnapshot
    capture: WorkspaceRepositoryDeltaCaptureMetrics


class WorkspaceRepositoryDeltaResident:
    """One bounded delta-capture consumer over a maintained observer journal.

    This resident never scans the repository. Explicit preparation reads only
    the selected preimages, and the follower consumes already-published
    Workspace observation batches off the publisher's path.
    """

    def __init__(
        self,
        *,
        session: WorkspaceRepositoryObservationSession,
        store: WorkspaceRepositoryDeltaRetentionClient,
        replay_wait_timeout: float = 0.5,
    ) -> None:
        binding_ref = session.binding.binding_key
        if type(store) is not WorkspaceRepositoryDeltaRetentionClient:
            raise TypeError("original Workspace retention client required")
        store.verify_repository_binding(expected_binding_ref=binding_ref)
        if replay_wait_timeout <= 0:
            raise ValueError("Delta resident replay wait timeout must be positive")
        self._session = session
        self._store = store
        self._coordinator = WorkspaceRepositoryDeltaCaptureCoordinator(
            binding=session.binding,
            store=store,
        )
        self._resolver = WorkspaceRepositoryContentDeltaResolver(store=store)
        self._replay_wait_timeout = replay_wait_timeout
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._epoch: str | None = None
        self._observed_cursor: int | None = None
        self._last_error: str | None = None
        self._stopped = False

    @property
    def session(self) -> WorkspaceRepositoryObservationSession:
        return self._session

    @property
    def store(self) -> WorkspaceRepositoryDeltaRetentionClient:
        return self._store

    @property
    def coordinator(self) -> WorkspaceRepositoryDeltaCaptureCoordinator:
        return self._coordinator

    def resolve_evidence(
        self,
        evidence: WorkspaceRepositoryChangeEvidence,
        *,
        context_refs: tuple[str, ...],
    ) -> WorkspaceRepositoryContentDeltaResolution:
        snapshot = self.snapshot()
        return self._resolver.resolve(
            evidence,
            context_refs=context_refs,
            observed_epoch=snapshot.epoch,
            observed_cursor=snapshot.observed_cursor,
            resident_error=snapshot.last_error,
        )

    def snapshot(self) -> WorkspaceRepositoryDeltaResidentSnapshot:
        task = self._task
        state = (
            RepositoryDeltaResidentState.STOPPED
            if self._stopped
            else (
                RepositoryDeltaResidentState.DEGRADED
                if self._last_error is not None
                else (
                    RepositoryDeltaResidentState.FOLLOWING
                    if task is not None and not task.done()
                    else RepositoryDeltaResidentState.IDLE
                )
            )
        )
        return WorkspaceRepositoryDeltaResidentSnapshot(
            repository_binding_ref=self._store.repository_binding_ref,
            state=state,
            epoch=self._epoch,
            observed_cursor=self._observed_cursor,
            last_error=self._last_error,
            store=self._store.snapshot(),
            capture=self._coordinator.metrics(),
        )

    async def prepare(
        self,
        *,
        selected_paths: tuple[str, ...],
        context_refs: tuple[str, ...] = (),
        policy: WorkspaceRepositoryDeltaCapturePolicy | None = None,
    ) -> WorkspaceRepositoryDeltaCapture:
        captures = await self.prepare_batch(
            selected_paths=selected_paths,
            context_refs=context_refs,
            policy=policy,
        )
        if len(captures) != 1:
            raise ValueError("Single delta preparation exceeds capture policy")
        return captures[0]

    async def prepare_batch(
        self,
        *,
        selected_paths: tuple[str, ...],
        context_refs: tuple[str, ...] = (),
        policy: WorkspaceRepositoryDeltaCapturePolicy | None = None,
    ) -> tuple[WorkspaceRepositoryDeltaCapture, ...]:
        if self._stopped:
            raise RuntimeError("Delta resident is stopped")
        selected_policy = policy or WorkspaceRepositoryDeltaCapturePolicy()
        shards = repository_delta_selection_shards(
            selected_paths,
            policy=selected_policy,
        )
        snapshot = await self._session.start(background=False)
        captures = tuple(
            [
                await self._coordinator.prepare_async(
                    snapshot=snapshot,
                    selected_paths=shard,
                    policy=selected_policy,
                    context_refs=context_refs,
                )
                for shard in shards
            ]
        )
        async with self._lock:
            if self._stopped:
                raise RuntimeError("Delta resident is stopped")
            if self._epoch is None:
                self._epoch = snapshot.epoch
                self._observed_cursor = snapshot.cursor
            elif self._epoch != snapshot.epoch:
                self._last_error = "workspace_repository_delta_epoch_changed"
                raise RuntimeError(self._last_error)
            self._ensure_follower_locked()
        return captures

    async def stop(self) -> None:
        async with self._lock:
            self._stopped = True
            task = self._task
            self._task = None
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def _ensure_follower_locked(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(
                self._follow(),
                name="workspace-repository-delta-resident",
            )

    async def _follow(self) -> None:
        try:
            while not self._stopped:
                epoch = self._epoch
                after_cursor = self._observed_cursor
                if epoch is None or after_cursor is None:
                    return
                replay = await self._session.replay(
                    after_cursor=after_cursor,
                    epoch=epoch,
                    wait_timeout=self._replay_wait_timeout,
                )
                if replay.gap is not None:
                    self._last_error = (
                        "workspace_repository_delta_observation_gap:"
                        f"{replay.gap.reason.value}"
                    )
                    return
                for batch in replay.batches:
                    await self._coordinator.observe_async(batch)
                    self._observed_cursor = batch.cursor
        except asyncio.CancelledError:
            raise
        except Exception as error:  # noqa: BLE001 - snapshot carries exact failure
            self._last_error = f"{type(error).__name__}: {error}"
