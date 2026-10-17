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
from .repository_index_journal import IndexJournal

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
    journal_origin: tuple | None = None


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
    def filesystem(cls, *, state_root: Path, index_format: str = "json_v1"):
        if cls is not FilesystemDeltaRetentionFactory or not isinstance(
            state_root, Path
        ):
            raise DeltaRetentionOwnerRefusal("retention_owner_mismatch")
        if type(index_format) is not str or index_format not in (
            "json_v1",
            "events_v2",
            "auto",
        ):
            raise DeltaRetentionOwnerRefusal("retention_index_format_invalid")
        factory = object.__new__(cls)
        with _LOCK:
            _FACTORIES[factory] = (state_root, os.getpid(), index_format)
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
            journal = vars(original_store).get("_index_journal")
            if type(journal) is not IndexJournal:
                raise DeltaRetentionOwnerRefusal("retention_index_origin_unknown")
            _OWNERS[owner] = _OwnerRecord(
                self,
                original_store,
                os.getpid(),
                "active",
                binding,
                (
                    journal,
                    IndexJournal,
                    vars(IndexJournal)["__dict__"],
                    WorkspaceRepositoryDeltaStore,
                    vars(WorkspaceRepositoryDeltaStore)["__dict__"],
                ),
            )
        return owner


class FilesystemDeltaRetentionOwner(_Original):
    __slots__ = ()

    def verify_capture_separation(self, *, repository_root: Path, cache_root: Path):
        record = _record(self)
        self.verify_original_owner(expected_binding_ref=record.binding)
        # A retaining factory can name another root. Only the native store's
        # actual location establishes physical separation.
        store_root = record.store.store_root
        roots = (repository_root, cache_root, store_root)
        if any(
            not isinstance(p, Path) or not p.is_absolute() or p.resolve() != p
            for p in roots
        ):
            raise DeltaRetentionOwnerRefusal("retention_canonical_roots_required")
        for index, left in enumerate(roots):
            for right in roots[index + 1 :]:
                if left.is_relative_to(right) or right.is_relative_to(left):
                    raise DeltaRetentionOwnerRefusal("retention_capture_roots_overlap")

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
                index_format=_FACTORIES[record.factory][2],
            )
        except BaseException:
            with _LOCK:
                if record.phase != "released":
                    record.phase = "refused"
            raise
        with _LOCK:
            if record.phase != "initializing":
                raise DeltaRetentionOwnerRefusal("retention_not_active")
            journal = vars(store).get("_index_journal")
            if type(journal) is not IndexJournal:
                record.phase = "refused"
                raise DeltaRetentionOwnerRefusal("retention_index_origin_unknown")
            record.journal_origin = (
                journal,
                IndexJournal,
                vars(IndexJournal)["__dict__"],
                WorkspaceRepositoryDeltaStore,
                vars(WorkspaceRepositoryDeltaStore)["__dict__"],
            )
            record.phase = "active"

    def _active_store(self):
        record = _record(self)
        self.verify_original_owner(expected_binding_ref=record.binding)
        with _LOCK:
            if record.phase != "active":
                raise DeltaRetentionOwnerRefusal("retention_not_active")
            origin = record.journal_origin
            if (
                origin is None
                or type(origin[0]) is not origin[1]
                or type(record.store) is not origin[3]
                or origin[4].__get__(record.store, origin[3]).get("_index_journal")
                is not origin[0]
            ):
                record.phase = "refused"
                raise DeltaRetentionOwnerRefusal("retention_index_origin_unknown")
            return record.store

    @property
    def repository_binding_ref(self) -> str:
        return self._active_store().repository_binding_ref

    def retire_owner(self):
        record = _record(self)
        with _LOCK:
            store, origin = record.store, record.journal_origin
            record.phase = "released"
            record.store = record.journal_origin = None
        if store is None:
            return
        if origin is None:
            if type(store) is not WorkspaceRepositoryDeltaStore:
                raise DeltaRetentionOwnerRefusal("retention_index_origin_unknown")
            if vars(store).get("_index_journal") is not None:
                raise DeltaRetentionOwnerRefusal("retention_index_origin_unknown")
            return
        journal, kind, storage, store_kind, store_storage = origin
        if (
            type(store) is not store_kind
            or type(journal) is not kind
            or vars(kind).get("__dict__") is not storage
            or "failure_evidence" in vars(kind)
            or store_storage.__get__(store, store_kind).get("_index_journal")
            is not journal
        ):
            raise DeltaRetentionOwnerRefusal("retention_index_origin_unknown")
        if storage.__get__(journal, kind).get("failure_evidence") is not None:
            # Original custody is spent, uncertainty never delegates to a
            # substituted getter or renews after restoring the store field.
            raise DeltaRetentionOwnerRefusal("retention_index_cleanup_unknown")

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
