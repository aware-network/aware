"""Original namespace custody and observations, not journal/write authority.

Explicit arming spends the original epoch write and sync once. The original
child validates this retained claim at each ordinal; observations grant no rights.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import threading
import weakref
from dataclasses import dataclass, field, fields, replace
from typing import Any
from uuid import uuid4

from . import confined_entry as entry
from . import confined_mutation as native
from . import cooperative_source as source
from . import private_namespace_values as values
from . import retained_file_sequence as sequences
from .confined_mutation import ConfinedFileMutationRequest, ConfinedMutationProfile
from .private_directory import (
    PrivateDirectoryBinding,
    PrivateFileReadResult,
    RetainedPrivateDirectory,
    RetainedPrivateFileSequence,
)
from .private_namespace_values import (
    PrivateNamespaceCleanup,
    PrivateNamespaceControlObservation,
    PrivateNamespaceFootprint,
    PrivateNamespaceInventoryObservation,
    PrivateNamespaceLimits,
    PrivateNamespaceTransactionObservation,
)
from .retained_file_sequence import ConfinedSequenceLimits

_owner_module: Any = None
_PORTS: dict[str, tuple[Any, Any, Any]] = {}
_TYPES: dict[str, type] = {}
_SOURCE = {
    name: (getattr(source, name), getattr(source, name).__code__)
    for name in (
        "_lock",
        "_unlock",
        "_epoch",
        "_validate_control_info",
        "_parse_epoch_body",
        "_write_epoch",
        "_sync_epoch",
    )
}
_LEDGER = native._ReadLedger
_LEDGER_METHODS = {
    name: (getattr(_LEDGER, name), getattr(_LEDGER, name).__code__)
    for name in ("open", "close", "close_all", "close_unspent")
}
_ENTRY_PORTS = {
    name: (getattr(entry, name), getattr(entry, name).__code__)
    for name in (
        "_observe_private_entry_with_cleanup",
        "observe_confined_entry_with_cleanup",
        "_observe",
        "_roster",
    )
}
_ENTRY_ERROR = entry.ConfinedEntryObservationError
_NATIVE_PORTS = {
    name: (getattr(sequences, name), getattr(sequences, name).__code__)
    for name in ("_issued", "_release_state", "_observation")
}


def _owner():
    global _owner_module
    if _owner_module is None:
        owner = importlib.import_module("aware_file_system.private_directory")
        for name in (
            "_original_directory",
            "validate_private_directory",
            "observe_private_directory_file",
            "private_directory_value_to_payload",
            "_auth",
            "_retained_evidence",
            "retain_private_file_sequence",
            "_original_private_sequence",
            "_cleanup_private_sequence",
            "_safe_directory_observation",
            "_private_sequence_reservation",
            "verify_private_file_sequence",
        ):
            operation = getattr(owner, name)
            _PORTS[name] = (owner, operation, operation.__code__)
        _TYPES.update({kind.__name__: kind for kind in owner._SCHEMAS})
        _owner_module = owner
    return _owner_module


def _port(name):
    _owner()
    owner, operation, code = _PORTS[name]
    if getattr(owner, name) is not operation or operation.__code__ is not code:
        raise _Fault("namespace_owner_changed")
    return operation


def _source(name, *, cleanup=False):
    for key, (operation, code) in _SOURCE.items():
        if operation.__code__ is not code or (
            not cleanup and getattr(source, key) is not operation
        ):
            raise _Fault("namespace_source_changed")
    return _SOURCE[name][0]


def _owned_port(name):
    # Original cleanup rights survive export substitution, not code mutation.
    _, operation, code = _PORTS[name]
    if operation.__code__ is not code:
        raise _Fault("namespace_owner_changed")
    return operation


def _native_port(name):
    operation, code = _NATIVE_PORTS[name]
    if operation.__code__ is not code:
        raise _Fault("namespace_native_owner_changed")
    return operation


def _ledger_check():
    if native._ReadLedger is not _LEDGER:
        raise _Fault("namespace_ledger_changed")
    for name, (operation, code) in _LEDGER_METHODS.items():
        if getattr(_LEDGER, name) is not operation or operation.__code__ is not code:
            raise _Fault("namespace_ledger_changed")


def _make(name, *items, emergency=False):
    _owner()
    kind = _TYPES[name]
    if emergency:
        # Original cached slots, used only for incomplete retained evidence.
        return _PORTS["_retained_evidence"][1](kind, *items)
    _port("_auth")(kind)
    return kind(*items)


class _Fault(RuntimeError):
    @property
    def code(self):
        return (
            self.args[0]
            if self.args and type(self.args[0]) is str
            else "namespace_operation_failed"
        )


class PrivateNamespaceRefusal(RuntimeError):
    def __init__(
        self, evidence: values.PrivateNamespaceRefusalEvidence, cause: BaseException
    ):
        self.evidence = evidence
        self.original_cause = cause
        super().__init__(evidence.code)


class RetainedPrivateNamespaceTransaction:
    # CPython supplies this slot when the original factory uses object.__new__.
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("original_namespace_factory_required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("namespace_subclass_refused")

    def __copy__(self):
        raise TypeError("namespace_copy_refused")

    def __deepcopy__(self, memo):
        raise TypeError("namespace_copy_refused")

    def __reduce_ex__(self, protocol):
        raise TypeError("namespace_serialization_refused")


@dataclass
class _EpochRecord:
    kind: str
    reference: str
    before: int
    requested: int | None
    dispatch: str = "not_attempted"
    effect: str = "none"
    durability: str = "not_confirmed"
    after: int | None = None
    returned: int | None = None
    cause: Any = None


@dataclass(eq=False)
class _State:
    parent: Any
    root: Any
    binding: values.PrivateNamespaceBinding
    ledger: native._ReadLedger
    pid: int = field(default_factory=os.getpid)
    thread: int = field(default_factory=threading.get_ident)
    root_fd: int | None = None
    control_fd: int | None = None
    lock: str = "not_acquired"
    phase: str = "reserved"
    unlock_attempted: bool = False
    released: bool = False
    complete: bool = True
    primary: Any = None
    cause: BaseException | None = None
    secondary: list[Any] = field(default_factory=list)
    cleanup: values.PrivateNamespaceCleanup | None = None
    handle_ref: Any = None
    preparing_child: bool = False
    child_started: bool = False
    child: Any = None
    child_state: Any = None
    child_binding: Any = None
    child_cleanup: Any = None
    native_child: Any = None
    footprint: Any = None
    child_resources: tuple[Any, ...] = ()
    arm_spent: bool = False
    epoch_records: tuple[_EpochRecord, ...] = ()
    armed_control: entry.EntryStat | None = None


_TRANSACTIONS: dict[int, tuple[Any, _State]] = {}
_NAMESPACE_ROOTS: dict[int, tuple[Any, Any]] = {}


def _primary(error, stage, state=None):
    owner = _owner()
    if type(error) is owner.PrivateDirectoryRefusal:
        original = error.evidence.primary_failure
        if (
            type(original) is _TYPES["ConfinedSequencePrimaryFailure"]
            and original.state != "none"
        ):
            return original
    cause = error.original_cause if type(error) is _ENTRY_ERROR else error
    code = (
        error.args[0]
        if type(error) in (_Fault, source.SourceAuthorityError)
        and error.args
        and type(error.args[0]) is str
        else "namespace_operation_failed"
    )
    return _make(
        "ConfinedSequencePrimaryFailure",
        "observed",
        None if state is None else state.binding.transaction_ref,
        stage,
        code,
        type(cause).__name__,
        not isinstance(cause, Exception),
        emergency=True,
    )


def _resource_rows(state):
    result = []
    for row in state.ledger.resources:
        if row.acquisition_state == "not_acquired":
            continue
        result.append(
            _make(
                "ConfinedSequenceResourceEvidence",
                row.resource_ref,
                "aware.filesystem.private-namespace.v1",
                row.kind,
                row.path,
                "released"
                if row.closed
                else "unknown"
                if row.spent or row.descriptor is None
                else "owned",
                row.spent,
                "confirmed" if row.closed else "unknown",
                (),
                emergency=True,
            )
        )
    return tuple(result)


def _epoch_rows(state, *, emergency=False):
    return tuple(
        _make(
            "PrivateNamespacePhysicalEffect",
            row.reference,
            row.kind,
            source.CONTROL_NAME,
            row.dispatch,
            row.effect,
            row.durability,
            row.before,
            row.after,
            row.requested,
            row.returned,
            row.cause,
            emergency=emergency,
        )
        for row in state.epoch_records
    )


def _snapshot(state, *, emergency=False):
    if state.native_child is not None and not emergency:
        child_observation = _native_port("_observation")(state.native_child)
        state.child_resources = child_observation.resources
        if (
            child_observation.primary_failure.state != "none"
            and state.primary.state == "none"
        ):
            state.primary = child_observation.primary_failure
            state.complete = False
            if not state.released:
                state.phase = "retired"
        elif (
            child_observation.phase == "completed"
            and state.phase in {"armed", "executing"}
            and not state.released
        ):
            state.phase = "completed"
    return _make(
        "PrivateNamespaceTransactionObservation",
        "aware.filesystem.private-namespace-observation.v1",
        state.binding,
        state.phase,
        state.lock,
        _epoch_rows(state, emergency=emergency),
        state.footprint,
        None
        if state.child_binding is None
        else state.child_binding.private_sequence_ref,
        _resource_rows(state) + state.child_resources,
        state.primary,
        state.complete,
        False,
        emergency=emergency,
    )


def _safe_snapshot(state):
    try:
        return _snapshot(state)
    except BaseException as error:  # noqa: BLE001 - retain current disposal facts, not stale snapshots
        _record_failure(state, error, "observation")
        return _snapshot(state, emergency=True)


def _settlement(state, ordinal):
    # Ledger reservation order survives an interruption before the ordinary
    # returned-fd assignment to State. Never infer custody from that alias.
    if ordinal >= len(state.ledger.resources):
        return "not_acquired"
    row = state.ledger.resources[ordinal]
    if row.acquisition_state == "not_acquired":
        return "not_acquired"
    return "confirmed" if row.closed else "unknown"


def _record_failure(state, error, stage):
    primary = _primary(error, stage, state)
    if state.primary.state == "none":
        state.primary = primary
        error.__traceback__ = None
        state.cause = error
    else:
        state.secondary.append(primary)
    state.complete = False


def _release_child(state):
    if not state.child_started:
        return
    try:
        if state.child_state is not None:
            state.child_cleanup = _owned_port("_cleanup_private_sequence")(
                state.child_state
            )
        elif state.native_child is not None:
            cleanup = _native_port("_release_state")(state.native_child)
            state.child_cleanup = _make(
                "PrivateSequenceCleanup",
                state.child_binding,
                _owned_port("_safe_directory_observation")(state.root),
                cleanup,
                emergency=True,
            )
    except BaseException as error:  # noqa: BLE001 - retain original child facts and continue separate coordination cleanup
        _record_failure(state, error, "child_release")
        original = state.native_child
        if original is not None and original.cleanup is None:
            try:
                # Continue only original still-unspent rights; attempted
                # descriptor closes are never issued again.
                _native_port("_release_state")(original)
            except BaseException as continuation_error:  # noqa: BLE001 - repeated interruption remains unknown
                _record_failure(state, continuation_error, "child_cleanup_continuation")
        native_cleanup = None if original is None else original.cleanup
        if native_cleanup is not None:
            state.child_cleanup = _make(
                "PrivateSequenceCleanup",
                state.child_binding,
                _owned_port("_safe_directory_observation")(state.root),
                native_cleanup,
                emergency=True,
            )
    if (
        state.child_cleanup is None
        or state.child_cleanup.sequence.release != "confirmed"
    ):
        cause = None if state.native_child is None else state.native_child.cleanup_error
        _record_failure(
            state,
            cause or _Fault("namespace_child_release_unresolved"),
            "child_release",
        )
    if state.child_cleanup is not None:
        state.child_resources = state.child_cleanup.sequence.resources


def _cleanup_value(state):
    unlock = (
        "confirmed"
        if state.lock == "confirmed_released"
        else "unknown"
        if state.unlock_attempted
        else "not_acquired"
    )
    control = _settlement(state, 1)
    root = _settlement(state, 0)
    outcome = (
        "confirmed"
        if (unlock, control, root) == ("confirmed",) * 3
        and not state.secondary
        and (
            not state.child_started
            or state.child_cleanup is not None
            and state.footprint is not None
            and state.child_cleanup.binding == state.child_binding
            and state.child_cleanup.sequence.release == "confirmed"
        )
        else "not_acquired"
        if (unlock, control, root) == ("not_acquired",) * 3
        else "unknown"
    )
    state.phase = "released" if outcome in {"confirmed", "not_acquired"} else "unknown"
    if outcome == "unknown":
        state.complete = False
    observation = _safe_snapshot(state)
    state.cleanup = _make(
        "PrivateNamespaceCleanup",
        "aware.filesystem.private-namespace-cleanup.v1",
        observation,
        state.child_cleanup,
        unlock,
        control,
        root,
        tuple(state.secondary),
        outcome,
        emergency=True,
    )
    return state.cleanup


def _release(state):
    if state.native_child is not None and state.native_child.busy:
        raise _Fault("namespace_child_busy")
    if state.released:
        return state.cleanup if state.cleanup is not None else _cleanup_value(state)
    state.released = True
    state.phase = "releasing"
    try:
        try:
            try:
                _release_child(state)
            finally:
                if state.lock in {"held", "unknown"} and not state.unlock_attempted:
                    state.unlock_attempted = True
                    try:
                        _source("_unlock", cleanup=True)(state.control_fd)
                        state.lock = "confirmed_released"
                    except BaseException as error:  # noqa: BLE001 - dispose other owned resources without repeating unlock
                        state.lock = "unknown"
                        _record_failure(state, error, "unlock")
        finally:
            try:
                _ledger_check()
                _LEDGER_METHODS["close_all"][0](state.ledger)
            except BaseException as error:  # noqa: BLE001 - preserve rights and unavailable settlement
                state.ledger.cleanup_failure(error, "namespace_close")
        if state.ledger.first_cleanup_error is not None:
            _record_failure(state, state.ledger.first_cleanup_error, "close")
        return _cleanup_value(state)
    finally:
        root = state.root
        pair = None if root is None else _NAMESPACE_ROOTS.get(id(root))
        if (
            root is not None
            and pair is not None
            and pair[1]() is state
            and state.cleanup is not None
            and state.cleanup.outcome == "confirmed"
        ):
            if root.namespace_claim is pair[1]:
                root.namespace_claim = None
            _NAMESPACE_ROOTS.pop(id(root), None)
        state.child = state.child_state = state.native_child = None
        # Borrowing ends even when return/snapshot allocation is unavailable.
        state.parent = None
        state.root = None


def _failure(
    error, stage, state=None, *, read=None, inventory=None, entry_failure=None
):
    owner = _owner()
    primary = _primary(error, stage, state)
    if state is not None:
        if state.primary.state == "none":
            state.primary = primary
            state.cause = error
        state.complete = False
        primary = state.primary
    original = error.evidence if type(error) is owner.PrivateDirectoryRefusal else None
    if original is None and read is not None:
        original = _make(
            "PrivateDirectoryRefusalEvidence",
            primary.code,
            primary.cause_type,
            stage,
            read.directory_after,
            None,
            read.original,
            None,
            primary,
            False,
            emergency=True,
        )
    evidence = _make(
        "PrivateNamespaceRefusalEvidence",
        "aware.filesystem.private-namespace-refusal.v1",
        primary.code or "namespace_operation_failed",
        stage,
        primary,
        None if state is None else state.binding.control_before,
        None if state is None else _safe_snapshot(state),
        inventory,
        original,
        entry_failure,
        None if state is None else state.cleanup,
        "not_acquired"
        if state is None
        else "unknown"
        if state.cleanup is None or state.cleanup.outcome == "unknown"
        else "borrowed",
        False,
        False,
        emergency=True,
    )
    error.__traceback__ = None
    return PrivateNamespaceRefusal(
        evidence,
        state.cause if state is not None and state.cause is not None else error,
    )


def _require(handle):
    pair = state = None
    try:
        if type(handle) is not RetainedPrivateNamespaceTransaction:
            raise _Fault("namespace_original_transaction_required")
        pair = _TRANSACTIONS.get(id(handle))
        if pair is None or pair[0]() is not handle:
            raise _Fault("namespace_original_transaction_required")
        state = pair[1]
        if (state.pid, state.thread) != (os.getpid(), threading.get_ident()):
            raise _Fault("namespace_execution_changed")
        return state
    finally:
        handle = pair = state = None


def _finalize(key, state):
    try:
        if state.pid != os.getpid():
            # The child may close its inherited descriptor copies, never unlock
            # the parent's shared open-file description.
            if state.native_child is not None:
                _native_port("_release_state")(state.native_child)
            _LEDGER_METHODS["close_all"][0](state.ledger)
        else:
            _release(state)
    except BaseException:  # noqa: BLE001 - finalization never retries spent rights
        state.complete = False
    finally:
        _TRANSACTIONS.pop(key, None)


def _parent(directory, expected_binding):
    root = None
    try:
        root = _port("_original_directory")(directory)
        _port("validate_private_directory")(
            directory, expected_binding=expected_binding
        )
        return root
    finally:
        directory = root = None


def _stat_value(info):
    return _make(
        "EntryStat",
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_uid,
        info.st_gid,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def observe_private_namespace_control(
    directory: RetainedPrivateDirectory, *, expected_binding: PrivateDirectoryBinding
) -> PrivateNamespaceControlObservation:
    root = read = None
    try:
        root = _parent(directory, expected_binding)
        before = os.stat(source.CONTROL_NAME, dir_fd=root.fd, follow_symlinks=False)
        _source("_validate_control_info")(before)
        read = _port("observe_private_directory_file")(
            directory,
            expected_binding=expected_binding,
            path=source.CONTROL_NAME,
            maximum_bytes=30,
        )
        after = os.stat(source.CONTROL_NAME, dir_fd=root.fd, follow_symlinks=False)
        if _stat_value(before) != _stat_value(after):
            raise _Fault("namespace_control_changed")
        epoch = _source("_parse_epoch_body")(read.original.observation.content)
        result = _make(
            "PrivateNamespaceControlObservation",
            "aware.filesystem.private-namespace-control.v1",
            "namespace-control:" + uuid4().hex,
            expected_binding,
            source.CONTROL_NAME,
            source.PROFILE,
            _stat_value(after),
            epoch,
            read,
            True,
        )
        _port("private_directory_value_to_payload")(result)
        return result
    except BaseException as error:  # noqa: BLE001 - preserve interruption evidence at the public boundary
        refusal = _failure(error, "control_observation", read=read)
        raise refusal from refusal.original_cause
    finally:
        del directory, expected_binding, root, read


def retain_private_namespace_transaction(
    directory: RetainedPrivateDirectory,
    *,
    expected_binding: PrivateDirectoryBinding,
    expected_control: PrivateNamespaceControlObservation,
    limits: PrivateNamespaceLimits,
) -> RetainedPrivateNamespaceTransaction:
    root = state = handle = key = None
    try:
        _owner()
        if (
            type(expected_control) is not _TYPES["PrivateNamespaceControlObservation"]
            or type(limits) is not _TYPES["PrivateNamespaceLimits"]
        ):
            raise _Fault("namespace_input_invalid")
        _port("private_directory_value_to_payload")(expected_control)
        _port("private_directory_value_to_payload")(limits)
        if limits.owned_descriptor_budget < 3:
            raise _Fault("namespace_descriptor_capacity_exceeded")
        root = _parent(directory, expected_binding)
        if expected_control.directory != root.binding:
            raise _Fault("namespace_control_binding_mismatch")
        if source.fcntl is None or sys.platform != "linux":
            raise _Fault("namespace_platform_unsupported")
        _ledger_check()
        binding = _make(
            "PrivateNamespaceBinding",
            "aware.filesystem.private-namespace-binding.v1",
            "namespace-transaction:" + uuid4().hex,
            "namespace-generation:" + uuid4().hex,
            os.getpid(),
            threading.get_ident(),
            root.binding,
            expected_control,
            limits,
        )
        primary = _make(
            "ConfinedSequencePrimaryFailure", "none", None, None, None, None, False
        )
        state = _State(
            directory, root, binding, _LEDGER(private_root=root), primary=primary
        )
        state.ledger.stage = "namespace_root"
        state.root_fd = state.ledger.open(
            root.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        )
        state.ledger.stage = "namespace_control"
        state.control_fd = state.ledger.open(
            source.CONTROL_NAME,
            os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=state.root_fd,
        )
        lock = _source("_lock")
        state.lock = "unknown"  # Reserve lock settlement before dispatch.
        try:
            lock(state.control_fd, exclusive=True)
            state.lock = "held"
        except source.SourceAuthorityError as error:
            if error.code == "source_authority_busy":
                state.lock = "not_acquired"
            raise
        epoch = _source("_epoch")(state.control_fd)
        current = _stat_value(os.fstat(state.control_fd))
        named = _stat_value(
            os.stat(source.CONTROL_NAME, dir_fd=state.root_fd, follow_symlinks=False)
        )
        _port("validate_private_directory")(
            directory, expected_binding=expected_binding
        )
        if (
            epoch != expected_control.epoch
            or current != expected_control.control_stat
            or current != named
        ):
            raise _Fault("namespace_control_changed")
        with root.lock:
            _register_namespace_root(state)
        result = _snapshot(state)
        _port("private_directory_value_to_payload")(result)
        handle = object.__new__(RetainedPrivateNamespaceTransaction)
        key = id(handle)
        state.handle_ref = weakref.ref(handle)
        _TRANSACTIONS[key] = (state.handle_ref, state)
        weakref.finalize(handle, _finalize, key, state)
        return handle
    except BaseException as error:  # noqa: BLE001 - settle acquired custody even on interruption
        if key is not None:
            _TRANSACTIONS.pop(key, None)
        if state is not None:
            _record_failure(state, error, "retain")
            _release(state)
        refusal = _failure(error, "retain", state)
        raise refusal from refusal.original_cause
    finally:
        del (
            directory,
            expected_binding,
            expected_control,
            limits,
            root,
            state,
            handle,
            key,
        )


def _current(state):
    if (
        state.released
        or state.phase
        not in {"reserved", "prepared", "armed", "executing", "completed"}
        or state.lock != "held"
        or state.primary.state != "none"
    ):
        raise _Fault("namespace_transaction_retired")
    _port("validate_private_directory")(
        state.parent, expected_binding=state.binding.directory
    )
    expected = state.binding.control_before
    expected_stat = state.armed_control or expected.control_stat
    expected_epoch = expected.epoch + (state.armed_control is not None)
    if (
        _source("_epoch")(state.control_fd) != expected_epoch
        or _stat_value(os.fstat(state.control_fd)) != expected_stat
        or _stat_value(
            os.stat(source.CONTROL_NAME, dir_fd=state.root_fd, follow_symlinks=False)
        )
        != expected_stat
    ):
        raise _Fault("namespace_control_changed")


def _root_gone(key, reference):
    pair = _NAMESPACE_ROOTS.get(key)
    if pair is not None and pair[0] is reference:
        _NAMESPACE_ROOTS.pop(key, None)


def _register_namespace_root(state):
    root = state.root
    if root.namespace_claim is not None or root.child is not None:
        raise _Fault("namespace_parent_in_use")
    key = id(root)
    reference = weakref.ref(state)
    _NAMESPACE_ROOTS[key] = (weakref.ref(root, lambda r: _root_gone(key, r)), reference)
    root.namespace_claim = reference


def _namespace_owner_join(root, stage, *, original=None, child=None):
    state = pair = private = handle = None
    try:
        pair = _NAMESPACE_ROOTS.get(id(root))
        if pair is None or pair[0]() is not root or root.namespace_claim is not pair[1]:
            raise _Fault("namespace_original_claim_required")
        state = pair[1]()
        if state is None or state.handle_ref is None:
            raise _Fault("namespace_original_claim_required")
        # Acquire once, before validation. The exact validated original stays
        # strongly held until custody transfers to the worker's return value.
        handle = state.handle_ref()
        if _require(handle) is not state:
            raise _Fault("namespace_original_claim_required")
        _current(state)
        if stage == "dispatch":
            if (
                original is None
                or original is not state.native_child
                or state.child_state is None
                or state.child_binding is None
                or state.child_state.released
                or state.child_state.directory is not root
                or original.binding is not state.child_binding.sequence
                or _native_port("_issued")(state.child_state.original) is not original
            ):
                raise _Fault("namespace_original_child_required")
            if (
                not state.arm_spent
                or state.armed_control is None
                or len(state.epoch_records) != 2
                or any(
                    row.dispatch != "returned"
                    or row.effect != "applied"
                    or row.durability != "confirmed"
                    for row in state.epoch_records
                )
            ):
                raise _Fault("namespace_arm_required")
            state.phase = "executing"
            # Original worker holds the genuine transaction until its busy flag
            # is cleared. This is custody, not a caller-provided verifier/flag.
            return handle
        if not state.preparing_child or state.phase != "reserved":
            raise _Fault("namespace_child_preparation_required")
        if stage == "private_prepare":
            if state.child_started:
                raise _Fault("namespace_child_already_retained")
        elif stage == "native_prepare":
            if (
                state.child_started
                or type(original) is not sequences._SequenceState
                or original.private_root is not root
            ):
                raise _Fault("namespace_original_child_required")
            state.child_started = True
            state.native_child = (
                original  # Original custody before first fd acquisition.
            )
        elif stage == "private_child":
            private = _port("_original_private_sequence")(child)
            if (
                private.directory is not root
                or original is not state.native_child
                or _native_port("_issued")(private.original) is not original
            ):
                raise _Fault("namespace_original_child_required")
            state.child = (
                child  # Own the returned handle before fallible projection/return.
            )
            state.child_state = private
            state.child_binding = private.binding
        else:
            raise _Fault("namespace_join_stage_invalid")
    except BaseException as error:
        if stage == "dispatch" and state is not None and original is state.native_child:
            _record_failure(state, error, "namespace_dispatch")
            state.phase = "retired"
        raise
    finally:
        del root, original, child, state, pair, private, handle


def retain_private_namespace_file_sequence(
    transaction: RetainedPrivateNamespaceTransaction,
    *,
    requests: tuple[ConfinedFileMutationRequest, ...],
    limits: ConfinedSequenceLimits,
    confinement_profile: ConfinedMutationProfile,
) -> RetainedPrivateFileSequence:
    state = child = None
    try:
        state = _require(transaction)
        _current(state)
        if state.child_started or state.phase != "reserved":
            raise _Fault("namespace_child_already_retained")
        if type(limits) is not ConfinedSequenceLimits:
            raise _Fault("namespace_sequence_limits_invalid")
        selected = state.binding.limits
        _port("private_directory_value_to_payload")(
            _make(
                "PrivateNamespaceLimits",
                selected.inventory_entries,
                selected.name_bytes,
                selected.roster_bytes,
                selected.inventory_wire_bytes,
                selected.member_bytes,
                selected.owned_descriptor_budget,
                selected.cursor_resource_budget,
                limits,
            )
        )
        for name in sequences._LIMIT_CAPS:
            if getattr(limits, name) > getattr(
                state.binding.limits.sequence_limits, name
            ):
                raise _Fault("namespace_sequence_limits_exceeded")
        if (
            limits.simultaneous_owned_descriptors + 3
            > state.binding.limits.owned_descriptor_budget
        ):
            raise _Fault("namespace_descriptor_capacity_exceeded")
        state.preparing_child = True
        try:
            child = _port("retain_private_file_sequence")(
                state.parent,
                expected_binding=state.binding.directory,
                requests=requests,
                limits=limits,
                confinement_profile=confinement_profile,
            )
        finally:
            state.preparing_child = False
        if child is not state.child or state.child_binding is None:
            raise _Fault("namespace_original_child_required")
        _current(state)
        binding = state.child_binding.sequence
        reserved, _ = _port("_private_sequence_reservation")(
            state.root.root,
            binding,
            len(state.native_child.resources),
            whole=True,
        )
        state.footprint = _make(
            "PrivateNamespaceFootprint",
            "aware.filesystem.private-namespace-footprint.v1",
            state.binding.transaction_ref,
            state.child_binding,
            (source.CONTROL_NAME,),
            binding.ordered_steps,
            tuple(row.scratch_path for row in binding.files),
            sum(row.candidate_size_bytes for row in binding.files),
            reserved,
            3 + limits.simultaneous_owned_descriptors,
            2,
            True,
        )
        _port("private_directory_value_to_payload")(state.footprint)
        state.phase = "prepared"
        _port("private_directory_value_to_payload")(_snapshot(state))
        return child
    except BaseException as error:  # noqa: BLE001 - failed preparation retains original child custody and closes it before the lock
        refusal = _observation_refusal(error, "child_preparation", state)
        raise refusal from refusal.original_cause
    finally:
        del transaction, requests, limits, confinement_profile, state, child


def arm_private_namespace_transaction(
    transaction: RetainedPrivateNamespaceTransaction,
    *,
    sequence: RetainedPrivateFileSequence,
    expected_footprint: PrivateNamespaceFootprint,
) -> PrivateNamespaceTransactionObservation:
    state = active = None
    try:
        state = _require(transaction)
        if state.arm_spent:
            raise _Fault("namespace_arm_already_spent")
        _current(state)
        if (
            state.phase != "prepared"
            or sequence is not state.child
            or state.child_state is None
            or state.footprint is None
            or state.child_state.released
        ):
            raise _Fault("namespace_original_child_required")
        encode = _port("private_directory_value_to_payload")
        if encode(expected_footprint) != encode(state.footprint):
            raise _Fault("namespace_footprint_mismatch")
        _port("verify_private_file_sequence")(
            sequence, expected_binding=state.child_binding
        )
        _current(state)
        before = state.binding.control_before.epoch
        control_fd, root_fd = state.control_fd, state.root_fd
        if control_fd is None or root_fd is None:
            raise _Fault("namespace_original_control_required")
        if before == 2**64 - 1:
            raise _Fault("source_epoch_exhausted")
        # Authenticate both original operations before spending either right.
        write, sync = _source("_write_epoch"), _source("_sync_epoch")
        requested = len(source._HEADER) + 8
        state.epoch_records = (
            _EpochRecord(
                "control_epoch_write",
                "namespace-epoch:" + str(uuid4()),
                before,
                requested,
                cause=state.primary,
            ),
            _EpochRecord(
                "control_fsync",
                "namespace-sync:" + str(uuid4()),
                before,
                None,
                cause=state.primary,
            ),
        )
        # Validate the complete descriptive return before the first effect.
        encode(_snapshot(state))
        state.arm_spent = True
        active = state.epoch_records[0]
        active.dispatch, active.effect = "attempted", "unknown"
        count = write(control_fd, before + 1)
        active.dispatch = "returned"
        if type(count) is not int or not 0 <= count <= requested:
            raise _Fault("source_epoch_write_return_invalid")
        active.returned = count
        if count != requested:
            if count == 0:
                active.effect = "none"
            raise _Fault("source_epoch_write_incomplete")
        active.effect, active.after = "applied", before + 1
        active = state.epoch_records[1]
        active.dispatch, active.effect, active.durability = (
            "attempted",
            "unknown",
            "unknown",
        )
        sync(control_fd)
        active.dispatch, active.effect, active.durability = (
            "returned",
            "applied",
            "confirmed",
        )
        active.after = before + 1
        state.epoch_records[0].durability = "confirmed"
        active = None
        # Only known write+sync returns can establish an armed control bookend.
        # This read never upgrades an unavailable original return.
        control = _stat_value(os.fstat(control_fd))
        if (
            control.values()[:7]
            != state.binding.control_before.control_stat.values()[:7]
            or control
            != _stat_value(
                os.stat(source.CONTROL_NAME, dir_fd=root_fd, follow_symlinks=False)
            )
            or _source("_epoch")(control_fd) != before + 1
        ):
            raise _Fault("namespace_control_changed")
        state.armed_control = control
        state.phase = "armed"
        _current(state)
        observed = _snapshot(state)
        encode(observed)
        return observed
    except BaseException as error:  # noqa: BLE001 - spent arm and original physical facts survive return/refusal failure
        if active is not None:
            active.cause = _primary(error, "epoch_" + active.kind, state)
        refusal = _observation_refusal(error, "arming", state)
        raise refusal from refusal.original_cause
    finally:
        del transaction, sequence, expected_footprint, state, active


def _inventory_value(state, roster, members, complete):
    size = 0
    # Only the decimal length of encoded_bytes can change the framing length.
    # Reach a fixed point over the original owner codec, never a second schema.
    for _ in range(8):
        result = _make(
            "PrivateNamespaceInventoryObservation",
            "aware.filesystem.private-namespace-inventory.v1",
            state.binding.transaction_ref,
            roster.observation_ref,
            roster,
            tuple(members),
            complete,
            True,
            size,
            True,
        )
        payload = _port("private_directory_value_to_payload")(result)
        encoded = len(
            json.dumps(
                payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        )
        if encoded == size:
            if encoded > state.binding.limits.inventory_wire_bytes:
                raise _Fault("namespace_inventory_wire_capacity_exceeded")
            return result
        size = encoded
    raise _Fault("namespace_inventory_framing_unavailable")


def _entry_failure_value(error, state):
    if type(error) is not _ENTRY_ERROR:
        return None
    prefix = error.observation_prefix
    ancestors = tuple(
        _make(
            "PrivateNamespaceAncestorPrefix",
            row[0],
            row[1],
            row[2],
            None,
            None,
            row[6],
            None,
            None,
            emergency=True,
        )
        for row in prefix.get("ancestors", ())
    )
    text = prefix.get("link_text")
    partial = _make(
        "PrivateNamespaceEntryPrefix",
        prefix.get("root_before"),
        prefix.get("root_after"),
        prefix.get("entry_locator"),
        prefix.get("entry_before"),
        prefix.get("entry_after"),
        prefix.get("opened_directory"),
        prefix.get("kind"),
        ancestors,
        prefix.get("ancestor_bookends", ()),
        prefix.get("children_before"),
        prefix.get("children_after"),
        None if text is None else os.fsencode(text),
        prefix.get("descriptor_resources"),
        prefix.get("cursor_resources"),
        prefix.get("resource_evidence_available", False),
        emergency=True,
    )
    raw = error.raw_unrepresentable_name
    raw_bytes = (
        os.fsencode(raw) if type(raw) is str else raw if type(raw) is bytes else None
    )
    descriptor_cleanup = error.original_descriptor_cleanup
    if descriptor_cleanup is None:
        descriptor_cleanup = _make(
            "ConfinedFileReadCleanup",
            "unknown",
            None,
            None,
            None,
            ("entry_cleanup_unavailable",),
            emergency=True,
        )
    cursor_cleanup = error.cursor_cleanup
    if cursor_cleanup is None:
        cursor_cleanup = _make(
            "EntryCursorCleanup",
            "unknown",
            None,
            None,
            None,
            ("entry_cursor_cleanup_unavailable",),
            emergency=True,
        )
    return _make(
        "PrivateNamespaceEntryFailure",
        "aware.filesystem.private-namespace-entry-failure.v1",
        error.request_snapshot,
        error.observation_ref,
        error.phase,
        partial,
        error.roster_prefix,
        raw_bytes,
        "filesystem_surrogateescape"
        if type(raw) is str
        else "raw_bytes"
        if type(raw) is bytes
        else "unavailable",
        descriptor_cleanup,
        cursor_cleanup,
        _primary(error, "entry", state),
        emergency=True,
    )


def _observation_refusal(error, stage, state, *, read=None, inventory=None):
    if state is not None and state.primary.state == "none":
        _record_failure(state, error, stage)
    original_entry = None
    try:
        original_entry = _entry_failure_value(error, state)
    except BaseException as mapping_error:  # noqa: BLE001 - mapping failure cannot prevent original cleanup
        if state is not None:
            _record_failure(state, mapping_error, "entry_failure_mapping")
    finally:
        if state is not None and not state.released:
            _release(state)
    return _failure(
        error,
        stage,
        state,
        read=read,
        inventory=inventory,
        entry_failure=original_entry,
    )


def observe_private_namespace_inventory(
    transaction: RetainedPrivateNamespaceTransaction,
) -> PrivateNamespaceInventoryObservation:
    state = roster = inventory = None
    members = []
    try:
        state = _require(transaction)
        _current(state)
        limits = state.binding.limits
        if limits.owned_descriptor_budget < 6:
            raise _Fault("namespace_descriptor_capacity_exceeded")
        for name, (operation, code) in _ENTRY_PORTS.items():
            if getattr(entry, name) is not operation or operation.__code__ is not code:
                raise _Fault("namespace_entry_owner_changed")
        with state.root.lock:
            _current(state)
            if state.root.child is not None:
                raise _Fault("namespace_parent_in_use")
            if state.root.acquisitions >= 128:
                raise _Fault("namespace_parent_capacity_exceeded")
            state.root.acquisitions += 1
            marker = "namespace-inventory:" + uuid4().hex
            state.root.child = marker
            try:
                roster = _ENTRY_PORTS["_observe_private_entry_with_cleanup"][0](
                    private_root=state.root,
                    maximum_children=limits.inventory_entries,
                    maximum_name_bytes=limits.name_bytes,
                    maximum_roster_bytes=limits.roster_bytes,
                )
                if type(roster) is not _TYPES["ConfinedEntryObservation"]:
                    raise _Fault("namespace_original_roster_required")
                _port("private_directory_value_to_payload")(roster)
                for name in roster.children_before:
                    # Flat names use the shared canonical path rules, never a
                    # journal filename grammar or a second admission evaluator.
                    native._saved_read_path(name)
                    before = _stat_value(
                        os.stat(name, dir_fd=state.root_fd, follow_symlinks=False)
                    )
                    members.append(
                        _make("PrivateNamespaceInventoryMember", name, before)
                    )
                for member in members:
                    if (
                        _stat_value(
                            os.stat(
                                member.name, dir_fd=state.root_fd, follow_symlinks=False
                            )
                        )
                        != member.stat
                    ):
                        raise _Fault("namespace_inventory_member_changed")
                if (
                    state.root_fd is None
                    or _stat_value(os.fstat(state.root_fd)) != roster.root_after
                ):
                    raise _Fault("namespace_inventory_root_changed")
                _current(state)
                inventory = _inventory_value(state, roster, members, True)
                return inventory
            finally:
                if state.root.child == marker:
                    state.root.child = None
    except BaseException as error:  # noqa: BLE001 - retire only this original transaction and retain physical failure evidence
        if roster is not None and inventory is None:
            try:
                inventory = _inventory_value(state, roster, members, False)
            except BaseException as prefix_error:  # noqa: BLE001 - bounded prefix may itself exceed the accepted wire cap
                if state is not None and state.primary.state == "none":
                    _record_failure(state, error, "inventory")
                _record_failure(state, prefix_error, "inventory_prefix")
        refusal = _observation_refusal(error, "inventory", state, inventory=inventory)
        raise refusal from refusal.original_cause
    finally:
        del transaction, state, roster, inventory, members


def observe_private_namespace_file(
    transaction: RetainedPrivateNamespaceTransaction, *, path: str, maximum_bytes: int
) -> PrivateFileReadResult:
    state = read = None
    try:
        state = _require(transaction)
        _current(state)
        if (
            type(maximum_bytes) is not int
            or not 0 < maximum_bytes <= state.binding.limits.member_bytes
            or state.binding.limits.owned_descriptor_budget < 5
        ):
            raise _Fault("namespace_member_capacity_exceeded")
        native._saved_read_path(path)
        if "/" in path:
            raise _Fault("namespace_member_flat_required")
        read = _port("observe_private_directory_file")(
            state.parent,
            expected_binding=state.binding.directory,
            path=path,
            maximum_bytes=maximum_bytes,
        )
        _current(state)
        _port("private_directory_value_to_payload")(read)
        return read
    except BaseException as error:  # noqa: BLE001 - preserve original bounded read/cleanup, never retry or spend an epoch
        refusal = _observation_refusal(error, "member_read", state, read=read)
        raise refusal from refusal.original_cause
    finally:
        del transaction, state, path, maximum_bytes, read


def observe_private_namespace_transaction(
    transaction: RetainedPrivateNamespaceTransaction,
) -> PrivateNamespaceTransactionObservation:
    state = None
    try:
        state = _require(transaction)
        result = _snapshot(state)
        _port("private_directory_value_to_payload")(result)
        return result
    except BaseException as error:  # noqa: BLE001 - retain original observation failure classification
        refusal = _failure(error, "observe", state)
        raise refusal from refusal.original_cause
    finally:
        del transaction, state


def release_private_namespace_transaction(
    transaction: RetainedPrivateNamespaceTransaction,
) -> PrivateNamespaceCleanup:
    state = None
    try:
        state = _require(transaction)
        result = _release(state)
        if result is None or result.outcome == "unknown" or not state.complete:
            raise _Fault("namespace_cleanup_unresolved")
        _port("private_directory_value_to_payload")(result)
        return result
    except BaseException as error:  # noqa: BLE001 - preserve completed/unknown disposal on interruption
        refusal = _failure(error, "release", state)
        raise refusal from refusal.original_cause
    finally:
        del transaction, state


__all__ = [
    "PrivateNamespaceRefusal",
    "RetainedPrivateNamespaceTransaction",
    "arm_private_namespace_transaction",
    "observe_private_namespace_control",
    "observe_private_namespace_file",
    "observe_private_namespace_inventory",
    "observe_private_namespace_transaction",
    "release_private_namespace_transaction",
    "retain_private_namespace_file_sequence",
    "retain_private_namespace_transaction",
]


def _capacity_context_authenticate():
    if _owner_module is not _CAPACITY_OWNER_MODULE:
        raise _Fault("namespace_capacity_model_unavailable")
    for module, name, registry, entries in _CAPACITY_CONTEXT_REGISTRIES:
        if (
            module.__dict__.get(name) is not registry
            or type(registry) is not dict
            or len(registry) != len(entries)
            or any(registry.get(key) is not value for key, value in entries)
        ):
            raise _Fault("namespace_capacity_model_unavailable")
    for module, name, operation, code in _CAPACITY_CONTEXT_PORTS:
        if module.__dict__.get(name) is not operation or operation.__code__ is not code:
            raise _Fault("namespace_capacity_model_unavailable")
    if (
        replace is not _CAPACITY_REPLACE[0]
        or replace.__code__ is not _CAPACITY_REPLACE[1]
    ):
        raise _Fault("namespace_capacity_model_unavailable")
    for name, original in _CAPACITY_OWNER_PORTS:
        if _PORTS.get(name) is not original:
            raise _Fault("namespace_capacity_model_unavailable")
    for name, original in _CAPACITY_OWNER_TYPES:
        if _TYPES.get(name) is not original:
            raise _Fault("namespace_capacity_model_unavailable")
        _owner_module._auth(original)
    for (
        module,
        name,
        cls,
        init,
        code,
        getattribute,
        new,
        slots,
    ) in _CAPACITY_STATE_TYPES:
        if (
            module.__dict__.get(name) is not cls
            or cls.__init__ is not init
            or init.__code__ is not code
            or cls.__getattribute__ is not getattribute
            or cls.__new__ is not new
            or any(cls.__dict__.get(key) is not value for key, value in slots)
        ):
            raise _Fault("namespace_capacity_model_unavailable")


def _capture_namespace_capacity_context(transaction, *, expected_binding):
    """Original pure component capture; no settlement, freshness or cleanup.

    Private same-owner join for the public capacity history port. The returned
    tuple contains detached data and counters only, never custody or rights.
    """
    state = root = parent = child = native_child = snapshot = None
    try:
        _capacity_context_authenticate()
        state = _require(transaction)
        if state.parent is None or state.root is None:
            # Confirmed release deliberately drops live parent custody. Earlier
            # detached histories survive; counters must never be invented here.
            raise _Fault("namespace_capacity_history_changed")
        parent = state.parent  # Strong genuine custody throughout capture.
        root = _port("_original_directory")(parent)
        if root is not state.root:
            raise _Fault("namespace_capacity_binding_mismatch")
        with root.lock:
            _capacity_context_authenticate()
            if state.handle_ref is None or state.handle_ref() is not transaction:
                raise _Fault("namespace_capacity_original_transaction_required")
            if type(expected_binding) is not _TYPES["PrivateNamespaceBinding"]:
                raise _Fault("namespace_capacity_binding_mismatch")
            encode = _port("private_directory_value_to_payload")
            if encode(expected_binding) != encode(state.binding):
                raise _Fault("namespace_capacity_binding_mismatch")
            if state.preparing_child or state.phase == "releasing":
                raise _Fault("namespace_capacity_history_changed")
            native_child = state.native_child
            if native_child is not None and native_child.busy:
                raise _Fault("namespace_capacity_history_changed")
            if not state.released:
                pair = _NAMESPACE_ROOTS.get(id(root))
                if (
                    pair is None
                    or pair[0]() is not root
                    or root.namespace_claim is not pair[1]
                    or pair[1]() is not state
                ):
                    raise _Fault("namespace_capacity_original_transaction_required")
            parent_snapshot = _owner_module._directory_observation(root)
            snapshot = _snapshot(state, emergency=True)
            child_snapshot = None
            if native_child is not None:
                child = _native_port("_observation")(native_child)
                if state.child_binding is not None:
                    if (
                        state.child_binding.directory != state.binding.directory
                        or child.binding is not state.child_binding.sequence
                    ):
                        raise _Fault("namespace_capacity_binding_mismatch")
                    child_snapshot = _make(
                        "PrivateSequenceObservation",
                        state.child_binding,
                        parent_snapshot,
                        child,
                    )
                phase, primary, complete = (
                    snapshot.phase,
                    snapshot.primary_failure,
                    snapshot.ledger_complete,
                )
                if child.primary_failure.state != "none" and primary.state == "none":
                    primary, complete = child.primary_failure, False
                    if not state.released:
                        phase = "retired"
                elif (
                    child.phase == "completed"
                    and phase in {"armed", "executing"}
                    and not state.released
                ):
                    phase = "completed"
                _port("_auth")(type(snapshot))
                snapshot = replace(
                    snapshot,
                    phase=phase,
                    primary_failure=primary,
                    ledger_complete=complete and child.ledger_complete,
                    resources=_resource_rows(state) + child.resources,
                )
            for value in (snapshot, parent_snapshot):
                encode(value)
            if child_snapshot is not None:
                encode(child_snapshot)
            _capacity_context_authenticate()
            return (
                snapshot,
                parent_snapshot,
                child_snapshot,
                root.acquisitions,
                root.validations,
            )
    finally:
        transaction = expected_binding = state = root = parent = child = (
            native_child
        ) = snapshot = None


_NAMESPACE_OWNER_JOIN = (_namespace_owner_join, _namespace_owner_join.__code__)

# Freeze original owner callbacks at import, not after caller-provided mutation.
_owner()

_CAPACITY_CONTEXT_PORTS = tuple(
    (module, name, getattr(module, name), getattr(module, name).__code__)
    for module, names in (
        (
            sys.modules[__name__],
            (
                "_require",
                "_snapshot",
                "_resource_rows",
                "_epoch_rows",
                "_make",
                "_port",
                "_owner",
                "_native_port",
            ),
        ),
        (
            _owner_module,
            (
                "_original_directory",
                "_directory_observation",
                "private_directory_value_to_payload",
                "_auth",
                "_retained_evidence",
            ),
        ),
        (sequences, ("_observation", "_resources", "_scratch_residue")),
    )
    for name in names
) + tuple(
    (module, name, operation, operation.__code__)
    for module in (_owner_module, sequences, native)
    for name, operation in module.__dict__.items()
    if type(operation) is type(_require) and operation.__module__ == module.__name__
)
_CAPACITY_CONTEXT_REGISTRIES = tuple(
    (module, name, registry, tuple(registry.items()))
    for module, name in (
        (_owner_module, "_SCHEMAS"),
        (_owner_module, "_EQUALITY"),
        (_owner_module, "_WIRES"),
        (_owner_module, "_OWNER_HELPERS"),
        (sequences, "_LIMIT_CAPS"),
        (sys.modules[__name__], "_NATIVE_PORTS"),
        (sys.modules[__name__], "_PORTS"),
        (sys.modules[__name__], "_TYPES"),
    )
    for registry in (getattr(module, name),)
)
_CAPACITY_OWNER_PORTS = tuple(_PORTS.items())
_CAPACITY_OWNER_MODULE = _owner_module
_CAPACITY_OWNER_TYPES = tuple(_TYPES.items())
_CAPACITY_REPLACE = (replace, replace.__code__)
_CAPACITY_STATE_TYPES = tuple(
    (
        module,
        name,
        cls,
        cls.__init__,
        cls.__init__.__code__,
        cls.__getattribute__,
        cls.__new__,
        tuple((row.name, cls.__dict__.get(row.name)) for row in fields(cls)),
    )
    for module, name in (
        (sys.modules[__name__], "_State"),
        (sys.modules[__name__], "_EpochRecord"),
        (_owner_module, "_DirectoryState"),
        (_owner_module, "_PrivateSequenceState"),
        (sequences, "_SequenceState"),
        (native, "_ReadLedger"),
        (native, "_ReadResource"),
    )
    for cls in (getattr(module, name),)
)


def _namespace_export(name):
    original, code = _NAMESPACE_EXPORTS[name]
    if (
        globals().get(name) is not original
        or code is not None
        and original.__code__ is not code
    ):
        raise AttributeError("namespace_export_changed")
    return original


_NAMESPACE_EXPORTS = {
    name: (globals()[name], getattr(globals()[name], "__code__", None))
    for name in __all__
}
_NAMESPACE_FACADE = (_namespace_export, _namespace_export.__code__)
