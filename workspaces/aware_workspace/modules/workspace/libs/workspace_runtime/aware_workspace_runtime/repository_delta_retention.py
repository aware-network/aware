"""Neutral retention lifecycle and fixed original owner dispatch."""

from __future__ import annotations

import inspect
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import uuid4
from weakref import WeakKeyDictionary

from aware_workspace_sdk.repository_delta_retention_values import (
    WorkspaceRepositoryDeltaRetentionObservation,
    WorkspaceRepositoryDeltaRetentionPhase,
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
    MAX_DELTA_BODY_BYTES,
)

if TYPE_CHECKING:
    from aware_workspace_fs_adapter.repository_delta_retention import (
        FilesystemDeltaRetentionOwner,
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
    owner: FilesystemDeltaRetentionOwner
    pid: int = field(default_factory=os.getpid)
    ref: str = field(default_factory=lambda: "delta-retention:" + uuid4().hex)
    phase: WorkspaceRepositoryDeltaRetentionPhase = "allocated"
    binding: str | None = None
    diagnostics: tuple[str, ...] = ()
    error: BaseException | None = None


class WorkspaceRepositoryDeltaRetentionRuntime:
    resolve_bodies: Callable[..., tuple[bytes | None, ...]]

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
        state = self._state(state)
        with self._lock:
            inactive = state.phase != "active"
            owner = state.owner
            binding = state.binding
        if inactive:
            self._refuse(state, "retention_not_active")
        if type(binding) is not str:
            self._refuse(state, "retention_binding_mismatch")
        try:
            owner.verify_original_owner(expected_binding_ref=binding)
        except ValueError as error:
            self._refuse(
                state, getattr(error, "code", "retention_owner_mismatch"), error
            )
        # Owner validation may race retirement or alter the retained binding.
        # Repeat the original runtime/state check at the terminal boundary.
        self._state(state)
        with self._lock:
            if state.phase != "active":
                self._refuse(state, "retention_not_active")
            if (state.owner is not owner or type(state.binding) is not str
                or state.binding != binding):
                self._refuse(state, "retention_binding_mismatch")
        return owner

    def verify_capture_separation(self, state, *, repository_root, cache_root):
        owner = self._active_owner(state)
        try:
            owner.verify_capture_separation(
                repository_root=repository_root,
                cache_root=cache_root,
            )
        except (OSError, ValueError, TypeError) as error:
            self._refuse(
                state, getattr(error, "code", "retention_separation_refused"), error
            )

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


def _bind_original_bulk_reader(kind):
    from aware_workspace_fs_adapter import repository_delta_retention as fs
    from aware_workspace_fs_adapter.repository_delta_store import (
        WorkspaceRepositoryDeltaStore,
    )

    active = kind._active_owner
    owner_kind = fs.FilesystemDeltaRetentionOwner
    factory_kind = fs.FilesystemDeltaRetentionFactory
    owner_read = owner_kind.resolve_body
    descriptors = tuple((cls, name, inspect.getattr_static(cls, name)) for cls, names in (
        (kind, ("verify_original_runtime", "_state", "verify", "observe", "_active_owner", "_refuse")),
        (owner_kind, ("resolve_body", "_active_store", "verify_original_owner")),
        (factory_kind, ("verify_original_factory",)),
        (WorkspaceRepositoryDeltaStore, ("resolve_body", "_body_path")),
    ) for name in names)
    class_namespaces = tuple((type.__getattribute__(cls, "__dict__"), name, original)
                             for cls, name, original in descriptors)
    dunders = tuple((type.__getattribute__(cls, "__dict__"), name,
                     type.__getattribute__(cls, "__dict__").get(name))
                    for cls in (kind, _State, owner_kind, factory_kind, WorkspaceRepositoryDeltaStore)
                    for name in ("__hash__", "__eq__", "__getattribute__"))
    fs_namespace = vars(fs)
    fs_helpers = tuple((name, fs_namespace[name]) for name in ("_record", "_factory"))
    runtime_descriptors = tuple((name, original) for cls, name, original in descriptors if cls is kind)
    store_descriptors = tuple((name, original) for cls, name, original in descriptors if cls is WorkspaceRepositoryDeltaStore)

    def check_instance(value, expected):
        namespace = None
        try:
            namespace = object.__getattribute__(value, "__dict__")
            if any(name in namespace and namespace[name] is not original
                   for name, original in expected):
                raise WorkspaceRepositoryDeltaRetentionRefusal("retention_reader_origin_changed")
        finally:
            del value, expected, namespace

    def check():
        if (any(namespace.get(name) is not original for namespace, name, original in class_namespaces)
            or any(fs_namespace.get(name) is not original for name, original in fs_helpers)
            or any(namespace.get(name) is not original for namespace, name, original in dunders)):
            raise WorkspaceRepositoryDeltaRetentionRefusal("retention_reader_origin_changed")

    def resolve_bodies(self, state, body_refs):
        owner = store = original_record = None
        recognized = False
        values = []
        total_bytes = 0
        try:
            if type(body_refs) is not tuple or len(body_refs) > 65_536 or any(
                type(ref) is not str or not ref or ref.strip() != ref for ref in body_refs
            ):
                raise ValueError("exact bounded body reference tuple required")
            if type(self) is not kind:
                raise WorkspaceRepositoryDeltaRetentionRefusal("retention_owner_mismatch")
            with object.__getattribute__(self, "_lock"):
                recognized = any(item is state for item in object.__getattribute__(self, "_states"))
            check()
            check_instance(self, runtime_descriptors)
            owner = active(self, state)
            binding = state.binding
            if type(owner) is not owner_kind:
                raise WorkspaceRepositoryDeltaRetentionRefusal("retention_owner_mismatch")
            original_record = fs_helpers[0][1](owner)
            store = original_record.store
            for ref in body_refs:
                check()
                if (original_record.store is not store
                    or type(store) is not WorkspaceRepositoryDeltaStore):
                    raise WorkspaceRepositoryDeltaRetentionRefusal("retention_reader_origin_changed")
                check_instance(store, store_descriptors)
                # Keep the original state/owner current for every physical read.
                # Full outer verification is amortized, never carried to another call.
                with self._lock:
                    if (type(state) is not _State or not any(item is state for item in self._states)
                        or state.pid != os.getpid() or state.phase != "active"
                        or state.owner is not owner or state.binding != binding):
                        raise WorkspaceRepositoryDeltaRetentionRefusal("retention_not_active")
                values.append(owner_read(owner, ref))
                if values[-1] is not None:
                    total_bytes += len(values[-1])
                    if total_bytes > MAX_DELTA_BODY_BYTES:
                        raise WorkspaceRepositoryDeltaRetentionRefusal("retention_bulk_limit_exceeded")
            check()
            check_instance(store, store_descriptors)
            if original_record.store is not store:
                raise WorkspaceRepositoryDeltaRetentionRefusal("retention_reader_origin_changed")
            check_instance(self, runtime_descriptors)
            if active(self, state) is not owner or state.binding != binding:
                raise WorkspaceRepositoryDeltaRetentionRefusal("retention_owner_mismatch")
            check()
            return tuple(values)
        except BaseException:
            if recognized and type(state) is _State:
                with object.__getattribute__(self, "_lock"):
                    if object.__getattribute__(state, "phase") != "released":
                        object.__setattr__(state, "phase", "refused")
            values.clear()
            raise
        finally:
            del self, state, body_refs, owner, store, original_record, values

    return resolve_bodies


def _unavailable_bulk_reader(self, state, body_refs):
    try:
        raise WorkspaceRepositoryDeltaRetentionRefusal("retention_filesystem_unavailable")
    finally:
        del self, state, body_refs


# The filesystem adapter is optional. No backend authority exists in its absence,
# and physical descriptor origins must never be recaptured lazily in this process.
try:
    import aware_workspace_fs_adapter as _optional_filesystem_adapter
except ModuleNotFoundError as error:
    if error.name != "aware_workspace_fs_adapter":
        raise
    WorkspaceRepositoryDeltaRetentionRuntime.resolve_bodies = _unavailable_bulk_reader
else:
    del _optional_filesystem_adapter
    WorkspaceRepositoryDeltaRetentionRuntime.resolve_bodies = _bind_original_bulk_reader(
        WorkspaceRepositoryDeltaRetentionRuntime,
    )
