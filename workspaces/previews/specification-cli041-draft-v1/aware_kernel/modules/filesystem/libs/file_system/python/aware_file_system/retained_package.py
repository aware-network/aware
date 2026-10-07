"""Original cooperative package staging/publication; no Issue or SPEC authority.

Custody authenticates original lower-owner resources, not Issue authorization.
Consumers still require the separately qualified complete successor closure.
Observed bytes/identity are not write-history detection or continuous confinement.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import os
import secrets
import stat
import threading
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from weakref import WeakKeyDictionary, finalize

from .confined_mutation import ConfinedMutationEffectState
from .retained_mutation import RetainedPhysicalEffect

_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_HANDLES: WeakKeyDictionary = WeakKeyDictionary()
_POSTIMAGES: WeakKeyDictionary = WeakKeyDictionary()
_LENSES: WeakKeyDictionary = WeakKeyDictionary()
_READERS: WeakKeyDictionary = WeakKeyDictionary()
_INPUTS: WeakKeyDictionary = WeakKeyDictionary()
_LENS_CLAIMS: WeakKeyDictionary = WeakKeyDictionary()


@dataclass(frozen=True, slots=True)
class PackagePhysicalEvidence:
    package_outcome: str
    effects: tuple[RetainedPhysicalEffect, ...]
    residual_scratch_paths: tuple[str, ...]
    cleanup_diagnostics: tuple[str, ...]
    durability_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class PackageCleanupObservation:
    """Detached original-holder history, never freshness or write authority."""

    root_locator: str
    target_path: str
    scratch_path: str
    attempted: bool
    outcome: str
    evidence: PackagePhysicalEvidence


@dataclass(frozen=True, slots=True)
class PackagePlanBinding:
    """Inspection from an original entrance, not a portable write permit."""

    root_locator: str
    root_identity: tuple[int, int, int]
    parent_path: str
    parent_identity: tuple[int, int, int]
    namespace_identity: tuple[int, int]
    target_path: str
    scratch_path: str
    ordered_members: tuple[tuple[str, bytes], ...]


class PackagePublicationRefusal(RuntimeError):
    def __init__(self, code: str, evidence: PackagePhysicalEvidence | None = None):
        super().__init__(code)
        self.code = code
        self.evidence = evidence or PackagePhysicalEvidence("none", (), (), ())


@dataclass(frozen=True, slots=True)
class PackageInputObservation:
    """Historical custody evidence; never a cleanup or publication capability."""

    attempt_ref: str
    client_intent_id: str
    resource_state: str
    transfer_state: str
    release_invocation: str
    owner_cleanup_attempted: bool | None
    owner_cleanup_outcome: str
    diagnostics: tuple[str, ...]
    binding: PackagePlanBinding | None
    cleanup: PackageCleanupObservation | None


class PackageInputCustodyRefusal(PackagePublicationRefusal):
    def __init__(self, code: str, *, input_observation: PackageInputObservation | None):
        cleanup = None if input_observation is None else input_observation.cleanup
        super().__init__(
            code,
            PackagePhysicalEvidence("unknown", (), (), ())
            if cleanup is None
            else cleanup.evidence,
        )
        self.input_observation = input_observation


class PackageInputReservation:
    """Original cleanup-only custody. Receiver authenticity belongs to Issue."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use reserve_package_input")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Original reservation cannot be subclassed")

    def __copy__(self):
        raise TypeError("Reservation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Reservation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Reservation cannot be serialized")


class PackageInputClaim:
    """Original transferred claim, correlated to one plan and opaque receiver."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use transfer_package_input")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Original claim cannot be subclassed")

    def __copy__(self):
        raise TypeError("Claim cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Claim cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Claim cannot be serialized")


@dataclass
class _InputRecord:
    attempt_ref: str
    client_intent_id: str
    binding: PackagePlanBinding
    resource_state: str = "reserved"
    transfer_state: str = "not_attempted"
    release_invocation: str = "not_invoked"
    receiver: object = None
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class _InputEntry:
    # Only live original capabilities retain the plan. The record stored on
    # its state has no backlink to a capability/plan, avoiding weak-key cycles.
    plan: object
    record: _InputRecord
    role: str


@dataclass
class _Entry:
    observed: os.stat_result
    body: bytes | None


@dataclass
class _State:
    root: Path
    target: str
    scratch: str
    members: tuple[tuple[str, bytes], ...]
    namespace: tuple[int, int]
    fds: dict[str, int] = field(default_factory=dict)
    ancestors: dict[str, os.stat_result] = field(default_factory=dict)
    entries: dict[str, _Entry] = field(default_factory=dict)
    effects: list[RetainedPhysicalEffect] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    residual: set[str] = field(default_factory=set)
    pid: int = field(default_factory=os.getpid)
    phase: str = "planned"
    outcome: str = "none"
    cleanup_attempted: bool = False
    cleanup_outcome: str = "not_attempted"
    lock: threading.RLock = field(default_factory=threading.RLock)
    provenance: object = field(default_factory=object)
    input_custody: _InputRecord | None = None


def _path(value: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or "\\" in value
        or unicodedata.normalize("NFC", value) != value
        or any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F for c in value)
    ):
        raise ValueError("Canonical package-relative path required")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("UTF-8 path required") from error
    parsed = PurePosixPath(value)
    if (
        parsed.is_absolute()
        or ".." in parsed.parts
        or str(parsed) != value
        or value == "."
        or len(encoded) > 1024
    ):
        raise ValueError("Bounded canonical package-relative path required")
    return value


def _identity(value):
    return value.st_dev, value.st_ino, value.st_mode


def _signature(value):
    return (
        *_identity(value),
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_nlink,
    )


def _digest(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _namespace():
    value = os.stat("/proc/self/ns/mnt")
    return value.st_dev, value.st_ino


def _evidence(state):
    return PackagePhysicalEvidence(
        state.outcome,
        tuple(state.effects),
        tuple(sorted(state.residual)),
        tuple(state.diagnostics),
    )


def _record(state, path, kind, status, observed=None, body=None):
    state.effects.append(
        RetainedPhysicalEffect(
            path,
            kind,
            status,
            mode=None if observed is None else stat.S_IMODE(observed.st_mode),
            after_digest=None if body is None else _digest(body),
            after_identity=None
            if observed is None
            else (observed.st_dev, observed.st_ino),
        )
    )


def _parent(path):
    value = str(PurePosixPath(path).parent)
    return "" if value == "." else value


def _absence(state, path):
    try:
        os.stat(
            PurePosixPath(path).name,
            dir_fd=state.fds[_parent(path)],
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    raise PackagePublicationRefusal("package_name_occupied")


def _topology(state):
    if _namespace() != state.namespace:
        raise PackagePublicationRefusal("package_mount_namespace_changed")
    root = state.ancestors[""]
    if _identity(os.stat(state.root, follow_symlinks=False)) != _identity(root):
        raise PackagePublicationRefusal("package_root_changed")
    for path, expected in state.ancestors.items():
        current = os.fstat(state.fds[path])
        if _identity(current) != _identity(expected):
            raise PackagePublicationRefusal("package_parent_changed")
        if path and _identity(
            os.stat(
                PurePosixPath(path).name,
                dir_fd=state.fds[_parent(path)],
                follow_symlinks=False,
            )
        ) != _identity(expected):
            raise PackagePublicationRefusal("package_parent_changed")


def _read(parent_fd, name):
    descriptor = os.open(
        name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd
    )
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > 2 * 1024 * 1024
        ):
            raise PackagePublicationRefusal("package_member_not_regular")
        chunks = []
        remaining = 2 * 1024 * 1024 + 1
        while remaining:
            body = os.read(descriptor, min(remaining, 65536))
            if not body:
                break
            chunks.append(body)
            remaining -= len(body)
        after = os.fstat(descriptor)
        body = b"".join(chunks)
        if _signature(before) != _signature(after) or len(body) > 2 * 1024 * 1024:
            raise PackagePublicationRefusal("package_member_changed_during_read")
        return body, after
    finally:
        os.close(descriptor)


def _current_name(state, path):
    return (
        PurePosixPath(state.target).name
        if path == state.scratch and state.outcome == "published"
        else PurePosixPath(path).name
    )


def _check_entry(state, path, entry):
    parent_fd = state.fds[_parent(path)]
    name = _current_name(state, path)
    current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if _identity(current) != _identity(entry.observed):
        raise PackagePublicationRefusal("package_entry_substituted")
    if entry.body is not None:
        body, current = _read(parent_fd, name)
        if body != entry.body or _signature(current) != _signature(entry.observed):
            raise PackagePublicationRefusal("package_member_postimage_changed")
    elif _identity(os.fstat(state.fds[path])) != _identity(entry.observed):
        raise PackagePublicationRefusal("package_directory_substituted")


def _verify(state):
    _topology(state)
    if state.outcome != "published":
        _absence(state, state.target)
    for path, entry in state.entries.items():
        _check_entry(state, path, entry)
    if state.phase == "staged" or state.outcome == "published":
        for directory, entry in state.entries.items():
            if directory not in state.fds or entry.body is not None:
                continue
            expected = {
                PurePosixPath(path).name
                for path in state.entries
                if _parent(path) == directory
            }
            with os.scandir(state.fds[directory]) as listing:
                for item in listing:
                    if item.name not in expected:
                        raise PackagePublicationRefusal("package_foreign_entry")
                    expected.remove(item.name)
            if expected:
                raise PackagePublicationRefusal("package_member_missing")


def _close_all(state):
    descriptors, state.fds = state.fds, {}
    for descriptor in reversed(tuple(descriptors.values())):
        try:
            os.close(descriptor)
        except BaseException as error:  # noqa: BLE001 - attempt all descriptor releases after interruption
            state.diagnostics.append("descriptor_close:" + type(error).__name__)


def _cleanup(state):
    if state.outcome == "published":
        return
    try:
        _topology(state)
    except BaseException as error:  # noqa: BLE001 - never clean relocated topology after interruption
        state.diagnostics.append("cleanup_topology:" + type(error).__name__)
        return
    original_root = state.entries.get(state.scratch)
    if original_root is None:
        return
    try:
        _check_entry(state, state.scratch, original_root)
    except FileNotFoundError:
        # Unknown rename may have moved the owned tree to the public target.
        # Never clean it through still-live child descriptors in that case.
        state.residual.clear()
        return
    except BaseException as error:  # noqa: BLE001 - scratch identity is required before any deletion
        state.diagnostics.append("cleanup_stage_identity:" + type(error).__name__)
        return
    for path, entry in sorted(
        state.entries.items(),
        key=lambda item: (item[0].count("/"), item[0]),
        reverse=True,
    ):
        try:
            _check_entry(state, path, entry)
            kind = "cleanup_file" if entry.body is not None else "cleanup_directory"
            _record(state, path, kind, ConfinedMutationEffectState.UNKNOWN)
            operation = os.unlink if entry.body is not None else os.rmdir
            operation(PurePosixPath(path).name, dir_fd=state.fds[_parent(path)])
            _record(state, path, kind, ConfinedMutationEffectState.APPLIED)
            state.residual.discard(path)
        except FileNotFoundError:
            state.residual.discard(path)
        except BaseException as error:  # noqa: BLE001 - preserve residue and continue bounded cleanup
            state.diagnostics.append(path + ":" + type(error).__name__)


def _cleanup_once(state):
    if state.cleanup_attempted:
        return
    state.cleanup_attempted = True
    state.cleanup_outcome = "unknown"
    try:
        _cleanup(state)
    except BaseException as error:  # noqa: BLE001 - preserve interruption and still attempt descriptor cleanup
        state.diagnostics.append("cleanup_failed:" + type(error).__name__)
    finally:
        try:
            _close_all(state)
        except BaseException as error:  # noqa: BLE001 - never retry an ambiguous descriptor close
            state.diagnostics.append(
                "descriptor_cleanup_failed:" + type(error).__name__
            )
    state.cleanup_outcome = (
        "incomplete"
        if state.diagnostics or state.residual or state.fds
        else "completed"
    )


def _retire(state, code, cause=None):
    state.phase = "retired"
    _cleanup_once(state)
    raise PackagePublicationRefusal(code, _evidence(state)) from cause


def _historical_binding(state):
    parent = _parent(state.target)
    return PackagePlanBinding(
        str(state.root),
        _identity(state.ancestors[""]),
        parent,
        _identity(state.ancestors[parent]),
        state.namespace,
        state.target,
        state.scratch,
        state.members,
    )


def _cleanup_observation(state):
    return PackageCleanupObservation(
        str(state.root),
        state.target,
        state.scratch,
        state.cleanup_attempted,
        state.cleanup_outcome,
        _evidence(state),
    )


def _input_observation(state, record):
    return PackageInputObservation(
        record.attempt_ref,
        record.client_intent_id,
        record.resource_state,
        record.transfer_state,
        record.release_invocation,
        state.cleanup_attempted,
        state.cleanup_outcome,
        tuple(record.diagnostics),
        record.binding,
        _cleanup_observation(state),
    )


def _input_refusal(code, state=None):
    observation = None
    if state is not None and state.input_custody is not None:
        try:
            observation = _input_observation(state, state.input_custody)
        except BaseException:  # noqa: BLE001 - unavailable evidence must stay unknown
            observation = None
    return PackageInputCustodyRefusal(
        code,
        input_observation=observation,
    )


def _local_input_entry(value):
    entry = (
        _INPUTS.get(value)
        if type(value) in {PackageInputReservation, PackageInputClaim}
        else None
    )
    if entry is None:
        raise _input_refusal("original_package_input_required")
    state = _HANDLES.get(entry.plan)
    if state is None or state.pid != os.getpid():
        # In particular, a fork refusal does not retire the parent's holder.
        raise _input_refusal("package_input_foreign_process")
    return entry, state


def _guard_input(state, claim):
    record = state.input_custody
    if record is None:
        if claim is not None:
            raise _input_refusal("unexpected_package_input_claim")
        return
    entry = _INPUTS.get(claim) if type(claim) is PackageInputClaim else None
    if (
        entry is None
        or entry.role != "claim"
        or entry.record is not record
        or _HANDLES.get(entry.plan) is not state
        or record.transfer_state != "completed"
    ):
        raise _input_refusal("package_input_claim_required", state)
    # A spent original claim may observe/release idempotently. Currentness and
    # staging still pass through the original terminal checks, never renewal.


def _release_input_state(state, record):
    if record.release_invocation != "not_invoked":
        return
    record.release_invocation = "invoked"
    record.resource_state = "released"
    try:
        _cleanup_once(state)
        state.phase = "released"
        record.release_invocation = "returned"
    except BaseException as error:  # noqa: BLE001 - retain release interruption evidence
        state.phase = "released"
        record.release_invocation = "raised"
        record.diagnostics.append("input_release:" + type(error).__name__)


def _abandon_input(entry):
    state = _HANDLES.get(entry.plan)
    if state is None or state.pid != os.getpid():
        return
    with state.lock:
        if entry.role == "reservation" and entry.record.transfer_state == "completed":
            return  # Cleanup authority moved; old reservation collection is inert.
        _release_input_state(state, entry.record)


def _correlation(value):
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or unicodedata.normalize("NFC", value) != value
        or any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F for c in value)
    ):
        raise ValueError("Bounded exact custody correlation required")
    if len(value.encode("utf-8")) > 1024:
        raise ValueError("Bounded exact custody correlation required")
    return value


def reserve_package_input(
    plan, *, attempt_ref: str, client_intent_id: str
) -> PackageInputReservation:
    attempt_ref = _correlation(attempt_ref)
    client_intent_id = _correlation(client_intent_id)
    state = _HANDLES.get(plan) if type(plan) is RetainedPackagePublication else None
    if state is None or state.pid != os.getpid():
        raise _input_refusal("original_local_package_input_required")
    with state.lock:
        if state.input_custody is not None:
            raise _input_refusal("package_input_already_owned", state)
        if state.phase not in {"planned", "retired", "released"}:
            raise _input_refusal("package_input_already_spent")
        record = _InputRecord(attempt_ref, client_intent_id, _historical_binding(state))
        state.input_custody = record
        try:
            reservation = object.__new__(PackageInputReservation)
            entry = _InputEntry(plan, record, "reservation")
            _INPUTS[reservation] = entry
            finalize(reservation, _abandon_input, entry)
            return reservation
        except BaseException as error:
            # Only this call's positively acquired original is disposed.
            record.diagnostics.append("input_issuance:" + type(error).__name__)
            _release_input_state(state, record)
            raise _input_refusal("package_input_reservation_failed", state) from error


def observe_package_input(value: object) -> PackageInputObservation:
    entry, state = _local_input_entry(value)
    with state.lock:
        try:
            return _input_observation(state, entry.record)
        except BaseException as error:
            raise PackageInputCustodyRefusal(
                "package_input_observation_unavailable", input_observation=None
            ) from error


def transfer_package_input(
    reservation: object, *, receiver: object
) -> PackageInputClaim:
    entry, state = _local_input_entry(reservation)
    if type(reservation) is not PackageInputReservation or entry.role != "reservation":
        raise _input_refusal("original_package_reservation_required")
    if receiver is None:
        raise ValueError("Opaque receiver identity required")
    with state.lock:
        record = entry.record
        if (
            record.resource_state != "reserved"
            or record.transfer_state != "not_attempted"
        ):
            raise _input_refusal("package_input_transfer_replay", state)
        if state.phase != "planned" or state.cleanup_attempted:
            raise _input_refusal("package_input_cleanup_only", state)
        record.transfer_state = "attempted"
        try:
            claim = object.__new__(PackageInputClaim)
            claimed = _InputEntry(entry.plan, record, "claim")
            _INPUTS[claim] = claimed
            finalize(claim, _abandon_input, claimed)
            record.receiver = receiver
            record.transfer_state = "completed"
            record.resource_state = "transferred"
            return claim
        except BaseException as error:
            record.diagnostics.append("input_transfer:" + type(error).__name__)
            _release_input_state(state, record)
            raise _input_refusal("package_input_transfer_failed", state) from error


def require_package_input_claim(value, *, plan, receiver) -> PackageInputClaim:
    entry, state = _local_input_entry(value)
    with state.lock:
        _guard_input(state, value)
        if (
            entry.plan is not plan
            or entry.record.receiver is not receiver
            or entry.record.resource_state != "transferred"
        ):
            raise _input_refusal("package_input_claim_mismatch", state)
        return value


def release_package_input(value: object) -> PackageInputObservation:
    entry, state = _local_input_entry(value)
    with state.lock:
        record = entry.record
        if entry.role == "reservation" and record.transfer_state == "completed":
            raise _input_refusal("package_input_cleanup_transferred", state)
        _release_input_state(state, record)
        try:
            observation = _input_observation(state, record)
        except BaseException as error:
            raise PackageInputCustodyRefusal(
                "package_input_release_observation_unavailable", input_observation=None
            ) from error
        if (
            state.cleanup_outcome != "completed"
            or record.release_invocation == "raised"
        ):
            raise PackageInputCustodyRefusal(
                "package_input_release_incomplete", input_observation=observation
            )
        return observation


def _issued(handle):
    state = _HANDLES.get(handle) if type(handle) is RetainedPackagePublication else None
    if state is None:
        raise PackagePublicationRefusal("original_package_handle_required")
    if state.pid != os.getpid():
        if state.input_custody is not None:
            raise _input_refusal("package_input_foreign_process")
        state.phase = "retired"
        _close_all(state)
        raise PackagePublicationRefusal("package_foreign_process", _evidence(state))
    return state


def _check(state):
    if state.phase in {"retired", "released", "consumed"}:
        raise PackagePublicationRefusal("package_handle_terminal", _evidence(state))
    try:
        _verify(state)
    except BaseException as error:  # noqa: BLE001 - interruption irreversibly retires authority
        _retire(state, getattr(error, "code", "package_currentness_failed"), error)


class _RenameRefusal(RuntimeError):
    pass


def _rename_no_replace(parent_fd, source, target):
    library = ctypes.CDLL(None, use_errno=True)
    try:
        operation = library.renameat2
    except AttributeError as error:
        raise _RenameRefusal("atomic_package_publication_unavailable") from error
    operation.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    operation.restype = ctypes.c_int
    if operation(parent_fd, os.fsencode(source), parent_fd, os.fsencode(target), 1):
        number = ctypes.get_errno()
        if number in {errno.EEXIST, errno.ENOTEMPTY}:
            raise _RenameRefusal("package_name_occupied")
        if number in {errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP}:
            raise _RenameRefusal("atomic_package_publication_unavailable")
        raise OSError(number, os.strerror(number))


class PackagePublicationPostimage:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original package publisher")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Original postimage type cannot be subclassed")

    def __copy__(self):
        raise TypeError("Postimage cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Postimage cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Postimage cannot be serialized")


class RetainedPackagePublication:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use retain_package_publication")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Original package handle cannot be subclassed")

    def __copy__(self):
        raise TypeError("Package handle cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Package handle cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Package handle cannot be serialized")

    @property
    def phase(self):
        return _issued(self).phase

    @property
    def evidence(self):
        state = _issued(self)
        with state.lock:
            # A snapshot is one coherent point in this original attempt's
            # history, including retirement/cleanup; never a live write permit.
            return _evidence(state)

    @property
    def scratch_path(self):
        return _issued(self).scratch

    def validate_current(self, *, input_claim=None):
        state = _issued(self)
        with state.lock:
            _guard_input(state, input_claim)
            _check(state)

    def stage(self, *, input_claim=None):
        state = _issued(self)
        with state.lock:
            _guard_input(state, input_claim)
            _check(state)
            if state.phase != "planned":
                _retire(state, "package_stage_replay")
            while state.phase != "staged":
                self.stage_next_effect(input_claim=input_claim)
            return self.lend_staged_source(input_claim=input_claim)

    def stage_next_effect(self, *, input_claim=None):
        """One mkdir, exclusive file-create or write submission per entrance.

        Issue can revalidate its original authority before every step without
        passing FileSystem an arbitrary callback or claiming a bulk-call guard.
        Completion can return None: it validates, but performs no source effect.
        """
        state = _issued(self)
        with state.lock:
            _guard_input(state, input_claim)
            _check(state)
            if state.phase not in {"planned", "staging_spent"}:
                _retire(state, "package_stage_replay")
            state.phase = "staging_spent"
            try:
                if state.scratch not in state.entries:
                    _absence(state, state.scratch)
                    _make_directory(state, state.scratch, 0o700)
                    return state.effects[-1]
                directories = {
                    str(parent)
                    for path, _ in state.members
                    for parent in PurePosixPath(path).parents
                    if str(parent) != "."
                }
                for relative in sorted(
                    directories, key=lambda path: (path.count("/"), path)
                ):
                    path = state.scratch + "/" + relative
                    if path not in state.entries:
                        _make_directory(state, path, 0o755)
                        return state.effects[-1]
                for relative, body in state.members:
                    path = state.scratch + "/" + relative
                    if path not in state.entries:
                        _create_file(state, path)
                        return state.effects[-1]
                    entry = state.entries[path]
                    if len(entry.body) < len(body):
                        _write_file(state, path, body)
                        return state.effects[-1]
                    if path in state.fds:
                        descriptor = state.fds.pop(path)
                        os.close(descriptor)
                state.phase = "staged"
                _check(state)
                return None
            except BaseException as error:
                if state.phase == "retired":
                    raise
                _retire(state, getattr(error, "code", "package_staging_failed"), error)

    def lend_staged_source(self, *, input_claim=None):
        state = _issued(self)
        with state.lock:
            _guard_input(state, input_claim)
            _check(state)
            if state.phase != "staged":
                _retire(state, "package_stage_required")
            lens = object.__new__(StagedPackageSource)
            _LENSES[lens] = self
            _LENS_CLAIMS[lens] = input_claim
            return lens

    def publish_package(self, *, input_claim=None):
        state = _issued(self)
        with state.lock:
            _guard_input(state, input_claim)
            _check(state)
            if state.phase != "staged":
                _retire(state, "package_stage_required")
            state.phase = "publication_spent"
            state.outcome = "unknown"
            _record(
                state,
                state.target,
                "package_publication",
                ConfinedMutationEffectState.UNKNOWN,
            )
            try:
                try:
                    _rename_no_replace(
                        state.fds[_parent(state.target)],
                        PurePosixPath(state.scratch).name,
                        PurePosixPath(state.target).name,
                    )
                except _RenameRefusal as error:
                    state.outcome = "none"
                    _record(
                        state,
                        state.target,
                        "package_publication",
                        ConfinedMutationEffectState.NONE,
                    )
                    raise PackagePublicationRefusal(str(error)) from error
                state.outcome = "published"
                state.residual.clear()
                _record(
                    state,
                    state.target,
                    "package_publication",
                    ConfinedMutationEffectState.APPLIED,
                )
                state.phase = "published"
                _check(state)
                _record(
                    state,
                    state.target,
                    "package_postimage",
                    ConfinedMutationEffectState.APPLIED,
                    state.entries[state.scratch].observed,
                )
                image = object.__new__(PackagePublicationPostimage)
                _POSTIMAGES[image] = (self, state)
                return image
            except BaseException as error:
                if state.phase == "retired":
                    raise
                _retire(
                    state, getattr(error, "code", "package_publication_failed"), error
                )

    def finish(self, postimage, *, input_claim=None):
        state = _issued(self)
        with state.lock:
            _guard_input(state, input_claim)
            validate_package_postimage(self, postimage, input_claim=input_claim)
            if state.phase != "published":
                raise PackagePublicationRefusal(
                    "package_completion_replay", _evidence(state)
                )
            state.phase = "consumed"
            # Retain read-only correlation until explicit release at the return
            # horizon. Consumption never renews staging/publication authority.
            return _evidence(state)

    def release(self, *, input_claim=None):
        state = _issued(self)
        with state.lock:
            _guard_input(state, input_claim)
            if state.input_custody is not None:
                release_package_input(input_claim)
                return _evidence(state)
            _cleanup_once(state)
            state.phase = "released"
            return _evidence(state)

    def observe_cleanup(self) -> PackageCleanupObservation:
        return observe_package_cleanup(self)


class StagedPackageSource:
    """Original staged lens; duplicated descriptors belong to the borrower."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original publisher's staged source entrance")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Staged source cannot be subclassed")

    def __copy__(self):
        raise TypeError("Staged source cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Staged source cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Staged source cannot be serialized")

    def duplicate_parent_descriptor(self):
        handle = _LENSES.get(self) if type(self) is StagedPackageSource else None
        if handle is None:
            raise PackagePublicationRefusal("original_staged_source_required")
        state = _issued(handle)
        with state.lock:
            _guard_input(state, _LENS_CLAIMS.get(self))
            _check(state)
            if state.phase != "staged":
                _retire(state, "staged_source_terminal")
            return os.dup(state.fds[_parent(state.scratch)])

    @property
    def stage_name(self):
        handle = _LENSES.get(self) if type(self) is StagedPackageSource else None
        if handle is None:
            raise PackagePublicationRefusal("original_staged_source_required")
        state = _issued(handle)
        with state.lock:
            _guard_input(state, _LENS_CLAIMS.get(self))
            _check(state)
            if state.phase != "staged":
                _retire(state, "staged_source_terminal")
            return PurePosixPath(state.scratch).name


def _make_directory(state, path, mode):
    parent_fd = state.fds[_parent(path)]
    state.residual.add(path)
    _record(state, path, "directory", ConfinedMutationEffectState.UNKNOWN)
    os.mkdir(PurePosixPath(path).name, mode=mode, dir_fd=parent_fd)
    _record(state, path, "directory", ConfinedMutationEffectState.APPLIED)
    descriptor = os.open(PurePosixPath(path).name, _FLAGS, dir_fd=parent_fd)
    state.fds[path] = descriptor
    value = os.fstat(descriptor)
    state.entries[path] = _Entry(value, None)
    _record(state, path, "directory", ConfinedMutationEffectState.APPLIED, value)
    if value.st_dev != state.ancestors[""].st_dev or (
        path == state.scratch and stat.S_IMODE(value.st_mode) & 0o077
    ):
        raise PackagePublicationRefusal("package_private_stage_unavailable")


def _create_file(state, path):
    parent_fd = state.fds[_parent(path)]
    state.residual.add(path)
    _record(state, path, "file", ConfinedMutationEffectState.UNKNOWN)
    descriptor = os.open(
        PurePosixPath(path).name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o644,
        dir_fd=parent_fd,
    )
    state.fds[path] = descriptor
    value = os.fstat(descriptor)
    state.entries[path] = _Entry(value, b"")
    _record(state, path, "file", ConfinedMutationEffectState.APPLIED, value, b"")


def _write_file(state, path, body):
    descriptor = state.fds[path]
    position = len(state.entries[path].body)
    _record(state, path, "file_write", ConfinedMutationEffectState.UNKNOWN)
    amount = os.write(descriptor, memoryview(body)[position:])
    if amount <= 0:
        raise OSError("Package write made no progress")
    position += amount
    value = os.fstat(descriptor)
    state.entries[path] = _Entry(value, body[:position])
    _record(
        state,
        path,
        "file_write",
        ConfinedMutationEffectState.APPLIED,
        value,
        body[:position],
    )


def validate_package_plan(
    handle,
    *,
    root: Path,
    target_path: str,
    scratch_path: str,
    ordered_members: tuple[tuple[str, bytes], ...],
    input_claim=None,
):
    state = _issued(handle)
    with state.lock:
        _guard_input(state, input_claim)
        _check(state)
        if (state.root, state.target, state.scratch, state.members) != (
            root.absolute(),
            target_path,
            scratch_path,
            ordered_members,
        ):
            _retire(state, "package_plan_binding_mismatch")


def observe_package_plan(handle, *, input_claim=None):
    state = _issued(handle)
    with state.lock:
        _guard_input(state, input_claim)
        _check(state)
        return _historical_binding(state)


def validate_staged_package_source(handle, lens, *, input_claim=None):
    state = _issued(handle)
    with state.lock:
        _guard_input(state, input_claim)
        if type(lens) is not StagedPackageSource or _LENSES.get(lens) is not handle:
            _retire(state, "foreign_staged_source")
        _check(state)
        if state.phase != "staged":
            _retire(state, "staged_source_terminal")


def validate_package_postimage(handle, image, *, input_claim=None):
    state = _issued(handle)
    with state.lock:
        _guard_input(state, input_claim)
        if type(image) is not PackagePublicationPostimage or _POSTIMAGES.get(image) != (
            handle,
            state,
        ):
            _retire(state, "original_publication_postimage_required")
        if state.phase not in {"published", "consumed"} or state.outcome != "published":
            raise PackagePublicationRefusal(
                "package_postimage_terminal", _evidence(state)
            )
        try:
            _verify(state)
        except BaseException as error:  # noqa: BLE001 - preserve applied effects on interrupted postimage validation
            _retire(state, getattr(error, "code", "package_postimage_changed"), error)


def _abandon(state):
    with state.lock:
        if state.pid != os.getpid():
            _close_all(state)  # Foreign processes never delete the parent's scratch.
            return
        _cleanup_once(state)
        state.phase = "released"


def observe_package_cleanup(value: object) -> PackageCleanupObservation:
    # Unlike currentness validation, observation must not retire or close a
    # holder just because observation fails (including in a fork).
    state = _HANDLES.get(value) if type(value) is RetainedPackagePublication else None
    if state is None or state.pid != os.getpid():
        raise PackagePublicationRefusal("original_local_package_observation_required")
    with state.lock:
        return PackageCleanupObservation(
            str(state.root),
            state.target,
            state.scratch,
            state.cleanup_attempted,
            state.cleanup_outcome,
            _evidence(state),
        )


def require_retained_package_plan(
    value: object, *, input_claim=None
) -> RetainedPackagePublication:
    """Original live plan check, including consumed read-only correlation."""
    state = _issued(value)
    with state.lock:
        _guard_input(state, input_claim)
        if state.phase == "consumed":
            try:
                _verify(state)
            except BaseException as error:  # noqa: BLE001 - interruption retires authority
                _retire(
                    state, getattr(error, "code", "package_currentness_failed"), error
                )
        else:
            _check(state)
        return value


def require_retained_package_postimage(
    value: object, *, plan: object, input_claim=None
) -> PackagePublicationPostimage:
    validate_package_postimage(plan, value, input_claim=input_claim)
    return value


def _read_issued(value):
    state = _READERS.get(value) if type(value) is RetainedPackageReadPostimage else None
    if state is None:
        raise PackagePublicationRefusal("original_package_reader_required")
    if state.pid != os.getpid():
        with state.lock:
            state.phase = "retired"
            _close_all(state)
        raise PackagePublicationRefusal(
            "package_reader_foreign_process", _evidence(state)
        )
    return state


def _read_check(state):
    if state.phase != "read_current":
        raise PackagePublicationRefusal("package_reader_terminal", _evidence(state))
    try:
        _verify(state)
    except BaseException as error:
        state.phase = "retired"
        # A reader never owns source cleanup, even on a verification failure.
        _close_all(state)
        raise PackagePublicationRefusal(
            getattr(error, "code", "package_reader_currentness_failed"),
            _evidence(state),
        ) from error


def _abandon_reader(state):
    with state.lock:
        _close_all(state)
        state.phase = "released"


class RetainedPackageReadPostimage:
    """Independent original read-only provenance/descriptor lifetime.

    No publication, staging, Issue grant or shared mutable writer state. An
    escaped copy of portable evidence cannot issue or restore this holder.
    """

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use retain_package_postimage_read")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Original package reader cannot be subclassed")

    def __copy__(self):
        raise TypeError("Package reader cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Package reader cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Package reader cannot be serialized")

    @property
    def phase(self):
        state = _read_issued(self)
        with state.lock:
            return state.phase

    def validate_current(self) -> None:
        state = _read_issued(self)
        with state.lock:
            _read_check(state)

    def observe_binding(self) -> PackagePlanBinding:
        state = _read_issued(self)
        with state.lock:
            _read_check(state)
            parent = _parent(state.target)
            return PackagePlanBinding(
                str(state.root),
                _identity(state.ancestors[""]),
                parent,
                _identity(state.ancestors[parent]),
                state.namespace,
                state.target,
                state.scratch,
                state.members,
            )

    def duplicate_package_descriptor(self) -> int:
        state = _read_issued(self)
        with state.lock:
            _read_check(state)
            return os.dup(state.fds[state.scratch])

    def release(self) -> None:
        state = _read_issued(self)
        with state.lock:
            if state.phase == "released":
                return
            before = len(state.diagnostics)
            _close_all(state)
            state.phase = "released"
            if len(state.diagnostics) != before:
                raise PackagePublicationRefusal(
                    "package_reader_release_incomplete", _evidence(state)
                )


def retain_package_postimage_read(
    value: object, *, input_claim=None
) -> RetainedPackageReadPostimage:
    """Fork from known original applied publication, never ordinary observation."""
    origin = (
        _POSTIMAGES.get(value) if type(value) is PackagePublicationPostimage else None
    )
    if origin is None:
        raise PackagePublicationRefusal("original_publication_postimage_required")
    plan, source = origin
    if _issued(plan) is not source:
        raise PackagePublicationRefusal("original_publication_postimage_required")
    with source.lock:
        _guard_input(source, input_claim)
        validate_package_postimage(plan, value, input_claim=input_claim)
        retained = _State(
            source.root,
            source.target,
            source.scratch,
            source.members,
            source.namespace,
            ancestors=dict(source.ancestors),
            entries={
                path: _Entry(entry.observed, entry.body)
                for path, entry in source.entries.items()
            },
            effects=list(source.effects),
            phase="read_current",
            outcome="published",
            provenance=source.provenance,
        )
        try:
            for path, descriptor in source.fds.items():
                retained.fds[path] = os.dup(descriptor)
            # Check both sides after all duplications; an ordinary appeared
            # tree cannot replace original correlated provenance.
            validate_package_postimage(plan, value, input_claim=input_claim)
            _verify(retained)
            reader = object.__new__(RetainedPackageReadPostimage)
            _READERS[reader] = retained
            finalize(reader, _abandon_reader, retained)
            return reader
        except BaseException as error:
            _close_all(retained)
            retained.phase = "retired"
            raise PackagePublicationRefusal(
                getattr(error, "code", "package_read_retention_failed"),
                _evidence(retained),
            ) from error


def require_package_postimage_read(value: object) -> RetainedPackageReadPostimage:
    state = _read_issued(value)
    with state.lock:
        _read_check(state)
        return value


def validate_package_postimage_read(value: object, *, plan: object) -> None:
    """Join genuine reader provenance to its original plan, even after release."""
    source = _issued(plan)
    state = _read_issued(value)
    with state.lock:
        _read_check(state)
        if state.provenance is not source.provenance:
            state.phase = "retired"
            _close_all(state)
            raise PackagePublicationRefusal(
                "foreign_package_reader_provenance", _evidence(state)
            )


def release_package_postimage_read(value: object) -> None:
    # Exact original object validation remains separate from currentness:
    # cleanup must still work after a verification refusal.
    _read_issued(value)
    value.release()


def retain_package_publication(
    *,
    root: Path,
    target_path: str,
    ordered_members: tuple[tuple[str, bytes], ...],
    scratch_path: str | None = None,
):
    target = _path(target_path)
    members = ordered_members
    if type(members) is not tuple or not 1 <= len(members) <= 4096:
        raise ValueError("Nonempty bounded immutable members required")
    files = set()
    total = 0
    prior = None
    for member in members:
        if type(member) is not tuple or len(member) != 2:
            raise ValueError("Exact member pair required")
        path, body = member
        _path(path)
        if (
            type(body) is not bytes
            or len(body) > 2 * 1024 * 1024
            or (prior is not None and path <= prior)
        ):
            raise ValueError("Bounded uniquely sorted exact member bytes required")
        prior = path
        files.add(path)
        total += len(body)
    if total > 64 * 1024 * 1024 or any(
        str(parent) in files for path in files for parent in PurePosixPath(path).parents
    ):
        raise ValueError("Member conflict or total bytes exceeded")
    parent = _parent(target)
    scratch = (
        _path(scratch_path)
        if scratch_path is not None
        else ((parent + "/") if parent else "")
        + ".aware-spec-draft-"
        + secrets.token_hex(16)
    )
    suffix = PurePosixPath(scratch).name.removeprefix(".aware-spec-draft-")
    if (
        _parent(scratch) != parent
        or scratch == target
        or len(suffix) != 32
        or any(c not in "0123456789abcdef" for c in suffix)
        or not PurePosixPath(scratch).name.startswith(".aware-spec-draft-")
    ):
        raise ValueError("Distinct same-parent private scratch required")
    state = _State(root.absolute(), target, scratch, tuple(members), _namespace())
    try:
        state.fds[""] = os.open(state.root, _FLAGS)
        state.ancestors[""] = os.fstat(state.fds[""])
        if parent:
            current = ""
            for part in PurePosixPath(parent).parts:
                following = current + "/" + part if current else part
                state.fds[following] = os.open(part, _FLAGS, dir_fd=state.fds[current])
                value = os.fstat(state.fds[following])
                if value.st_dev != state.ancestors[""].st_dev:
                    raise PackagePublicationRefusal("package_mount_boundary")
                state.ancestors[following] = value
                current = following
        _topology(state)
        _absence(state, target)
        _absence(state, scratch)
        handle = object.__new__(RetainedPackagePublication)
        _HANDLES[handle] = state
        finalize(handle, _abandon, state)
        return handle
    except BaseException as error:
        _close_all(state)
        raise PackagePublicationRefusal(
            getattr(error, "code", "package_plan_failed"), _evidence(state)
        ) from error
