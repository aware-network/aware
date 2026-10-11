"""Original Workspace capture selection; observations grant no write authority."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

if TYPE_CHECKING:
    from aware_workspace_runtime.contracts import WorkspaceRepositoryObservationSnapshot
    from aware_workspace_runtime.repository_delta import (
        WorkspaceRepositoryContentDelta,
        WorkspaceRepositoryDeltaCapture,
        WorkspaceRepositoryDeltaCapturePolicy,
    )

    from .repository_delta_retention import WorkspaceRepositoryDeltaRetentionClient


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaCaptureObservation:
    session_ref: str
    repository_binding_ref: str
    phase: str
    capture: WorkspaceRepositoryDeltaCapture | None
    snapshot: WorkspaceRepositoryObservationSnapshot | None
    deltas: tuple[WorkspaceRepositoryContentDelta, ...]
    ledger_complete: bool
    cleanup_state: str
    diagnostics: tuple[str, ...]


class WorkspaceRepositoryDeltaCaptureRefusal(ValueError):
    def __init__(self, code: str, *, observation=None):
        self.code = code
        self.observation = observation
        super().__init__(code)


_LOCK = threading.RLock()
_CLIENTS = WeakKeyDictionary()


class WorkspaceRepositoryDeltaCaptureClient:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use original Workspace capture filesystem selection")

    def __copy__(self):
        raise TypeError("Capture clients cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Capture clients cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Capture clients cannot be serialized")

    @classmethod
    def filesystem(
        cls,
        *,
        repository_root: Path,
        cache_root: Path,
        retention: WorkspaceRepositoryDeltaRetentionClient,
    ) -> WorkspaceRepositoryDeltaCaptureClient:
        if cls is not WorkspaceRepositoryDeltaCaptureClient:
            raise WorkspaceRepositoryDeltaCaptureRefusal("capture_client_not_issued")
        from aware_workspace_fs_adapter.repository_delta_capture import (
            FilesystemDeltaCapturePort,
        )
        from aware_workspace_runtime.repository_delta_capture_client import (
            WorkspaceRepositoryDeltaCaptureRuntime,
        )

        try:
            physical = FilesystemDeltaCapturePort(
                repository_root=repository_root,
                cache_root=cache_root,
            )
            runtime = WorkspaceRepositoryDeltaCaptureRuntime(
                physical=physical,
                retention=retention,
            )
        except WorkspaceRepositoryDeltaCaptureRefusal:
            raise
        except (OSError, ValueError, TypeError) as error:
            raise WorkspaceRepositoryDeltaCaptureRefusal(
                getattr(error, "code", "capture_selection_refused"),
            ) from error
        client = object.__new__(cls)
        with _LOCK:
            _CLIENTS[client] = runtime
        return client

    def _owner(self):
        with _LOCK:
            owner = (
                _CLIENTS.get(self)
                if type(self) is WorkspaceRepositoryDeltaCaptureClient
                else None
            )
        if owner is None:
            raise WorkspaceRepositoryDeltaCaptureRefusal("capture_client_not_issued")
        owner.check_process()
        return owner

    @property
    def repository_binding_ref(self) -> str:
        return self._owner().binding_ref

    async def prepare_capture(
        self,
        *,
        selected_paths: tuple[str, ...],
        policy: WorkspaceRepositoryDeltaCapturePolicy | None = None,
        context_refs: tuple[str, ...] = (),
    ) -> WorkspaceRepositoryDeltaCaptureObservation:
        return await self._owner().prepare(
            selected_paths=selected_paths,
            policy=policy,
            context_refs=context_refs,
        )

    async def observe_capture(self) -> WorkspaceRepositoryDeltaCaptureObservation:
        return await self._owner().poll()

    def capture_observation(self) -> WorkspaceRepositoryDeltaCaptureObservation:
        """Detached retained evidence; no polling, renewal or causal inference."""
        return self._owner().observation()

    async def release_capture(self) -> WorkspaceRepositoryDeltaCaptureObservation:
        """Close only this observer; the borrowed retention client stays owned."""
        return await self._owner().release()


__all__ = (
    "WorkspaceRepositoryDeltaCaptureClient",
    "WorkspaceRepositoryDeltaCaptureObservation",
    "WorkspaceRepositoryDeltaCaptureRefusal",
)
