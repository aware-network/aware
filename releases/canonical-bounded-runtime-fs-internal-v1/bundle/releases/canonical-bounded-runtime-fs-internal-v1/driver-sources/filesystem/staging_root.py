"""Original cooperative POSIX staging-root custody and child-release boundary.

The original ledger owns acquisitions and once-only closes. Creation uses the
shared original mkdir primitive. Bookends observe cooperative topology, not
hostile same-UID exclusion or kernel-attributed creation identity.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
import threading
from dataclasses import dataclass, field, fields
from uuid import uuid4
from weakref import WeakKeyDictionary

from . import _staging_guard_history as history
from . import confined_mutation as physical
from . import retained_mutation as retained
from . import staging_partitioned_plan as metadata

PROFILE = "aware.filesystem.cooperative-posix-staging.v1"
RETAINED_DIRECTORY_PROFILE = "aware.filesystem.retained-directory-staging.v1"
RETIRED_MEMBER_PROFILE = "aware.filesystem.retired-member-staging.v1"
MAX_RETAINED_DIRECTORIES = 4096


@dataclass(frozen=True, slots=True)
class StagingRootEvidence:
    generation: str
    request_digest: str
    plan_digest: str
    phase: str
    creation: str
    root_identity: tuple | None
    root_sync: str
    parent_sync: str
    resources: tuple
    original_returns: tuple | history.RecordedHistory
    original_errors: tuple
    release_spent: bool
    cleanup: str
    capture_complete: bool
    active_child_ref: str | None
    child_terminals: tuple
    member_profile: str | None


class StagingRootRefusal(RuntimeError):
    def __init__(self, code, handle=None, state=None, cause=None):
        super().__init__(code)
        self.code = code
        self.handle = handle
        self.original_cause = cause
        self.original_state = state
        self.evidence = _evidence(state) if state is not None else None


class StagingRoot:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use prepare_stage")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Staging root cannot be subclassed")

    def __copy__(self):
        raise TypeError("Staging root cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Staging root cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Staging root cannot be serialized")


@dataclass(frozen=True, slots=True)
class StagingRootPreparation:
    handle: StagingRoot
    request_digest: str
    plan_digest: str


@dataclass
class _State:
    root: str
    operation: str
    namespace: str
    plan: metadata.PartitionedStagingPlan
    plan_seal: tuple
    request_digest: str
    plan_digest: str
    generation: str = field(default_factory=lambda: uuid4().hex)
    pid: int = field(default_factory=os.getpid)
    thread: int = field(default_factory=threading.get_ident)
    phase: str = "prepared"
    ledger: physical._ReadLedger = field(default_factory=physical._ReadLedger)
    # (retained parent fd, name, retained child fd, observed identity).
    parents: list = field(default_factory=list)
    root_fd: int | None = None
    root_identity: tuple | None = None
    creation: str = "not_attempted"
    root_sync: str = "not_attempted"
    parent_sync: str = "not_attempted"
    returns: list | history.GuardHistory = field(default_factory=list)
    errors: list = field(default_factory=list)
    release_spent: bool = False
    cleanup: str = "not_released"
    busy: bool = False
    capture_complete: bool = True
    lock: object = field(default_factory=threading.RLock)
    active_child: object = None
    child_terminals: list = field(default_factory=list)
    next_coordinate: tuple[int, int] = (0, 0)
    completed_entries: dict = field(default_factory=dict)
    member_profile: str | None = None
    history_profile: str | None = None
    history_pool: history.HistoryPool | None = None
    # Genuine root-ledger resources, borrowed by serial children. No eviction
    # or close-right transfer; explicit root release settles them once.
    retained_directories: dict = field(default_factory=dict)
    retired_members: dict = field(default_factory=dict)
    live_guard_capture: list | None = None
    live_guard_groups: list = field(default_factory=list)
    live_guard_results: list = field(default_factory=list)


_HANDLES = WeakKeyDictionary()
# Unreleased custody survives a dropped caller handle; no implicit finalizer,
# deletion or capacity refund. This cut does not qualify whole-attempt memory.
_CUSTODY = {}


def _plan_seal(plan):
    if (
        type(plan) is not metadata.PartitionedStagingPlan
        or type(plan.groups) is not tuple
        or not 1 <= len(plan.groups) <= metadata.MAX_GROUPS
    ):
        raise ValueError("original_partitioned_plan_required")
    if any(
        type(group) is not metadata.StagingPlanGroup
        or type(group.namespace) is not str
        or type(group.partitions) is not tuple
        or not 1 <= len(group.partitions) <= metadata.MAX_PARTITIONS
        for group in plan.groups
    ):
        raise ValueError("original_staging_groups_required")
    return tuple(
        (group.namespace, tuple(metadata._snapshot(p) for p in group.partitions))
        for group in plan.groups
    )


_LIMIT_FIELDS = tuple(
    value.name for value in fields(metadata.original.StagingPlanLimits)
)


def _plan_matches(plan, seal):
    """Compare original declared fields in place, without another plan graph.

    Preparation still captures and validates the complete original seal. This
    is a currentness guard, not a validator, admission or retained projection.
    """
    original = metadata.original
    if (
        type(plan) is not metadata.PartitionedStagingPlan
        or type(plan.groups) is not tuple
        or len(plan.groups) != len(seal)
    ):
        return False
    for ordinal, group in enumerate(plan.groups):
        name, partitions = seal[ordinal]
        if (
            type(group) is not metadata.StagingPlanGroup
            or type(group.namespace) is not str
            or group.namespace != name
            or type(group.partitions) is not tuple
            or len(group.partitions) != len(partitions)
        ):
            return False
        for index, partition in enumerate(group.partitions):
            limits, rows = partitions[index]
            if (
                type(partition) is not original.StagingPlan
                or type(partition.limits) is not original.StagingPlanLimits
                or type(partition.members) is not tuple
                or len(partition.members) != len(rows)
            ):
                return False
            for number, field_name in enumerate(_LIMIT_FIELDS):
                value = getattr(partition.limits, field_name)
                if type(value) is not int or value != limits[number]:
                    return False
            for member_index, member in enumerate(partition.members):
                pin = rows[member_index]
                if (
                    type(member)
                    is not (
                        original.StagingDirectory
                        if pin[0] == "directory"
                        else original.StagingFile
                    )
                    or type(member.path) is not str
                    or member.path != pin[1]
                    or type(member.mode) is not int
                    or member.mode != pin[2]
                ):
                    return False
                if pin[0] == "file" and (
                    type(member) is not original.StagingFile
                    or type(member.size_bytes) is not int
                    or member.size_bytes != pin[3]
                    or type(member.content_digest) is not str
                    or member.content_digest != pin[4]
                ):
                    return False
    return True


def _captured_plan(seal):
    return metadata.PartitionedStagingPlan(
        tuple(
            metadata.StagingPlanGroup(
                name, tuple(metadata._captured_plan(p) for p in parts)
            )
            for name, parts in seal
        )
    )


def _text(value, maximum):
    if type(value) is not str or not value or len(value) > maximum:
        raise ValueError("bounded_exact_text_required")
    physical._read_text(value, maximum)


def prepare_stage(
    *,
    profile,
    absolute_root,
    operation_ref,
    partitioned_plan,
    group_namespace,
    history_profile=None,
    stat_block_storage=False,
):
    """Pure preparation. Neither root existence nor physical capacity observed."""
    try:
        if type(profile) is not str or profile != PROFILE:
            raise ValueError("unsupported_staging_root_profile")
        if history_profile is not None and (
            type(history_profile) is not str
            or history_profile
            not in (
                history.PROFILE,
                history.COMPRESSED_PROFILE,
                RETAINED_DIRECTORY_PROFILE,
                RETIRED_MEMBER_PROFILE,
            )
        ):
            raise ValueError("unsupported_staging_history_profile")
        if type(stat_block_storage) is not bool or (
            stat_block_storage and history_profile != RETIRED_MEMBER_PROFILE
        ):
            raise ValueError("explicit_retired_stat_block_storage_required")
        _text(absolute_root, 4096)
        parts = absolute_root.split("/")
        if (
            not absolute_root.startswith("/")
            or any(p in ("", ".", "..") for p in parts[1:])
            or len(parts) - 1 > 64
            or "\\" in absolute_root
        ):
            raise ValueError("canonical_absolute_root_required")
        _text(operation_ref, 256)
        _text(group_namespace, 64)
        seal = _plan_seal(partitioned_plan)
        captured = _captured_plan(seal)
        summary = metadata.validate_partitioned_staging_plan(
            captured, profile=metadata.StagingMetadataProfile.TWO_GROUP_PARTITIONED_V1
        )
        if seal != _plan_seal(partitioned_plan) or seal != _plan_seal(captured):
            raise ValueError("staging_plan_changed")
        if group_namespace not in tuple(row[0] for row in seal):
            raise ValueError("staging_group_missing")
        declaration = [
            PROFILE,
            absolute_root,
            operation_ref,
            group_namespace,
            summary.plan_digest,
        ]
        if history_profile is not None:
            declaration.append(history_profile)
        if stat_block_storage:
            declaration.append("original_stat_blocks_32k_v1")
        body = json.dumps(
            declaration,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()
        digest = "sha256:" + hashlib.sha256(body).hexdigest()
        state = _State(
            absolute_root,
            operation_ref,
            group_namespace,
            partitioned_plan,
            seal,
            digest,
            summary.plan_digest,
        )
        if history_profile is not None:
            state.history_profile = history_profile
            state.history_pool = history.HistoryPool(
                compressed=history_profile
                in (
                    history.COMPRESSED_PROFILE,
                    RETAINED_DIRECTORY_PROFILE,
                    RETIRED_MEMBER_PROFILE,
                ),
                low_memory_encoding=history_profile
                in (RETAINED_DIRECTORY_PROFILE, RETIRED_MEMBER_PROFILE),
                packed_stat_storage=history_profile == RETIRED_MEMBER_PROFILE,
                stat_block_storage=stat_block_storage,
            )
            state.returns = history.GuardHistory(state.history_pool)
        handle = object.__new__(StagingRoot)
        _HANDLES[handle] = state
        _CUSTODY[id(state)] = state
        return StagingRootPreparation(handle, digest, summary.plan_digest)
    except BaseException as cause:
        raise StagingRootRefusal(
            "staging_root_preparation_refused", cause=cause
        ) from cause


def _require(handle):
    if type(handle) is not StagingRoot or handle not in _HANDLES:
        raise StagingRootRefusal("original_staging_root_required")
    state = _HANDLES[handle]
    if state.pid != os.getpid() or state.thread != threading.get_ident():
        raise StagingRootRefusal("staging_root_execution_mismatch", handle, state)
    if state.busy:
        raise StagingRootRefusal("staging_root_reentrant", handle, state)
    return state


def _identity(value):
    return (
        value.st_dev,
        value.st_ino,
        stat.S_IFMT(value.st_mode),
        value.st_uid,
        value.st_gid,
        stat.S_IMODE(value.st_mode),
    )


def _observed(state, label, function, *args, **kwargs):
    value = function(*args, **kwargs)
    live = getattr(state, "live_guard_capture", None)
    if live is not None:
        live.append(value)
    state.returns.append((label, value))
    return value


def _observe_live_bookends(state):
    """Retain actual current syscall returns,never decode recorded history."""
    if state.live_guard_capture is not None:
        raise ValueError("staging_live_guard_reentrant")
    values = []
    state.live_guard_groups.append(values)  # Also survives failed bookends.
    state.live_guard_capture = values
    try:
        _bookends(state)
    finally:
        state.live_guard_capture = None
    returned = tuple(values)
    state.live_guard_results.append((returned, tuple(id(value) for value in returned)))
    return returned


def _validate_live_bookends(state, returned):
    """IO-free original-owner correlation,not decoded-history promotion."""
    for value, seal in state.live_guard_results:
        if value is returned and tuple(id(item) for item in returned) == seal:
            return returned
    raise ValueError("original_live_staging_bookends_required")


def _directory_identity(state, descriptor):
    value = _observed(state, "fstat", os.fstat, descriptor)
    if not stat.S_ISDIR(value.st_mode):
        raise ValueError("staging_directory_required")
    return _identity(value)


def _bookends(state):
    for parent, name, child, expected in state.parents:
        if _directory_identity(state, child) != expected:
            raise ValueError("staging_parent_changed")
        if (
            parent is not None
            and _identity(
                _observed(
                    state,
                    "parent_stat",
                    os.stat,
                    name,
                    dir_fd=parent,
                    follow_symlinks=False,
                )
            )
            != expected
        ):
            raise ValueError("staging_parent_name_changed")
    if state.root_fd is not None:
        parent = state.parents[-1][2]
        named = _observed(
            state,
            "root_stat",
            os.stat,
            state.root.rsplit("/", 1)[1],
            dir_fd=parent,
            follow_symlinks=False,
        )
        if (
            _identity(named) != state.root_identity
            or _directory_identity(state, state.root_fd) != state.root_identity
        ):
            raise ValueError("staging_root_changed")


def admit_stage(
    prepared, *, expected_request_digest, expected_plan_digest, explicit_create_intent
):
    """One original create attempt. A refusal retains its handle and resources."""
    state = _require(prepared)
    with state.lock:
        if state.phase != "prepared":
            raise StagingRootRefusal("staging_root_admission_spent", prepared, state)
        if (
            type(explicit_create_intent) is not bool
            or not explicit_create_intent
            or type(expected_request_digest) is not str
            or type(expected_plan_digest) is not str
            or expected_request_digest != state.request_digest
            or expected_plan_digest != state.plan_digest
        ):
            raise StagingRootRefusal("staging_root_intent_mismatch", prepared, state)
        state.phase, state.busy = "admission_spent", True
        try:
            if _plan_seal(state.plan) != state.plan_seal:
                raise ValueError("staging_plan_changed")
            if not all(
                hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
            ):
                raise ValueError("staging_posix_profile_unavailable")
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            parent = state.ledger.open("/", flags)
            state.parents.append(
                (None, "/", parent, _directory_identity(state, parent))
            )
            parts = state.root.split("/")[1:]
            for name in parts[:-1]:
                child = state.ledger.open(name, flags, dir_fd=parent)
                state.parents.append(
                    (parent, name, child, _directory_identity(state, child))
                )
                parent = child
            _bookends(state)
            try:
                _observed(
                    state,
                    "absent_stat",
                    os.stat,
                    parts[-1],
                    dir_fd=parent,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            else:
                raise ValueError("staging_root_already_exists")
            state.creation = "unknown"
            try:
                _observed(
                    state,
                    "mkdir",
                    retained._mkdir_explicit,
                    parts[-1],
                    mode=0o700,
                    dir_fd=parent,
                )
            except FileExistsError:
                state.creation = "none"
                raise
            state.creation = "applied"
            named = _observed(
                state,
                "created_stat",
                os.stat,
                parts[-1],
                dir_fd=parent,
                follow_symlinks=False,
            )
            expected = _identity(named)
            state.root_fd = state.ledger.open(parts[-1], flags, dir_fd=parent)
            opened_identity = _directory_identity(state, state.root_fd)
            if (
                opened_identity != expected
                or expected[2] != stat.S_IFDIR
                or expected[3] != os.geteuid()
                or expected[5] != 0o700
            ):
                raise ValueError("staging_root_creation_bookend_mismatch")
            state.root_identity = opened_identity
            _bookends(state)
            for fd, field_name in (
                (state.root_fd, "root_sync"),
                (parent, "parent_sync"),
            ):
                setattr(state, field_name, "unknown")
                value = _observed(state, field_name, os.fsync, fd)
                if value is not None:
                    raise ValueError("staging_sync_return_invalid")
                setattr(state, field_name, "confirmed")
            _bookends(state)
            if _plan_seal(state.plan) != state.plan_seal:
                raise ValueError("staging_plan_changed")
            state.phase = "created"
            return prepared, _evidence(state)
        except BaseException as cause:
            state.phase = "failed"
            state.errors.append(cause)
            raise StagingRootRefusal(
                "staging_root_admission_failed", prepared, state, cause
            ) from cause
        finally:
            state.busy = False


def _evidence(state):
    return StagingRootEvidence(
        state.generation,
        state.request_digest,
        state.plan_digest,
        state.phase,
        state.creation,
        state.root_identity,
        state.root_sync,
        state.parent_sync,
        tuple(
            (r.resource_ref, r.kind, r.path, r.acquisition_state, r.spent, r.closed)
            for r in state.ledger.resources
        ),
        history.snapshot_returns(state.returns),
        tuple(state.errors),
        state.release_spent,
        state.cleanup,
        state.capture_complete
        and (
            type(state.returns) is not history.GuardHistory
            or state.returns.failure is None
        ),
        None if state.active_child is None else state.active_child.generation,
        tuple(state.child_terminals),
        state.member_profile,
    )


def observe_staging_root(handle):
    """IO-free retained evidence, not validation or renewed authority."""
    return _evidence(_require(handle))


def validate_staging_root_binding(
    handle,
    *,
    expected_absolute_root,
    expected_operation_ref,
    expected_partitioned_plan,
    expected_group_namespace,
):
    """IO-free binding check against original custody,not returned coordinates.

    No preparation,enrollment,admission,guard refresh or cleanup occurs. This
    validates the retained request binding,not current files or completion.
    Mismatches preserve the genuine state's effects and outstanding rights.
    """
    state = _require(handle)
    with state.lock:
        try:
            if (
                type(expected_absolute_root) is not str
                or expected_absolute_root != state.root
                or type(expected_operation_ref) is not str
                or expected_operation_ref != state.operation
                or type(expected_group_namespace) is not str
                or expected_group_namespace != state.namespace
                or expected_partitioned_plan is not state.plan
                or _plan_seal(expected_partitioned_plan) != state.plan_seal
            ):
                raise ValueError("original_staging_root_binding_mismatch")
            return _evidence(state)
        except BaseException as cause:
            raise StagingRootRefusal(
                "staging_root_binding_refused", handle, state, cause
            ) from cause


def release_stage(handle):
    """Dispose only original root resources once; never remove created paths."""
    state = _require(handle)
    with state.lock:
        if state.active_child is not None:
            raise StagingRootRefusal("staging_root_child_unresolved", handle, state)
        if state.release_spent:
            raise StagingRootRefusal("staging_root_release_spent", handle, state)
        state.release_spent, state.busy = True, True
        state.phase, state.cleanup = "release_spent", "unknown"
        try:
            settled = _settle_owned_resources(state)
            state.cleanup = "confirmed" if settled else "unknown"
            state.phase = "released" if settled else "release_unknown"
            if settled:
                _CUSTODY.pop(id(state), None)
            return _evidence(state)
        except BaseException as cause:
            state.errors.append(cause)
            state.phase = "release_unknown"
            state.capture_complete = False
            raise StagingRootRefusal(
                "staging_root_release_failed", handle, state, cause
            ) from cause
        finally:
            state.busy = False


def _borrow_directory(parent, borrower, *, path, parent_fd, name, expected):
    """Borrow original root custody; retain fresh guards and child attribution."""
    if (
        parent.history_profile
        not in (RETAINED_DIRECTORY_PROFILE, RETIRED_MEMBER_PROFILE)
        or parent.active_child is not borrower
        or parent.release_spent
        or parent.root_fd is None
        or parent.pid != os.getpid()
        or parent.thread != threading.get_ident()
    ):
        raise ValueError("original_directory_borrow_unavailable")
    completed = parent.completed_entries.get(path)
    if completed is None or completed[0][0] != "directory" or completed[1] != expected:
        raise ValueError("completed_directory_binding_required")
    retained = parent.retained_directories.get(path)
    if retained is None:
        if len(parent.retained_directories) >= MAX_RETAINED_DIRECTORIES:
            raise ValueError("retained_directory_limit_exceeded")
        fd = parent.ledger.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        resource = parent.ledger.resources[-1]
        row = (parent_fd, name, fd, expected)
        # Ledger custody precedes this fallible publication. An interrupted
        # insertion fails the current child; it cannot manufacture another right.
        parent.retained_directories[path] = (row, resource)
    else:
        row, resource = retained
        if row[:2] != (parent_fd, name) or row[3] != expected:
            raise ValueError("retained_directory_binding_changed")
        fd = row[2]
    if (
        not any(resource is value for value in parent.ledger.resources)
        or resource.descriptor != fd
        or resource.acquisition_state != "acquired"
        or resource.spent
        or resource.closed
    ):
        raise ValueError("retained_directory_custody_changed")
    opened = _observed(borrower, "parent_acquired", os.fstat, fd)
    named = _observed(
        borrower,
        "parent_borrow_named",
        os.stat,
        name,
        dir_fd=parent_fd,
        follow_symlinks=False,
    )
    if _identity(opened) != expected or _identity(named) != expected:
        raise ValueError("completed_parent_changed")
    return row


def _validate_closed_resources(state, *, ledger=None):
    ledger = state.ledger if ledger is None else ledger
    # Validate original returned closes without dispatching more disposal.
    for row in ledger.resources:
        if row.descriptor is not None and row.closed:
            try:
                _observed(state, "close_probe", os.fstat, row.descriptor)
            except OSError as error:
                if (
                    type(state.returns) is history.GuardHistory
                    and error.errno == errno.EBADF
                ):
                    state.returns.append_closed_probe(row.descriptor, error)
                else:
                    state.returns.append(("close_probe_error", error))
                if error.errno != errno.EBADF:
                    state.errors.append(error)
                    ledger.release_unknown = True
            else:
                ledger.release_unknown = True
    if ledger.first_cleanup_error is not None:
        state.errors.append(ledger.first_cleanup_error)
        state.capture_complete = False


def _ledger_settled(ledger):
    return (
        not ledger.acquisition_unknown
        and not ledger.release_unknown
        and not ledger.context_unknown
        and not ledger.attempts_unknown
        and all(
            r.acquisition_state == "not_acquired" or r.closed for r in ledger.resources
        )
    )


def _settle_owned_resources(state, *, ledger=None):
    """Shared original root/member settlement; never repeat a spent close."""
    ledger = state.ledger if ledger is None else ledger
    ledger.close_unspent()
    _validate_closed_resources(state, ledger=ledger)
    return _ledger_settled(ledger)
