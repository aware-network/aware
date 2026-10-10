"""Neutral retention lifecycle and fixed original owner dispatch."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from uuid import uuid4
from weakref import WeakKeyDictionary

from aware_workspace_sdk.repository_delta_retention_values import (
    WorkspaceRepositoryDeltaRetentionObservation,
)

from aware_workspace_runtime.repository_delta import (
    WorkspaceRepositoryContentDelta,
    WorkspaceRepositoryDeltaCapture,
)
from aware_workspace_runtime.repository_delta_store_contract import (
    WorkspaceRepositoryDeltaStoreSnapshot,
)

from .repository_delta_store_contract import (
    DEFAULT_DELTA_BODY_BYTES,
    DEFAULT_DELTA_BODY_CAPACITY,
    DEFAULT_DELTA_CAPTURE_CAPACITY,
    DEFAULT_DELTA_TRANSITION_CAPACITY,
)

_RUNTIME_LOCK = threading.RLock()
_RUNTIMES = WeakKeyDictionary()


class WorkspaceRepositoryDeltaRetentionRefusal(ValueError):
    def __init__(self, code, observation=None):
        self.code = code
        self.observation = observation
        super().__init__(code)


@dataclass(eq=False)
class _State:
    owner: object
    pid: int = field(default_factory=os.getpid)
    ref: str = field(default_factory=lambda: "delta-retention:" + uuid4().hex)
    phase: str = "allocated"
    binding: str | None = None
    diagnostics: tuple[str, ...] = ()
    error: BaseException | None = None


class WorkspaceRepositoryDeltaRetentionRuntime:
    def __init__(self, *, physical_factory):
        from aware_workspace_fs_adapter.repository_delta_retention import (
            FilesystemDeltaRetentionFactory,
        )

        if type(physical_factory) is not FilesystemDeltaRetentionFactory:
            raise WorkspaceRepositoryDeltaRetentionRefusal("retention_owner_mismatch")
        try:
            physical_factory.verify_original_factory()
        except ValueError as error:
            raise WorkspaceRepositoryDeltaRetentionRefusal(
                getattr(error, "code", "retention_owner_mismatch")
            ) from error
        self._physical = physical_factory
        self._states = set()
        self._lock = threading.RLock()
        self._pid = os.getpid()
        self._generation = "delta-provider:" + uuid4().hex
        with _RUNTIME_LOCK:
            _RUNTIMES[self] = physical_factory

    def verify_original_runtime(self):
        with _RUNTIME_LOCK:
            factory = (
                _RUNTIMES.get(self)
                if type(self) is WorkspaceRepositoryDeltaRetentionRuntime
                else None
            )
        if factory is None:
            raise WorkspaceRepositoryDeltaRetentionRefusal("retention_owner_mismatch")
        if factory is not self._physical:
            raise WorkspaceRepositoryDeltaRetentionRefusal("retention_owner_mismatch")
        if self._pid != os.getpid():
            raise WorkspaceRepositoryDeltaRetentionRefusal("retention_process_mismatch")
        try:
            factory.verify_original_factory()
        except ValueError as error:
            raise WorkspaceRepositoryDeltaRetentionRefusal(
                getattr(error, "code", "retention_owner_mismatch")
            ) from error

    def allocate(self):
        self.verify_original_runtime()
        state = _State(self._physical.allocate_owner())
        with self._lock:
            self._states.add(state)
        return state

    def retain(self, store, *, expected_binding_ref):
        self.verify_original_runtime()
        try:
            owner = self._physical.retain_owner(
                store, expected_binding_ref=expected_binding_ref
            )
        except ValueError as error:
            raise WorkspaceRepositoryDeltaRetentionRefusal(
                getattr(error, "code", "retention_owner_mismatch")
            ) from error
        state = _State(owner, phase="active", binding=expected_binding_ref)
        with self._lock:
            self._states.add(state)
        return state

    def _state(self, state):
        self.verify_original_runtime()
        with self._lock:
            if type(state) is not _State or state not in self._states:
                raise WorkspaceRepositoryDeltaRetentionRefusal("retention_not_issued")
            if state.pid != os.getpid():
                raise WorkspaceRepositoryDeltaRetentionRefusal(
                    "retention_process_mismatch"
                )
        return state

    def observe(self, state):
        state = self._state(state)
        with self._lock:
            return WorkspaceRepositoryDeltaRetentionObservation(
                state.ref,
                state.binding,
                state.phase,
                self._generation,
                state.pid,
                state.diagnostics,
            )

    def _refuse(self, state, code, error=None):
        refusal = WorkspaceRepositoryDeltaRetentionRefusal(code, self.observe(state))
        if error is not None:
            raise refusal from error
        raise refusal

    def initialize(
        self,
        state,
        *,
        repository_binding_ref,
        body_capacity=DEFAULT_DELTA_BODY_CAPACITY,
        maximum_bytes=DEFAULT_DELTA_BODY_BYTES,
        capture_capacity=DEFAULT_DELTA_CAPTURE_CAPACITY,
        delta_capacity=DEFAULT_DELTA_TRANSITION_CAPACITY,
    ):
        state = self._state(state)
        with self._lock:
            spent = state.phase != "allocated"
            if not spent:
                state.phase = "initializing"
                state.binding = (
                    repository_binding_ref
                    if isinstance(repository_binding_ref, str)
                    else None
                )
        if spent:
            self._refuse(state, "retention_initializer_spent")
        try:
            state.owner.initialize_original_store(
                repository_binding_ref=repository_binding_ref,
                body_capacity=body_capacity,
                maximum_bytes=maximum_bytes,
                capture_capacity=capture_capacity,
                delta_capacity=delta_capacity,
            )
        except BaseException as error:  # noqa: BLE001 - interrupted initialization is spent
            with self._lock:
                if state.phase != "released":
                    state.phase = "refused"
                state.error = error
                state.diagnostics += (type(error).__name__,)
            self._refuse(state, "retention_storage_initialization_refused", error)
        with self._lock:
            retired = state.phase != "initializing"
            if not retired:
                state.phase = "active"
        if retired:
            self._refuse(state, "retention_not_active")
        return self.observe(state)

    def verify(self, state, *, expected_binding_ref):
        state = self._state(state)
        with self._lock:
            inactive = state.phase != "active"
            mismatched = (
                type(expected_binding_ref) is not str
                or state.binding != expected_binding_ref
            )
            owner = state.owner
        if inactive:
            self._refuse(state, "retention_not_active")
        if mismatched:
            self._refuse(state, "retention_binding_mismatch")
        try:
            owner.verify_original_owner(expected_binding_ref=expected_binding_ref)
        except ValueError as error:
            self._refuse(
                state, getattr(error, "code", "retention_owner_mismatch"), error
            )
        return self.observe(state)

    def _active_owner(self, state):
        self.verify(state, expected_binding_ref=self._state(state).binding)
        with self._lock:
            inactive = state.phase != "active"
            owner = state.owner
        if inactive:
            self._refuse(state, "retention_not_active")
        return owner

    def release(self, state):
        state = self._state(state)
        with self._lock:
            released = state.phase == "released"
            state.phase = "released"
            owner = state.owner
        if released:
            return self.observe(state)
        try:
            owner.retire_owner()
        except BaseException as error:  # noqa: BLE001 - retirement never renews authority
            with self._lock:
                state.diagnostics += (type(error).__name__,)
            self._refuse(state, "retention_supplier_unavailable", error)
        return self.observe(state)

    def repository_binding_ref(self, state):
        return self._active_owner(state).repository_binding_ref

    def snapshot(self, state) -> WorkspaceRepositoryDeltaStoreSnapshot:
        return self._active_owner(state).snapshot()

    def record_body(self, state, content: bytes) -> str:
        return self._active_owner(state).record_body(content)

    def record_bodies(self, state, contents: tuple[bytes, ...]) -> tuple[str, ...]:
        return self._active_owner(state).record_bodies(contents)

    def contains_body(self, state, body_ref: str) -> bool:
        return self._active_owner(state).contains_body(body_ref)

    def resolve_body(self, state, body_ref: str) -> bytes | None:
        return self._active_owner(state).resolve_body(body_ref)

    def record_capture(self, state, value: WorkspaceRepositoryDeltaCapture) -> None:
        return self._active_owner(state).record_capture(value)

    def resolve_capture(
        self, state, capture_ref: str
    ) -> WorkspaceRepositoryDeltaCapture | None:
        return self._active_owner(state).resolve_capture(capture_ref)

    def retained_captures(self, state) -> tuple[WorkspaceRepositoryDeltaCapture, ...]:
        return self._active_owner(state).retained_captures()

    def record_delta(self, state, value: WorkspaceRepositoryContentDelta) -> None:
        return self._active_owner(state).record_delta(value)

    def resolve_delta(
        self, state, delta_ref: str
    ) -> WorkspaceRepositoryContentDelta | None:
        return self._active_owner(state).resolve_delta(delta_ref)

    def retained_deltas(self, state) -> tuple[WorkspaceRepositoryContentDelta, ...]:
        return self._active_owner(state).retained_deltas()
