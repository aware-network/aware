"""Original FS retention issuance; one physical store and no caller registrars."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from weakref import WeakKeyDictionary

from aware_workspace_runtime.repository_delta import (
    WorkspaceRepositoryContentDelta,
    WorkspaceRepositoryDeltaCapture,
)
from aware_workspace_runtime.repository_delta_store_contract import (
    DEFAULT_DELTA_BODY_BYTES,
    DEFAULT_DELTA_BODY_CAPACITY,
    DEFAULT_DELTA_CAPTURE_CAPACITY,
    DEFAULT_DELTA_TRANSITION_CAPACITY,
    WorkspaceRepositoryDeltaStoreSnapshot,
)

from .repository_delta_store import WorkspaceRepositoryDeltaStore

_LOCK = threading.RLock()
_FACTORIES = WeakKeyDictionary()
_OWNERS = WeakKeyDictionary()


class DeltaRetentionOwnerRefusal(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class _Original:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use original Workspace FS retention selection")

    def __copy__(self):
        raise TypeError("Retention owners cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Retention owners cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Retention owners cannot be serialized")


@dataclass
class _OwnerRecord:
    factory: object
    store: object
    pid: int
    phase: str = "allocated"
    binding: str | None = None


def _factory(factory):
    with _LOCK:
        value = (
            _FACTORIES.get(factory)
            if type(factory) is FilesystemDeltaRetentionFactory
            else None
        )
        if value is None:
            raise DeltaRetentionOwnerRefusal("retention_owner_mismatch")
        if value[1] != os.getpid():
            raise DeltaRetentionOwnerRefusal("retention_process_mismatch")
        return value[0]


def _record(owner):
    with _LOCK:
        record = (
            _OWNERS.get(owner) if type(owner) is FilesystemDeltaRetentionOwner else None
        )
        if record is None:
            raise DeltaRetentionOwnerRefusal("retention_owner_mismatch")
        if record.pid != os.getpid():
            raise DeltaRetentionOwnerRefusal("retention_process_mismatch")
        _factory(record.factory)
        return record


class FilesystemDeltaRetentionFactory(_Original):
    __slots__ = ()

    @classmethod
    def filesystem(cls, *, state_root: Path):
        if cls is not FilesystemDeltaRetentionFactory or not isinstance(
            state_root, Path
        ):
            raise DeltaRetentionOwnerRefusal("retention_owner_mismatch")
        factory = object.__new__(cls)
        with _LOCK:
            _FACTORIES[factory] = (state_root, os.getpid())
        return factory

    def verify_original_factory(self):
        _factory(self)

    def allocate_owner(self):
        _factory(self)
        # Retain the actual original before any effectful initializer.
        owner = object.__new__(FilesystemDeltaRetentionOwner)
        record = _OwnerRecord(
            self, object.__new__(WorkspaceRepositoryDeltaStore), os.getpid()
        )
        with _LOCK:
            _OWNERS[owner] = record
        return owner

    def retain_owner(self, original_store, *, expected_binding_ref):
        _factory(self)
        if type(original_store) is not WorkspaceRepositoryDeltaStore:
            raise DeltaRetentionOwnerRefusal("retention_owner_mismatch")
        # Original active issued stores cannot be adopted after a failed init.
        with _LOCK:
            siblings = tuple(r for r in _OWNERS.values() if r.store is original_store)
            if any(r.phase != "active" for r in siblings):
                raise DeltaRetentionOwnerRefusal("retention_not_active")
        try:
            binding = original_store.repository_binding_ref
            original_store.snapshot()
        except (AttributeError, TypeError) as error:
            raise DeltaRetentionOwnerRefusal("retention_not_active") from error
        if binding != expected_binding_ref:
            raise DeltaRetentionOwnerRefusal("retention_binding_mismatch")
        owner = object.__new__(FilesystemDeltaRetentionOwner)
        with _LOCK:
            _OWNERS[owner] = _OwnerRecord(
                self, original_store, os.getpid(), "active", binding
            )
        return owner


class FilesystemDeltaRetentionOwner(_Original):
    __slots__ = ()

    def verify_original_owner(self, *, expected_binding_ref):
        record = _record(self)
        with _LOCK:
            if record.phase != "active":
                raise DeltaRetentionOwnerRefusal("retention_not_active")
            if type(record.store) is not WorkspaceRepositoryDeltaStore:
                raise DeltaRetentionOwnerRefusal("retention_owner_mismatch")
            if record.binding != expected_binding_ref:
                raise DeltaRetentionOwnerRefusal("retention_binding_mismatch")
            store = record.store
        if store.repository_binding_ref != expected_binding_ref:
            raise DeltaRetentionOwnerRefusal("retention_binding_mismatch")

    def initialize_original_store(
        self,
        *,
        repository_binding_ref,
        body_capacity=DEFAULT_DELTA_BODY_CAPACITY,
        maximum_bytes=DEFAULT_DELTA_BODY_BYTES,
        capture_capacity=DEFAULT_DELTA_CAPTURE_CAPACITY,
        delta_capacity=DEFAULT_DELTA_TRANSITION_CAPACITY,
    ):
        record = _record(self)
        with _LOCK:
            if record.phase != "allocated":
                raise DeltaRetentionOwnerRefusal("retention_initializer_spent")
            record.phase = "initializing"
            record.binding = repository_binding_ref
            store = record.store
        try:
            WorkspaceRepositoryDeltaStore.__init__(
                store,
                state_root=_factory(record.factory),
                repository_binding_ref=repository_binding_ref,
                body_capacity=body_capacity,
                maximum_bytes=maximum_bytes,
                capture_capacity=capture_capacity,
                delta_capacity=delta_capacity,
            )
        except BaseException:
            with _LOCK:
                if record.phase != "released":
                    record.phase = "refused"
            raise
        with _LOCK:
            if record.phase != "initializing":
                raise DeltaRetentionOwnerRefusal("retention_not_active")
            record.phase = "active"

    def _active_store(self):
        record = _record(self)
        self.verify_original_owner(expected_binding_ref=record.binding)
        with _LOCK:
            if record.phase != "active":
                raise DeltaRetentionOwnerRefusal("retention_not_active")
            return record.store

    @property
    def repository_binding_ref(self) -> str:
        return self._active_store().repository_binding_ref

    def retire_owner(self):
        record = _record(self)
        with _LOCK:
            record.phase = "released"
            record.store = None

    def snapshot(self) -> WorkspaceRepositoryDeltaStoreSnapshot:
        return self._active_store().snapshot()

    def record_body(self, content: bytes) -> str:
        return self._active_store().record_body(content)

    def record_bodies(self, contents: tuple[bytes, ...]) -> tuple[str, ...]:
        return self._active_store().record_bodies(contents)

    def contains_body(self, body_ref: str) -> bool:
        return self._active_store().contains_body(body_ref)

    def resolve_body(self, body_ref: str) -> bytes | None:
        return self._active_store().resolve_body(body_ref)

    def record_capture(self, value: WorkspaceRepositoryDeltaCapture) -> None:
        return self._active_store().record_capture(value)

    def resolve_capture(
        self, capture_ref: str
    ) -> WorkspaceRepositoryDeltaCapture | None:
        return self._active_store().resolve_capture(capture_ref)

    def retained_captures(self) -> tuple[WorkspaceRepositoryDeltaCapture, ...]:
        return self._active_store().retained_captures()

    def record_delta(self, value: WorkspaceRepositoryContentDelta) -> None:
        return self._active_store().record_delta(value)

    def resolve_delta(self, delta_ref: str) -> WorkspaceRepositoryContentDelta | None:
        return self._active_store().resolve_delta(delta_ref)

    def retained_deltas(self) -> tuple[WorkspaceRepositoryContentDelta, ...]:
        return self._active_store().retained_deltas()
