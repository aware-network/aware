"""Genuine original-owner retention facade; descriptive values cannot issue clients."""

from __future__ import annotations

import threading
from pathlib import Path
from weakref import WeakKeyDictionary

from aware_workspace_runtime.repository_delta import (
    WorkspaceRepositoryContentDelta,
    WorkspaceRepositoryDeltaCapture,
)
from aware_workspace_runtime.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionRefusal,
)
from aware_workspace_runtime.repository_delta_store_contract import (
    DEFAULT_DELTA_BODY_BYTES,
    DEFAULT_DELTA_BODY_CAPACITY,
    DEFAULT_DELTA_CAPTURE_CAPACITY,
    DEFAULT_DELTA_TRANSITION_CAPACITY,
    WorkspaceRepositoryDeltaStoreSnapshot,
)

_LOCK = threading.RLock()
_FACTORIES = WeakKeyDictionary()
_CLIENTS = WeakKeyDictionary()


class _Original:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use Workspace SDK filesystem retention selection")

    def __copy__(self):
        raise TypeError("Retention clients cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Retention clients cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Retention clients cannot be serialized")


def _factory(factory):
    with _LOCK:
        runtime = (
            _FACTORIES.get(factory)
            if type(factory) is WorkspaceRepositoryDeltaRetentionFactory
            else None
        )
    if runtime is None:
        raise WorkspaceRepositoryDeltaRetentionRefusal("retention_not_issued")
    runtime.verify_original_runtime()
    return runtime


def _client(client):
    with _LOCK:
        value = (
            _CLIENTS.get(client)
            if type(client) is WorkspaceRepositoryDeltaRetentionClient
            else None
        )
    if value is None:
        raise WorkspaceRepositoryDeltaRetentionRefusal("retention_not_issued")
    value[0].verify_original_runtime()
    return value


def _issue(runtime, state):
    runtime.verify_original_runtime()
    runtime.observe(state)
    client = object.__new__(WorkspaceRepositoryDeltaRetentionClient)
    with _LOCK:
        _CLIENTS[client] = (runtime, state)
    return client


class WorkspaceRepositoryDeltaRetentionFactory(_Original):
    __slots__ = ()

    @classmethod
    def filesystem(cls, *, state_root: Path):
        if cls is not WorkspaceRepositoryDeltaRetentionFactory:
            raise WorkspaceRepositoryDeltaRetentionRefusal("retention_owner_mismatch")
        from aware_workspace_fs_adapter.repository_delta_retention import (
            FilesystemDeltaRetentionFactory,
        )
        from aware_workspace_runtime.repository_delta_retention import (
            WorkspaceRepositoryDeltaRetentionRuntime,
        )

        try:
            physical = FilesystemDeltaRetentionFactory.filesystem(state_root=state_root)
        except ValueError as error:
            raise WorkspaceRepositoryDeltaRetentionRefusal(
                getattr(error, "code", "retention_owner_mismatch")
            ) from error
        runtime = WorkspaceRepositoryDeltaRetentionRuntime(physical_factory=physical)
        factory = object.__new__(cls)
        with _LOCK:
            _FACTORIES[factory] = runtime
        return factory

    def allocate_delta_retention(self):
        runtime = _factory(self)
        return _issue(runtime, runtime.allocate())

    def retain_delta_retention(
        self, original_store: object, *, expected_binding_ref: str
    ):
        runtime = _factory(self)
        return _issue(
            runtime,
            runtime.retain(original_store, expected_binding_ref=expected_binding_ref),
        )


class WorkspaceRepositoryDeltaRetentionClient(_Original):
    __slots__ = ()

    def initialize_delta_retention(
        self,
        *,
        repository_binding_ref: str,
        body_capacity: int = DEFAULT_DELTA_BODY_CAPACITY,
        maximum_bytes: int = DEFAULT_DELTA_BODY_BYTES,
        capture_capacity: int = DEFAULT_DELTA_CAPTURE_CAPACITY,
        delta_capacity: int = DEFAULT_DELTA_TRANSITION_CAPACITY,
    ):
        runtime, state = _client(self)
        return runtime.initialize(
            state,
            repository_binding_ref=repository_binding_ref,
            body_capacity=body_capacity,
            maximum_bytes=maximum_bytes,
            capture_capacity=capture_capacity,
            delta_capacity=delta_capacity,
        )

    def verify_repository_binding(self, *, expected_binding_ref: str):
        runtime, state = _client(self)
        return runtime.verify(state, expected_binding_ref=expected_binding_ref)

    def observe_retention(self):
        runtime, state = _client(self)
        return runtime.observe(state)

    def release_retention(self):
        runtime, state = _client(self)
        return runtime.release(state)

    @property
    def repository_binding_ref(self) -> str:
        runtime, state = _client(self)
        return runtime.repository_binding_ref(state)

    def snapshot(self) -> WorkspaceRepositoryDeltaStoreSnapshot:
        runtime, state = _client(self)
        return runtime.snapshot(state)

    def record_body(self, content: bytes) -> str:
        runtime, state = _client(self)
        return runtime.record_body(state, content)

    def record_bodies(self, contents: tuple[bytes, ...]) -> tuple[str, ...]:
        runtime, state = _client(self)
        return runtime.record_bodies(state, contents)

    def contains_body(self, body_ref: str) -> bool:
        runtime, state = _client(self)
        return runtime.contains_body(state, body_ref)

    def resolve_body(self, body_ref: str) -> bytes | None:
        runtime, state = _client(self)
        return runtime.resolve_body(state, body_ref)

    def record_capture(self, value: WorkspaceRepositoryDeltaCapture) -> None:
        runtime, state = _client(self)
        return runtime.record_capture(state, value)

    def resolve_capture(
        self, capture_ref: str
    ) -> WorkspaceRepositoryDeltaCapture | None:
        runtime, state = _client(self)
        return runtime.resolve_capture(state, capture_ref)

    def retained_captures(self) -> tuple[WorkspaceRepositoryDeltaCapture, ...]:
        runtime, state = _client(self)
        return runtime.retained_captures(state)

    def record_delta(self, value: WorkspaceRepositoryContentDelta) -> None:
        runtime, state = _client(self)
        return runtime.record_delta(state, value)

    def resolve_delta(self, delta_ref: str) -> WorkspaceRepositoryContentDelta | None:
        runtime, state = _client(self)
        return runtime.resolve_delta(state, delta_ref)

    def retained_deltas(self) -> tuple[WorkspaceRepositoryContentDelta, ...]:
        runtime, state = _client(self)
        return runtime.retained_deltas(state)


__all__ = (
    "WorkspaceRepositoryDeltaRetentionClient",
    "WorkspaceRepositoryDeltaRetentionFactory",
    "WorkspaceRepositoryDeltaRetentionRefusal",
)
