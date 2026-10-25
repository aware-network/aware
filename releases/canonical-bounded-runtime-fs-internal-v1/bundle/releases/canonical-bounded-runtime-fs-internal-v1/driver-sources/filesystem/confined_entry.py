"""Original Linux nofollow entry facts and bounded rosters, not tree authority.

Descriptor custody/settlement belongs to the original read ledger. Directory
cursors have separate once-only object rights; these are not hidden FD counts.
No contents, child traversal, repair, mutation, native dispatch or trust verdict.
"""

from __future__ import annotations

import errno
import os
import stat
import sys
import threading
from dataclasses import dataclass, fields
from itertools import pairwise
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, cast
from uuid import uuid4
from weakref import WeakKeyDictionary

from ._observation_receipt import _BODY_RECORD_BYTES, _ValueReceipt
from .confined_mutation import (
    ConfinedFileReadCleanup,
    _cause_kind,
    _read_root,
    _ReadLedger,
    _saved_read_path,
    _settle_confined_read_ledger,
)

_VALUE_POOLS = WeakKeyDictionary()


class _EntryValuePool:
    """Data sharing only; never a descriptor, observation or dispatch right."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use original entry value storage")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Entry value storage cannot be subclassed")

    def __copy__(self):
        raise TypeError("Entry value storage cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Entry value storage cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Entry value storage cannot be serialized")


def _new_entry_value_pool(*, packed_stats=False):
    if type(packed_stats) is not bool:
        raise TypeError("explicit_entry_stat_storage_profile_required")
    value = object.__new__(_EntryValuePool)
    _VALUE_POOLS[value] = (
        (os.getpid(), threading.get_ident()),
        {},
        {},
        packed_stats,
        {},
    )
    return value


def _value_pool(value):
    if type(value) is not _EntryValuePool or value not in _VALUE_POOLS:
        raise TypeError("original_entry_value_storage_required")
    record = _VALUE_POOLS[value]
    if record[0] != (os.getpid(), threading.get_ident()):
        raise ValueError("entry_value_storage_affinity")
    return record


def _shared_value(pool, value):
    if pool is None:
        return value
    record = _value_pool(pool)
    if type(value) not in (int, str):
        raise TypeError("immutable_entry_scalar_required")
    table = record[1 if type(value) is int else 2]
    if value in table:
        original = table[value]
        if type(original) is not type(value) or original != value:
            raise ValueError("entry_value_storage_changed")
        return original
    if len(table) >= (128 if record[3] else 4096):
        # Bounded cache eviction changes no occurrence/call/evidence charge.
        table.pop(next(iter(table)))
    table[value] = value
    return value


@dataclass(frozen=True, slots=True)
class ConfinedEntryRequest:
    root: Path
    path: str | None
    maximum_children: int
    maximum_name_bytes: int
    maximum_roster_bytes: int


@dataclass(frozen=True, slots=True)
class EntryRequestSnapshot:
    root: str
    path: str | None
    maximum_children: int
    maximum_name_bytes: int
    maximum_roster_bytes: int


@dataclass(frozen=True, slots=True)
class EntryStat:
    device: int
    inode: int
    mode: int
    uid: int
    gid: int
    nlink: int
    size: int
    mtime_ns: int
    ctime_ns: int

    def __post_init__(self):
        values = self.values()
        if any(type(value) is not int for value in values) or any(
            value < 0 for value in values[:7]
        ):
            raise ValueError("invalid_entry_stat")

    def values(self):
        return (
            self.device,
            self.inode,
            self.mode,
            self.uid,
            self.gid,
            self.nlink,
            self.size,
            self.mtime_ns,
            self.ctime_ns,
        )


@dataclass(frozen=True, slots=True, eq=False)
class _PackedEntryStat:
    """Fresh original observation wrapper sharing immutable scalar values.

    Selected only through the private packed-stat pool. Sharing values never
    skips an original syscall or shares the observation object's identity.
    """

    _values: tuple[int, ...]

    def __post_init__(self):
        if type(self._values) is not tuple or len(self._values) != 9:
            raise ValueError("complete_original_entry_stat_required")
        EntryStat.__post_init__(cast(EntryStat, self))

    def values(self):
        return self._values

    def __eq__(self, other):
        if type(other) not in (EntryStat, _PackedEntryStat):
            return NotImplemented
        return self._values == other.values()

    def __hash__(self):
        return hash(self._values)

    @property
    def device(self):
        return self._values[0]

    @property
    def inode(self):
        return self._values[1]

    @property
    def mode(self):
        return self._values[2]

    @property
    def uid(self):
        return self._values[3]

    @property
    def gid(self):
        return self._values[4]

    @property
    def nlink(self):
        return self._values[5]

    @property
    def size(self):
        return self._values[6]

    @property
    def mtime_ns(self):
        return self._values[7]

    @property
    def ctime_ns(self):
        return self._values[8]


EntryStatValue = EntryStat | _PackedEntryStat


@dataclass(frozen=True, slots=True)
class EntryAncestorBookends:
    path: str
    named_before: EntryStatValue
    opened_before: EntryStatValue
    named_after: EntryStatValue
    opened_after: EntryStatValue
    under_selected_root: bool


@dataclass(frozen=True, slots=True)
class EntryResource:
    resource_ref: str
    kind: str
    path: str | None
    acquisition_state: str
    close_spent: bool
    closed: bool | None


@dataclass(frozen=True, slots=True)
class EntryCursorCleanup:
    outcome: str
    acquired_count: int | None
    release_attempted_count: int | None
    closed_count: int | None
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self):
        counts = (self.acquired_count, self.release_attempted_count, self.closed_count)
        if self.outcome not in {"not_acquired", "closed", "unknown"}:
            raise ValueError("invalid_cursor_cleanup_outcome")
        if any(
            value is not None and (type(value) is not int or not 0 <= value <= 2)
            for value in counts
        ):
            raise ValueError("invalid_cursor_cleanup_count")
        if type(self.diagnostics) is not tuple or len(self.diagnostics) > 16:
            raise ValueError("invalid_cursor_diagnostics")
        if any(
            type(value) is not str or len(value.encode("utf-8")) > 1024
            for value in self.diagnostics
        ):
            raise ValueError("invalid_cursor_diagnostic")
        if self.outcome == "not_acquired" and (counts != (0, 0, 0) or self.diagnostics):
            raise ValueError("invalid_cursor_not_acquired")
        if self.outcome == "closed" and (
            counts not in {(1, 1, 1), (2, 2, 2)} or self.diagnostics
        ):
            raise ValueError("invalid_cursor_closed")
        if any(a is not None and b is not None and a < b for a, b in pairwise(counts)):
            raise ValueError("inconsistent_cursor_counts")
        if (
            self.outcome == "unknown"
            and not self.diagnostics
            and (counts == (0, 0, 0) or counts in {(1, 1, 1), (2, 2, 2)})
        ):
            raise ValueError("cursor_cleanup_uncertainty_required")


@dataclass(frozen=True, slots=True)
class ConfinedEntryObservation:
    request_snapshot: EntryRequestSnapshot
    observation_ref: str
    root_locator: str
    path: str | None
    root_before: EntryStatValue
    root_after: EntryStatValue
    ancestor_bookends: tuple[EntryAncestorBookends, ...]
    entry_before: EntryStatValue
    entry_after: EntryStatValue
    opened_directory: EntryStatValue | None
    kind: str
    children_before: tuple[str, ...] | None
    children_after: tuple[str, ...] | None
    link_text: str | None
    descriptor_cleanup: ConfinedFileReadCleanup
    cursor_cleanup: EntryCursorCleanup
    descriptor_resources: tuple[EntryResource, ...]
    cursor_resources: tuple[EntryResource, ...]
    grade: str = "entry_metadata_observed"
    continuous_exclusion: bool = False
    authorizes_dispatch: bool = False

    def __post_init__(self):
        if (
            self.grade != "entry_metadata_observed"
            or self.continuous_exclusion is not False
            or self.authorizes_dispatch is not False
        ):
            raise ValueError("entry_observation_is_not_authority")
        if (
            self.request_snapshot.root != self.root_locator
            or self.request_snapshot.path != self.path
        ):
            raise ValueError("entry_request_correlation_failed")
        self.descriptor_cleanup.__post_init__()
        self.cursor_cleanup.__post_init__()
        if self.descriptor_cleanup.outcome != "closed":
            raise ValueError("entry_descriptor_cleanup_unverified")
        resources = self.descriptor_resources + self.cursor_resources
        if len({row.resource_ref for row in resources}) != len(resources) or any(
            row.acquisition_state != "acquired"
            or row.close_spent is not True
            or row.closed is not True
            for row in resources
        ):
            raise ValueError("entry_resource_release_unverified")
        if self.descriptor_cleanup.acquired_count != len(self.descriptor_resources):
            raise ValueError("entry_descriptor_count_mismatch")
        if self.root_before != self.root_after or self.entry_before != self.entry_after:
            raise ValueError("entry_bookend_changed")
        if self.kind == "directory":
            if (
                self.opened_directory != self.entry_before
                or self.children_before is None
                or self.children_before != self.children_after
                or self.link_text is not None
                or len(self.cursor_resources) != 2
                or self.cursor_cleanup != EntryCursorCleanup("closed", 2, 2, 2)
            ):
                raise ValueError("entry_directory_evidence_invalid")
        elif self.kind in {"file", "symlink"}:
            if (
                any(
                    value is not None
                    for value in (
                        self.opened_directory,
                        self.children_before,
                        self.children_after,
                    )
                )
                or self.cursor_resources
                or self.cursor_cleanup != EntryCursorCleanup("not_acquired", 0, 0, 0)
            ):
                raise ValueError("entry_nondirectory_evidence_invalid")
            if (self.link_text is None) != (self.kind == "file"):
                raise ValueError("entry_link_evidence_invalid")
        else:
            raise ValueError("unsupported_entry_kind")


_ENTRY_RESULT_TYPE = ConfinedEntryObservation

OBSERVATION_RECEIPT_PROFILE = "aware.filesystem.closed-entry-value-receipt.v1"
_ENTRY_RECEIPT_POOL = None
_ENTRY_HEADER_PROFILE = "original_sealed_body_header_v1"
_ENTRY_HEADER_CACHE = {}
_ENTRY_HEADER_CACHE_LIMIT = 16
_ENTRY_INVOCATION_ISSUER = None


@dataclass(slots=True)
class _EntryInvocationIssuer:
    pool: object
    generation: str
    counter: int
    pending: dict


def _entry_invocation_issuer():
    global _ENTRY_INVOCATION_ISSUER
    pool = _entry_receipt_pool()
    pool._current()
    if _ENTRY_INVOCATION_ISSUER is None:
        _ENTRY_INVOCATION_ISSUER = _EntryInvocationIssuer(pool, uuid4().hex, 0, {})
    issuer = _ENTRY_INVOCATION_ISSUER
    if issuer.pool is not pool:
        raise ValueError("original_entry_issuer_changed")
    return issuer


def _reserve_entry_invocation(state):
    from ._observation_receipt import CALL_LIMIT

    issuer = _entry_invocation_issuer()
    if issuer.counter >= CALL_LIMIT:
        raise ValueError("original_entry_invocation_capacity")
    issuer.counter += 1  # Failed original observations never refund a coordinate.
    reference = "entry-observation:" + issuer.generation[:24] + f"{issuer.counter:08x}"
    prefix = issuer.generation[:24] + f"{issuer.counter:06x}"
    issuer.pending[reference] = prefix
    state.observation_ref = reference
    state.descriptors.reference_prefix = prefix
    return issuer, reference


class EntryObservationReceipt(_ValueReceipt):
    """Original-owner receipt; attribute snapshots are detached historical values."""

    __slots__ = ()

    def __new__(cls):
        raise TypeError("original_entry_observer_required")

    def __copy__(self):
        raise TypeError("entry_receipt_cannot_be_copied")

    def __deepcopy__(self, memo):
        raise TypeError("entry_receipt_cannot_be_copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("entry_receipt_is_process_local")

    def __getattr__(self, name: str) -> Any:
        header = _entry_receipt_record(self)[1]
        scalar = {
            "observation_ref": 1,
            "root_locator": 2,
            "path": 3,
            "kind": 8,
            "grade": 9,
            "continuous_exclusion": 10,
            "authorizes_dispatch": 11,
        }
        stats = {"root_before": 4, "root_after": 5, "entry_before": 6, "entry_after": 7}
        if name in scalar:
            return header[scalar[name]]
        if name in stats:
            return _PackedEntryStat(header[stats[name]])
        if name == "request_snapshot":
            return EntryRequestSnapshot(*header[0])
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(snapshot_confined_entry_receipt(self), name)


def _entry_receipt_pool():
    global _ENTRY_RECEIPT_POOL
    if _ENTRY_RECEIPT_POOL is None:
        from ._observation_receipt import _ClosedValuePool

        _ENTRY_RECEIPT_POOL = _ClosedValuePool(
            (
                EntryRequestSnapshot,
                EntryStat,
                _PackedEntryStat,
                EntryAncestorBookends,
                EntryResource,
                EntryCursorCleanup,
                ConfinedFileReadCleanup,
                _ENTRY_RESULT_TYPE,
            ),
            shared_bodies=True,
            receipt_type=EntryObservationReceipt,
        )
    return _ENTRY_RECEIPT_POOL


def _entry_value_header(value):
    return (
        tuple(
            getattr(value.request_snapshot, field.name)
            for field in fields(EntryRequestSnapshot)
        ),
        value.observation_ref,
        value.root_locator,
        value.path,
        value.root_before.values(),
        value.root_after.values(),
        value.entry_before.values(),
        value.entry_after.values(),
        value.kind,
        value.grade,
        value.continuous_exclusion,
        value.authorizes_dispatch,
    )


def _capture_entry_receipt(value) -> EntryObservationReceipt:
    from ._staging_guard_history import value_seal

    pool = _entry_receipt_pool()
    issuer = _entry_invocation_issuer()
    prefix = issuer.pending.get(value.observation_ref)
    if (
        type(prefix) is not str
        or any(
            resource.resource_ref != "read-resource:" + prefix + f"{index:02x}"
            for index, resource in enumerate(value.descriptor_resources)
        )
        or any(
            resource.resource_ref != value.observation_ref + ":cursor:" + str(index)
            for index, resource in enumerate(value.cursor_resources)
        )
    ):
        raise ValueError("original_entry_invocation_references_required")
    ref = pool.capture(value)
    if type(ref) is not EntryObservationReceipt:
        raise TypeError("original_entry_receipt_type_required")
    header = _entry_value_header(value)
    if _entry_value_header(pool.snapshot(ref)) != header:
        raise ValueError("entry_receipt_header_correlation_required")
    metadata = pool.records[ref]
    if type(metadata) is not bytes or len(metadata) != _BODY_RECORD_BYTES:
        raise ValueError("original_entry_body_enrollment_required")
    # Only this original invocation factory enrolls the header, after the
    # retained pending-reference and complete same-call correlation checks.
    pool.records[ref] = metadata + value_seal(header)
    issuer.pending.pop(value.observation_ref)
    return ref


def _entry_receipt_record(value):
    from ._staging_guard_history import value_seal

    pool = _entry_receipt_pool()
    if type(value) is not EntryObservationReceipt or value not in pool.records:
        raise ValueError("original_entry_receipt_required")
    record = pool.records[value]
    if type(record) is not bytes or len(record) != _BODY_RECORD_BYTES + 32:
        raise ValueError("entry_receipt_changed_or_foreign")
    ref, header_seal, body_seal, affinity = (
        value,
        record[_BODY_RECORD_BYTES:],
        pool.seal(value),
        pool.affinity,
    )
    header = _ENTRY_HEADER_CACHE.get(ref)
    if header is None:
        # Every field already resides in the original sealed body. The bounded
        # cache holds only immutable scalar tuples, never live custody or an
        # externally returned mutable snapshot. Eviction drops no evidence and
        # refunds no capture charge.
        header = _entry_value_header(_entry_receipt_pool().snapshot(ref))
        if value_seal(header) != header_seal:
            raise ValueError("entry_receipt_header_changed")
        if len(_ENTRY_HEADER_CACHE) >= _ENTRY_HEADER_CACHE_LIMIT:
            _ENTRY_HEADER_CACHE.pop(next(iter(_ENTRY_HEADER_CACHE)))
        _ENTRY_HEADER_CACHE[ref] = header
    if value_seal(header) != header_seal:
        raise ValueError("entry_receipt_header_changed")
    return ref, header, header_seal, body_seal, affinity


def validate_confined_entry_receipt(value):
    """IO-free original issuance/integrity check; never admits a filesystem action."""
    _entry_receipt_record(value)
    return value


def confined_entry_receipt_coordinate(value):
    """Original invocation facts only; no IO, renewed observation or authority."""
    _, header, *_ = _entry_receipt_record(value)
    issuer = _entry_invocation_issuer()
    reference = header[1]
    prefix = "entry-observation:" + issuer.generation[:24]
    if (
        type(reference) is not str
        or not reference.startswith(prefix)
        or len(reference) != len(prefix) + 8
    ):
        raise ValueError("original_entry_invocation_coordinate_required")
    ordinal = int(reference[-8:], 16)
    if not 0 < ordinal <= issuer.counter:
        raise ValueError("original_entry_invocation_coordinate_required")
    return issuer.generation, ordinal


def confined_entry_receipt_seal(value):
    _entry_receipt_record(value)
    # Reuse the original immutable complete metadata, not two more digest
    # objects and another tuple for every retained completion occurrence.
    return _entry_receipt_pool().records[value]


def snapshot_confined_entry_receipt(value):
    """Complete detached original field values,not reconstructed live custody."""
    ref, header, *_ = _entry_receipt_record(value)
    returned = _entry_receipt_pool().snapshot(ref)
    if (
        type(returned) is not _ENTRY_RESULT_TYPE
        or _entry_value_header(returned) != header
    ):
        raise ValueError("entry_receipt_snapshot_correlation_required")
    return returned


class ConfinedEntryObservationError(RuntimeError):
    """Original failure prefix/custody; detached values grant no retry rights."""

    def __init__(self, state, cause, descriptor_cleanup, cursor_cleanup):
        super().__init__("filesystem_entry_observation_failed")
        self.request = state.request
        self.request_snapshot = state.snapshot
        self.observation_ref = state.observation_ref
        self.phase = state.phase
        self.code = "filesystem_entry_observation_failed"
        prefix = dict(state.prefix)
        prefix["descriptor_resources"] = (
            state.resource_snapshot[0] if state.resource_snapshot is not None else None
        )
        prefix["cursor_resources"] = (
            state.resource_snapshot[1] if state.resource_snapshot is not None else None
        )
        prefix["resource_evidence_available"] = state.resource_snapshot is not None
        self.observation_prefix = MappingProxyType(prefix)
        self.roster_prefix = tuple(state.roster_prefix)
        self.original_descriptor_cleanup = descriptor_cleanup
        self.cursor_cleanup = cursor_cleanup
        self.original_cause = cause
        self.raw_unrepresentable_name = state.raw_name
        self.original_owner_custody = state
        self.authorizes_retry = False


@dataclass(slots=True)
class _CursorSlot:
    resource_ref: str
    path: str
    cursor: object = None
    acquisition_state: str = "not_acquired"
    spent: bool = False
    closed: bool = False


class _EntryReadLedger(_ReadLedger):
    entry_state: _State | None  # pyright: ignore[reportUninitializedInstanceVariable] - set by the original _State constructor before IO

    def close(self, descriptor):
        super().close(descriptor)
        try:
            owner = self.entry_state
            if owner is None:
                raise ValueError("entry_cleanup_owner_already_settled")
            owner.check()
        except BaseException as error:  # noqa: BLE001 - snapshot drift cannot prevent remaining original cleanup
            self.cleanup_failure(error, "entry_cleanup_snapshot")


class _State:
    def __init__(self, request, *, private_root=None, value_pool=None):
        if value_pool is not None:
            _value_pool(value_pool)
        self.value_pool = value_pool
        self.request = request
        self.snapshot: Any = None
        self.observation_ref = "entry-observation:" + uuid4().hex
        self.descriptors = _EntryReadLedger(private_root=private_root)
        self.descriptors.entry_state = self
        self.cursors = []
        self.cursor_diagnostics = []
        self.cursor_failure = None
        self.cursor_attempts_unknown = False
        self.cursor_context_unknown = False
        self.phase = "validation"
        self.prefix = {}
        self.roster_prefix = []
        self.raw_name = None
        self.last_return = None
        self.resource_snapshot: Any = None
        self.resource_evidence_failure: BaseException | None = None
        self.cursor_cleanup_value: Any = None
        self.descriptor_cleanup_value: Any = None
        self.settlement_error: BaseException | None = None

    def check(self):
        if self.snapshot is not None and _snapshot(self.request) != self.snapshot:
            raise ValueError("entry_request_snapshot_changed")

    def call(self, operation, *args, **kwargs):
        self.check()
        self.descriptors.stage = self.phase
        self.last_return = operation(*args, **kwargs)
        self.check()
        return self.last_return

    def open(self, name, parent=None):
        if len(self.descriptors.resources) >= 65:
            raise ValueError("entry_descriptor_limit")
        descriptor = self.call(
            self.descriptors.open,
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent,
        )
        if self.value_pool is not None:
            row = self.descriptors.resources[-1]
            if row.path is not None:
                row.path = cast(str, _shared_value(self.value_pool, row.path))
        return descriptor

    def cursor_diagnostic(self, error):
        if len(self.cursor_diagnostics) < 16:
            self.cursor_diagnostics.append(
                "cursor_cleanup_unknown:" + _cause_kind(error)
            )
        if self.cursor_failure is None:
            self.cursor_failure = error

    def settle_cursors(self):
        for slot in reversed(self.cursors):
            if slot.cursor is not None and not slot.spent:
                dispatched = returned = False
                try:
                    slot.spent = True
                    dispatched = True
                    slot.cursor.close()
                    returned = True
                    slot.closed = True
                except BaseException as error:  # noqa: BLE001 - spend once and continue distinct original resources
                    object.__setattr__(slot, "spent", True)
                    if returned:
                        object.__setattr__(slot, "closed", True)
                    if not dispatched:
                        self.cursor_attempts_unknown = True
                    self.cursor_diagnostic(error)
                try:
                    self.check()
                except BaseException as error:  # noqa: BLE001 - changed request cannot stop cleanup
                    self.cursor_diagnostic(error)

    def cursor_cleanup(self):
        acquired = (
            None
            if any(row.acquisition_state == "unknown" for row in self.cursors)
            else sum(row.acquisition_state == "acquired" for row in self.cursors)
        )
        attempted = (
            None
            if self.cursor_attempts_unknown
            else sum(row.spent for row in self.cursors)
        )
        closed = (
            None
            if any(row.spent and not row.closed for row in self.cursors)
            else sum(row.closed for row in self.cursors)
        )
        outcome = (
            "unknown"
            if acquired is None
            or closed is None
            or self.cursor_diagnostics
            or self.cursor_context_unknown
            else "closed"
            if acquired
            else "not_acquired"
        )
        return EntryCursorCleanup(
            outcome, acquired, attempted, closed, tuple(self.cursor_diagnostics)
        )


def _settle_cursors(state):
    try:
        state.settle_cursors()
    except BaseException as error:  # noqa: BLE001 - continue only known unspent original rights
        state.cursor_context_unknown = True
        state.cursor_diagnostic(error)
        try:
            state.settle_cursors()
        except BaseException as continuation_error:  # noqa: BLE001 - preserve unresolved custody, never replay a close
            state.cursor_diagnostic(continuation_error)
    try:
        return state.cursor_cleanup()
    except BaseException as error:  # noqa: BLE001 - snapshot failure is not successful cleanup
        state.cursor_context_unknown = True
        state.cursor_diagnostic(error)
        return EntryCursorCleanup(
            "unknown", None, None, None, tuple(state.cursor_diagnostics)
        )


def _snapshot(request):
    if type(request.root) is not type(Path()) or (
        request.path is not None and type(request.path) is not str
    ):
        raise TypeError("exact_entry_path_types_required")
    root = str(request.root)
    _read_root(root)
    if root.startswith("//"):
        raise ValueError("entry_double_root_refused")
    if request.path is not None:
        _saved_read_path(request.path)  # Existing 1024-byte relative bound wins.
    for value, limit in (
        (request.maximum_children, 20000),
        (request.maximum_name_bytes, 4096),
        (request.maximum_roster_bytes, 1048576),
    ):
        if type(value) is not int or not 1 <= value <= limit:
            raise ValueError("invalid_entry_limit")
    coordinate = (
        root if request.path is None else str(PurePosixPath(root) / request.path)
    )
    if (
        len(coordinate.encode("utf-8")) > 4096
        or len(PurePosixPath(coordinate).parts) - 1 > 64
    ):
        raise ValueError("entry_coordinate_limit")
    return EntryRequestSnapshot(
        root,
        request.path,
        request.maximum_children,
        request.maximum_name_bytes,
        request.maximum_roster_bytes,
    )


def _stat(value, pool=None):
    values = tuple(
        _shared_value(pool, item)
        for item in (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_uid,
            value.st_gid,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )
    )
    if pool is not None:
        record = _value_pool(pool)
        if record[3]:
            table = record[4]
            if values in table:
                retained = table[values]
                if type(retained) is not tuple or retained != values:
                    raise ValueError("entry_stat_value_storage_changed")
                values = retained
            else:
                if len(table) >= 128:
                    table.pop(next(iter(table)))
                table[values] = values
            return _PackedEntryStat(values)
    return EntryStat(*values)


def _same(left, right, under):
    return left == right if under else left.values()[:5] == right.values()[:5]


def _named(state, name, parent=None):
    return _stat(
        state.call(os.stat, name, dir_fd=parent, follow_symlinks=False),
        state.value_pool,
    )


def _opened(state, descriptor):
    return _stat(state.call(os.fstat, descriptor), state.value_pool)


def _roster(state, descriptor, ordinal):
    slot = _CursorSlot(
        state.observation_ref + ":cursor:" + str(ordinal), state.prefix["entry_locator"]
    )
    state.cursors.append(slot)  # Reserve before the external acquisition.
    state.check()
    slot.acquisition_state = "unknown"
    cursor = None
    try:
        cursor = os.scandir(descriptor)
        state.last_return = cursor
        if (
            cursor is None
            or not callable(getattr(cursor, "__next__", None))
            or not callable(getattr(cursor, "close", None))
        ):
            raise RuntimeError("entry_cursor_return_invalid")
        slot.cursor = cursor
        slot.acquisition_state = "acquired"
    except BaseException as error:
        if cursor is not None:
            object.__setattr__(slot, "cursor", cursor)
            object.__setattr__(slot, "acquisition_state", "acquired")
        elif isinstance(error, OSError) and error.errno in {
            errno.EBADF,
            errno.ENOENT,
            errno.ENOTDIR,
            errno.EACCES,
            errno.EPERM,
        }:
            slot.acquisition_state = "not_acquired"
        raise
    state.check()
    names = []
    state.roster_prefix = names
    seen = set()
    byte_count = 0
    while True:
        state.check()
        try:
            entry = next(cursor)
        except StopIteration:
            state.check()
            break
        state.last_return = entry
        state.check()
        name = entry.name
        state.check()
        state.raw_name = name
        if (
            type(name) is not str
            or not name
            or name in {".", ".."}
            or "/" in name
            or "\0" in name
        ):
            raise ValueError("invalid_entry_name")
        body = name.encode("utf-8", errors="strict")
        if (
            len(body) > state.snapshot.maximum_name_bytes
            or len(names) >= state.snapshot.maximum_children
            or byte_count + len(body) > state.snapshot.maximum_roster_bytes
        ):
            raise ValueError("entry_roster_limit")
        if name in seen:
            raise ValueError("duplicate_entry_name")
        names.append(name)
        seen.add(name)
        byte_count += len(body)
        state.raw_name = None
    return tuple(sorted(names, key=lambda name: name.encode("utf-8")))


def _acquire_entry_ancestors(state):
    snapshot = state.snapshot
    root_parts = PurePosixPath(snapshot.root).parts[1:]
    relative = () if snapshot.path is None else PurePosixPath(snapshot.path).parts
    ancestors = root_parts + relative[:-1]
    state.phase = "ancestor_acquisition"
    before = _named(state, "/")
    descriptor = state.open("/")
    opened = _opened(state, descriptor)
    rows: list[list[Any]] = [
        ["/", before, opened, None, descriptor, "/", len(root_parts) == 0]
    ]
    state.prefix["ancestors"] = rows
    if not _same(before, opened, len(root_parts) == 0):
        raise ValueError("entry_ancestor_changed")
    root_row = rows[0] if not root_parts else None
    for index, name in enumerate(ancestors, 1):
        parent = descriptor
        coordinate = _shared_value(
            state.value_pool, str(PurePosixPath(rows[-1][0]) / name)
        )
        named = _named(state, name, parent)
        if not stat.S_ISDIR(named.mode):
            raise ValueError("entry_ancestor_not_directory")
        descriptor = state.open(name, parent)
        opened = _opened(state, descriptor)
        under = index >= len(root_parts)
        rows.append([coordinate, named, opened, parent, descriptor, name, under])
        if not _same(named, opened, under):
            raise ValueError("entry_ancestor_changed")
        if index == len(root_parts):
            root_row = rows[-1]
    assert root_row is not None
    return rows, descriptor, root_row, relative


def _observe(state):
    snapshot = state.snapshot
    if state.descriptors.private_root is None:
        rows, descriptor, root_row, relative = _acquire_entry_ancestors(state)
    else:
        # The original read ledger duplicates the genuine retained private root,
        # rather than walking to a same-spelled pathname. Only flat/root reads
        # belong to this internal join; the original public walk stays intact.
        if snapshot.path is not None and "/" in snapshot.path:
            raise ValueError("private_entry_flat_required")
        state.phase = "ancestor_acquisition"
        before = _named(state, snapshot.root)
        descriptor = state.open(snapshot.root)
        opened = _opened(state, descriptor)
        if before != opened:
            raise ValueError("entry_ancestor_changed")
        rows = [[snapshot.root, before, opened, None, descriptor, snapshot.root, True]]
        root_row = rows[0]
        relative = () if snapshot.path is None else (snapshot.path,)
        state.prefix["ancestors"] = rows
    state.prefix["root_before"] = root_row[1]
    state.phase = "entry_observation"
    leaf = relative[-1] if relative else None
    entry_locator = (
        snapshot.root
        if leaf is None
        else str(PurePosixPath(snapshot.root) / cast(str, snapshot.path))
    )
    state.prefix["entry_locator"] = entry_locator
    entry_before = (
        _opened(state, descriptor) if leaf is None else _named(state, leaf, descriptor)
    )
    state.prefix["entry_before"] = entry_before
    kind = (
        "directory"
        if stat.S_ISDIR(entry_before.mode)
        else "file"
        if stat.S_ISREG(entry_before.mode)
        else "symlink"
        if stat.S_ISLNK(entry_before.mode)
        else None
    )
    if kind is None:
        raise ValueError("unsupported_entry_kind")
    state.prefix.update(
        kind=kind,
        opened_directory=None,
        children_before=None,
        children_after=None,
        link_text=None,
    )
    if kind == "directory":
        directory = descriptor if leaf is None else state.open(leaf, descriptor)
        opened = _opened(state, directory)
        state.prefix["opened_directory"] = opened
        if opened != entry_before:
            raise ValueError("entry_directory_changed")
        for ordinal, key in enumerate(("children_before", "children_after")):
            state.phase = "roster_" + str(ordinal)
            state.prefix[key] = _roster(state, directory, ordinal)
        if (
            state.prefix["children_before"] != state.prefix["children_after"]
            or _opened(state, directory) != opened
        ):
            raise ValueError("entry_directory_changed")
    elif kind == "symlink":
        state.phase = "readlink"
        text = state.call(os.readlink, leaf, dir_fd=descriptor)
        state.raw_name = text
        if (
            type(text) is not str
            or not 0
            < len(text.encode("utf-8", errors="strict"))
            <= snapshot.maximum_name_bytes
        ):
            raise ValueError("entry_link_text_invalid")
        state.prefix["link_text"] = text
        state.raw_name = None
    state.phase = "bookends"
    entry_after = (
        _opened(state, descriptor) if leaf is None else _named(state, leaf, descriptor)
    )
    state.prefix["entry_after"] = entry_after
    if entry_after != entry_before:
        raise ValueError("entry_changed")
    bookends = []
    for coordinate, named, opened, parent, fd, name, under in reversed(rows):
        named_after = _named(state, name, parent)
        opened_after = _opened(state, fd)
        if (
            not _same(named, named_after, under)
            or not _same(opened, opened_after, under)
            or not _same(named_after, opened_after, under)
        ):
            raise ValueError("entry_ancestor_changed")
        bookends.append(
            EntryAncestorBookends(
                coordinate, named, opened, named_after, opened_after, under
            )
        )
        if coordinate == snapshot.root:
            state.prefix["root_after"] = named_after
    state.prefix["ancestor_bookends"] = tuple(reversed(bookends))


def _resource_rows(state):
    descriptors = tuple(
        EntryResource(
            row.resource_ref,
            row.kind,
            row.path,
            row.acquisition_state,
            row.spent,
            True
            if row.closed
            else None
            if row.spent or row.acquisition_state == "unknown"
            else False,
        )
        for row in state.descriptors.resources
    )
    cursors = tuple(
        EntryResource(
            row.resource_ref,
            "directory_cursor",
            row.path,
            row.acquisition_state,
            row.spent,
            True
            if row.closed
            else None
            if row.spent or row.acquisition_state == "unknown"
            else False,
        )
        for row in state.cursors
    )
    return descriptors, cursors


def _settle_entry_resources(state):
    """Preserve completed carriers; continuation drains only original unspent rights."""
    try:
        if state.cursor_cleanup_value is None:
            state.cursor_cleanup_value = _settle_cursors(state)
    except BaseException as error:  # noqa: BLE001 - unavailable cursor evidence cannot skip descriptor settlement
        state.cursor_context_unknown = True
        state.settlement_error = state.settlement_error or error
    finally:
        if state.descriptor_cleanup_value is None:
            try:
                state.descriptor_cleanup_value = _settle_confined_read_ledger(
                    state.descriptors
                )
            except BaseException as error:  # noqa: BLE001 - retain original custody if cleanup materialization is unavailable
                state.descriptors.cleanup_failure(
                    error, "entry_cleanup_evidence_unknown"
                )
                state.descriptors.close_unspent()
                state.settlement_error = state.settlement_error or error


def observe_confined_entry_with_cleanup(
    *,
    root: Path,
    path: str | None = None,
    maximum_children: int = 20000,
    maximum_name_bytes: int = 4096,
    maximum_roster_bytes: int = 1048576,
    _private_root=None,
    _value_pool=None,
    _receipt_profile=None,
) -> ConfinedEntryObservation | EntryObservationReceipt:
    """Observe one original entry; observed agreement is not continuous exclusion."""
    request = ConfinedEntryRequest(
        root, path, maximum_children, maximum_name_bytes, maximum_roster_bytes
    )
    state = (
        _State(request)
        if _private_root is None and _value_pool is None
        else _State(request, private_root=_private_root, value_pool=_value_pool)
    )
    primary = None
    failed_phase = "validation"
    reserved_invocation = None
    try:
        try:
            state.snapshot = _snapshot(state.request)
            if _receipt_profile is not None and (
                type(_receipt_profile) is not str
                or _receipt_profile != OBSERVATION_RECEIPT_PROFILE
            ):
                raise ValueError("explicit_entry_receipt_profile_required")
            if sys.platform != "linux" or not all(
                hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
            ):
                raise ValueError("secure_entry_observation_unavailable")
            if _receipt_profile is not None:
                reserved_invocation = _reserve_entry_invocation(state)
            _observe(state)
        except BaseException as error:  # noqa: BLE001 - preserve primary failure before the independent settlement boundary
            primary, failed_phase = error, state.phase
        finally:
            _settle_entry_resources(state)
    except BaseException as error:  # noqa: BLE001 - interruption at the observation/settlement boundary still drains original custody
        if primary is None:
            primary, failed_phase = error, "cleanup"
        state.settlement_error = state.settlement_error or error
        try:
            _settle_entry_resources(state)
        except BaseException as continuation_error:  # noqa: BLE001 - no infallible progress under repeated interruption claim
            state.descriptors.cleanup_failure(
                continuation_error, "entry_settlement_boundary_unknown"
            )
    cursor_cleanup = state.cursor_cleanup_value
    descriptor_cleanup = state.descriptor_cleanup_value
    if primary is None and (
        descriptor_cleanup is None
        or cursor_cleanup is None
        or descriptor_cleanup.outcome != "closed"
        or cursor_cleanup.outcome == "unknown"
    ):
        primary = (
            state.settlement_error
            or state.cursor_failure
            or state.descriptors.first_cleanup_error
            or RuntimeError("entry_cleanup_unverified")
        )
        failed_phase = "cleanup"
    if primary is None:
        state.phase = "result"
    try:
        state.resource_snapshot = _resource_rows(state)
        state.check()
        if primary is None:
            state.phase = "result"
            descriptors, cursors = state.resource_snapshot
            prefix = state.prefix
            # Capture every same-call fact before invoking the result factory.
            # A self-consistent replacement is not the original observation.
            expected = (
                state.snapshot,
                state.observation_ref,
                state.snapshot.root,
                state.snapshot.path,
                prefix["root_before"],
                prefix["root_after"],
                prefix["ancestor_bookends"],
                prefix["entry_before"],
                prefix["entry_after"],
                prefix["opened_directory"],
                prefix["kind"],
                prefix["children_before"],
                prefix["children_after"],
                prefix["link_text"],
                cast(ConfinedFileReadCleanup, descriptor_cleanup),
                cast(EntryCursorCleanup, cursor_cleanup),
                descriptors,
                cursors,
                "entry_metadata_observed",
                False,
                False,
            )
            expected_seal = None
            receipt_value_seal = None
            if _receipt_profile is not None:
                from ._staging_guard_history import value_seal

                receipt_value_seal = value_seal
                expected_seal = value_seal(expected)
            result = ConfinedEntryObservation(*expected)
            if type(result) is not _ENTRY_RESULT_TYPE:
                raise TypeError("original_entry_result_required")
            _ENTRY_RESULT_TYPE.__post_init__(result)
            if (
                tuple(
                    getattr(result, field.name) for field in fields(_ENTRY_RESULT_TYPE)
                )
                != expected
            ):
                raise ValueError("entry_result_owner_correlation_failed")
            state.check()
            if _receipt_profile is not None:
                if (
                    receipt_value_seal is None
                    or receipt_value_seal(
                        tuple(
                            getattr(result, field.name)
                            for field in fields(_ENTRY_RESULT_TYPE)
                        )
                    )
                    != expected_seal
                ):
                    raise ValueError("entry_receipt_source_fields_changed")
                result = _capture_entry_receipt(result)
            # All original resources are settled and their complete carriers
            # have passed receiving. This callback backlink is computational
            # custody,not returned history. Failed/uncertain attempts keep it.
            # Avoid retaining a closed state/ledger cycle until cyclic GC.
            state.descriptors.entry_state = None
            return result
    except BaseException as error:  # noqa: BLE001 - post-cleanup construction cannot erase original observations
        state.resource_evidence_failure = error
        if primary is None:
            primary, failed_phase = error, state.phase
    if reserved_invocation is not None:
        issuer, reference = reserved_invocation
        issuer.pending.pop(reference, None)
    state.phase = failed_phase
    try:
        failure = ConfinedEntryObservationError(
            state, primary, descriptor_cleanup, cursor_cleanup
        )
    except BaseException as construction_error:
        construction_error.original_owner_custody = state  # pyright: ignore[reportAttributeAccessIssue] - original exception fallback has dynamic owner evidence
        construction_error.original_cause = primary  # pyright: ignore[reportAttributeAccessIssue] - preserve the original cause if failure construction itself fails
        raise construction_error from primary
    raise failure from primary


def _observe_private_entry_with_cleanup(
    *, private_root, maximum_children, maximum_name_bytes, maximum_roster_bytes
):
    """Internal original-owner join; a detached root coordinate is insufficient."""
    return observe_confined_entry_with_cleanup(
        root=private_root.root,
        maximum_children=maximum_children,
        maximum_name_bytes=maximum_name_bytes,
        maximum_roster_bytes=maximum_roster_bytes,
        _private_root=private_root,
    )
