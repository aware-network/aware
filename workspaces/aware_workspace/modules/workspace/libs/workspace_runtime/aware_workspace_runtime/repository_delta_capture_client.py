"""Command-local orchestration of the one original observer/capture/retention."""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

from aware_workspace_sdk.repository_delta_capture import (
    WorkspaceRepositoryDeltaCaptureObservation,
    WorkspaceRepositoryDeltaCaptureRefusal,
)
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionClient,
)

from .repository_delta import (
    RepositoryDeltaCapturePathState,
    WorkspaceRepositoryDeltaCapturePolicy,
)
from .repository_delta_capture import WorkspaceRepositoryDeltaCaptureCoordinator


async def _settled(awaitable):
    """Settle original work before returning cancellation and releasing locks."""

    async def guarded():
        try:
            return await awaitable, None
        except BaseException as error:  # noqa: BLE001 - retain original interruption
            return None, error

    task = asyncio.create_task(guarded())
    interrupted = None
    while True:
        try:
            value, failure = await asyncio.shield(task)
            break
        except asyncio.CancelledError as error:
            interrupted = interrupted or error
            if task.cancelled():
                # Cancellation before the guarded task starts cannot settle by
                # shielding an already-cancelled task indefinitely.
                raise
    if failure is not None:
        raise failure
    if interrupted is not None:
        raise interrupted
    return value


class WorkspaceRepositoryDeltaCaptureRuntime:
    def __init__(self, *, physical, retention):
        from aware_workspace_fs_adapter.repository_delta_capture import (
            FilesystemDeltaCapturePort,
        )

        if type(physical) is not FilesystemDeltaCapturePort:
            raise WorkspaceRepositoryDeltaCaptureRefusal(
                "capture_original_port_required"
            )
        if type(retention) is not WorkspaceRepositoryDeltaRetentionClient:
            raise WorkspaceRepositoryDeltaCaptureRefusal(
                "capture_original_retention_required"
            )
        physical.verify_current()
        self.binding_ref = physical.binding.binding_key
        selected_retention = retention.observe_retention()
        if selected_retention.phase == "active":
            retention.verify_repository_binding(expected_binding_ref=self.binding_ref)
            retention.verify_capture_separation(
                repository_root=physical.binding.root_path,
                cache_root=physical.cache_root,
            )
        elif selected_retention.phase != "allocated":
            raise WorkspaceRepositoryDeltaCaptureRefusal(
                "capture_retention_not_available"
            )
        self._physical = physical
        self._retention = retention
        self._pid = os.getpid()
        self._ref = "workspace-capture:" + uuid4().hex
        self._phase = "selected"
        self._session = None
        self._coordinator = None
        self._capture = None
        self._snapshot = None
        self._deltas = ()
        self._complete = True
        self._cleanup = "not_attempted"
        self._diagnostics = ()
        self._lock = asyncio.Lock()

    def check_process(self):
        if self._pid != os.getpid():
            raise WorkspaceRepositoryDeltaCaptureRefusal("capture_process_mismatch")

    def observation(self):
        self.check_process()
        return WorkspaceRepositoryDeltaCaptureObservation(
            self._ref,
            self.binding_ref,
            self._phase,
            self._capture,
            self._snapshot,
            self._deltas,
            self._complete,
            self._cleanup,
            self._diagnostics,
        )

    def _refuse(self, code, error=None):
        refusal = WorkspaceRepositoryDeltaCaptureRefusal(
            code, observation=self.observation()
        )
        if error is not None:
            raise refusal from error
        raise refusal

    def _current(self):
        self.check_process()
        self._physical.verify_current()
        self._retention.verify_repository_binding(expected_binding_ref=self.binding_ref)
        self._retention.verify_capture_separation(
            repository_root=self._physical.binding.root_path,
            cache_root=self._physical.cache_root,
        )

    def _adopt_snapshot(self, candidate):
        known = self._snapshot
        if candidate.binding_key != self.binding_ref or (
            known is not None
            and (
                candidate.epoch != known.epoch
                or candidate.cursor < known.cursor
                or (
                    candidate.cursor == known.cursor
                    and candidate.snapshot_digest != known.snapshot_digest
                )
            )
        ):
            raise ValueError("capture_observation_history_regressed")
        self._snapshot = candidate

    def _retain_failure(self, error):
        self._phase = "failed"
        self._complete = False
        self._diagnostics += ("capture_failure:" + type(error).__name__,)
        # Owner records may have been persisted before their return failed.
        # Recapture never erases already-known deltas or snapshot evidence.
        try:
            if self._session is not None and self._session.observation_initialized:
                self._adopt_snapshot(self._session.current_snapshot)
            captures = self._retention.retained_captures()
            if self._capture is None and self._snapshot is not None:
                candidates = [c for c in captures if self._ref in c.context_refs]
                if len(candidates) == 1:
                    self._capture = candidates[0]
            if self._capture is not None:
                known = {d.delta_ref: d for d in self._deltas}
                known.update(
                    {
                        d.delta_ref: d
                        for d in self._retention.retained_deltas()
                        if d.capture_ref == self._capture.capture_ref
                    }
                )
                self._deltas = tuple(known.values())
        except BaseException as recapture_error:  # noqa: BLE001 - preserve prior evidence
            self._diagnostics += (
                "capture_recapture_unavailable:" + type(recapture_error).__name__,
            )

    async def prepare(self, *, selected_paths, policy, context_refs):
        async with self._lock:
            self.check_process()
            if self._phase != "selected":
                self._refuse("capture_preparation_spent")
            self._phase = "preparing"
            try:
                self._current()
                if type(selected_paths) is not tuple or not selected_paths:
                    raise ValueError("capture_exact_paths_required")
                if type(context_refs) is not tuple or self._ref in context_refs:
                    raise ValueError("capture_context_invalid")
                policy = (
                    policy
                    if policy is not None
                    else WorkspaceRepositoryDeltaCapturePolicy()
                )
                if type(policy) is not WorkspaceRepositoryDeltaCapturePolicy:
                    raise TypeError("capture_original_policy_required")
                if len(selected_paths) > policy.maximum_selected_files:
                    raise ValueError("capture_selection_over_budget")
                if len(set(selected_paths)) != len(selected_paths):
                    raise ValueError("capture_duplicate_paths")
                self._physical.verify_paths(selected_paths)
                self._session = self._physical.create_session()
                self._adopt_snapshot(
                    await _settled(self._session.start(background=False))
                )
                self._physical.verify_paths(selected_paths, session=self._session)
                await _settled(self._session.observe_paths_once(selected_paths))
                self._adopt_snapshot(self._session.current_snapshot)
                self._coordinator = WorkspaceRepositoryDeltaCaptureCoordinator(
                    binding=self._physical.binding,
                    store=self._retention,
                )
                self._capture = await _settled(
                    self._coordinator.prepare_async(
                        snapshot=self._snapshot,
                        selected_paths=selected_paths,
                        policy=policy,
                        context_refs=(*context_refs, self._ref),
                    )
                )
                self._current()
                if any(
                    s.state
                    not in (
                        RepositoryDeltaCapturePathState.COVERED,
                        RepositoryDeltaCapturePathState.ABSENT,
                    )
                    for s in self._capture.path_states
                ):
                    raise ValueError("capture_preimage_incomplete")
                self._phase = "prepared"
                return self.observation()
            except BaseException as error:  # noqa: BLE001 - preparation is irreversibly spent
                self._retain_failure(error)
                self._refuse(
                    getattr(error, "code", str(error) or "capture_preparation_failed"),
                    error,
                )

    async def poll(self):
        async with self._lock:
            self.check_process()
            if self._phase != "prepared":
                self._refuse("capture_not_prepared")
            try:
                self._current()
                paths = self._capture.selected_paths
                self._physical.verify_paths(paths, session=self._session)
                batch = await _settled(self._session.observe_paths_once(paths))
                self._adopt_snapshot(self._session.current_snapshot)
                deltas = await _settled(self._coordinator.observe_async(batch))
                self._deltas += tuple(
                    d
                    for d in deltas
                    if d.delta_ref not in {known.delta_ref for known in self._deltas}
                )
                self._current()
                return self.observation()
            except BaseException as error:  # noqa: BLE001 - retain partial canonical publication
                self._retain_failure(error)
                self._refuse(
                    getattr(error, "code", "capture_observation_failed"), error
                )

    async def release(self):
        async with self._lock:
            self.check_process()
            if self._phase == "released":
                return self.observation()
            self._phase = "released"
            self._cleanup = "unknown"
            try:
                if self._session is not None:
                    await _settled(self._session.stop())
                self._cleanup = "completed"
            except BaseException as error:  # noqa: BLE001 - cleanup cannot erase capture history
                self._complete = False
                self._diagnostics += (
                    "capture_release_incomplete:" + type(error).__name__,
                )
                self._refuse("capture_release_incomplete", error)
            return self.observation()
