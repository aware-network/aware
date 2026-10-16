"""Original retained CREATE/UPDATE sequence; no Issue policy or caller callbacks."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
import threading
import weakref
from dataclasses import dataclass, field, fields, replace
from pathlib import Path, PurePosixPath
from types import MethodType
from typing import Any, Literal, cast
from unicodedata import normalize
from uuid import uuid4

from . import confined_mutation as native

Confinement = Literal["descriptor_walk_v1"]

DispatchState = Literal["not_attempted", "attempted", "returned"]

DurabilityState = Literal["not_confirmed", "confirmed", "unknown"]

EffectState = Literal["none", "applied", "unknown"]

FileKind = Literal["create", "update"]

ModePolicy = Literal["legacy_kernel_umask_restore_existing_v1"]

ObservationState = Literal["not_observed", "observed", "unavailable"]

Ownership = Literal["owned", "borrowed", "released", "unknown"]

Phase = Literal[
    "preparing",
    "prepared",
    "admitted",
    "enrolled",
    "spent",
    "executing",
    "completed",
    "retired",
]

PrimaryFailureState = Literal["none", "observed", "unknown"]

ReleaseOutcome = Literal["confirmed", "failed", "unknown"]

ResourceKind = Literal[
    "root_descriptor",
    "directory_descriptor",
    "file_descriptor",
    "scratch_descriptor",
    "lease",
    "logical_keeper",
    "temporary_buffer",
]

StepKind = Literal[
    "ancestor_create",
    "ancestor_sync",
    "scratch_create",
    "scratch_write",
    "scratch_restore_mode",
    "scratch_sync",
    "scratch_close",
    "target_link",
    "scratch_unlink",
    "target_replace",
    "parent_sync",
    "resource_release",
]


@dataclass(frozen=True, slots=True)
class ConfinedSequenceAncestorGuard:
    path: str
    observation: ConfinedSequenceDirectoryObservation


@dataclass(frozen=True, slots=True)
class ConfinedSequenceBinding:
    provider_ref: str
    provider_generation: str
    preparation_ref: str
    repository_root: str
    root_identity: tuple[int, int]
    process_id: int
    thread_id: int
    confinement_profile: Confinement
    mode_policy: ModePolicy
    limits: ConfinedSequenceLimits
    files: tuple[ConfinedSequenceFileBinding, ...]
    ancestor_guards: tuple[ConfinedSequenceAncestorGuard, ...]
    ordered_steps: tuple[ConfinedSequenceStep, ...]
    sequence_sha256: str


@dataclass(frozen=True, slots=True)
class ConfinedSequenceCleanup:
    binding: ConfinedSequenceBinding | None
    phase: Phase
    resources: tuple[ConfinedSequenceResourceEvidence, ...]
    scratch_residue: tuple[str, ...]
    release: ReleaseOutcome
    diagnostics: tuple[str, ...]
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class ConfinedSequenceDirectoryObservation:
    state: ObservationState
    exists: bool | None
    device: int | None
    inode: int | None
    mode: int | None
    mtime_ns: int | None
    ctime_ns: int | None


@dataclass(frozen=True, slots=True)
class ConfinedSequenceFileBinding:
    file_ordinal: int
    kind: FileKind
    path: str
    before: ConfinedSequenceFileObservation
    candidate_sha256: str
    candidate_size_bytes: int
    scratch_path: str
    mode_policy: ModePolicy


@dataclass(frozen=True, slots=True)
class ConfinedSequenceFileObservation:
    state: ObservationState
    exists: bool | None
    device: int | None
    inode: int | None
    mode: int | None
    size_bytes: int | None
    mtime_ns: int | None
    ctime_ns: int | None
    content_sha256: str | None


@dataclass(frozen=True, slots=True)
class ConfinedSequenceLimits:
    ancestor_guards: int
    binding_metadata_bytes: int
    created_ancestor_paths: int
    file_bytes: int
    file_transitions: int
    input_files: int
    path_components: int
    path_utf8_bytes: int
    physical_step_count: int
    retained_before_and_after_bytes: int
    scratch_paths: int
    simultaneous_live_scratch: int
    simultaneous_owned_descriptors: int


@dataclass(frozen=True, slots=True)
class ConfinedSequenceObservation:
    binding: ConfinedSequenceBinding | None
    phase: Phase
    next_ordinal: int
    effects: tuple[ConfinedSequencePhysicalEffect, ...]
    resources: tuple[ConfinedSequenceResourceEvidence, ...]
    scratch_residue: tuple[str, ...]
    primary_failure: ConfinedSequencePrimaryFailure
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class ConfinedSequencePhysicalEffect:
    ordinal: int
    kind: StepKind
    primary_path: str
    auxiliary_paths: tuple[str, ...]
    dispatch_state: DispatchState
    effect_state: EffectState
    before: ConfinedSequenceFileObservation
    after: ConfinedSequenceFileObservation
    requested_mode: int | None
    observed_mode: int | None
    durability: DurabilityState
    original_error: str | None


@dataclass(frozen=True, slots=True)
class ConfinedSequencePreconditions:
    root_identity: tuple[int, int]
    ancestor_guards: tuple[ConfinedSequenceAncestorGuard, ...]
    target: ConfinedSequenceFileObservation | None
    scratch: ConfinedSequenceFileObservation | None


@dataclass(frozen=True, slots=True)
class ConfinedSequencePrimaryFailure:
    state: PrimaryFailureState
    owner_ref: str | None
    stage: str | None
    code: str | None
    cause_type: str | None
    interruption: bool


@dataclass(frozen=True, slots=True)
class ConfinedSequenceRefusalEvidence:
    code: str
    cause_type: str | None
    preparation_ref: str | None
    observation: ConfinedSequenceObservation | None
    cleanup: ConfinedSequenceCleanup | None
    primary_failure: ConfinedSequencePrimaryFailure
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class ConfinedSequenceResourceEvidence:
    resource_ref: str
    provider_ref: str
    kind: ResourceKind
    path: str | None
    ownership: Ownership
    release_attempted: bool
    release_outcome: ReleaseOutcome
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConfinedSequenceStep:
    ordinal: int
    file_ordinal: int
    kind: StepKind
    primary_path: str
    auxiliary_paths: tuple[str, ...]
    preconditions: ConfinedSequencePreconditions
    mode_policy: ModePolicy
    requested_mode: int | None
    candidate_sha256: str
    candidate_size_bytes: int
    resource_refs: tuple[str, ...]
    cleanup_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConfinedSequenceStepResult:
    binding: ConfinedSequenceBinding | None
    step_ordinal: int
    phase: Phase
    next_ordinal: int
    effect: ConfinedSequencePhysicalEffect
    resources: tuple[ConfinedSequenceResourceEvidence, ...]
    primary_failure: ConfinedSequencePrimaryFailure
    ledger_complete: bool


_VALUE_TYPES = (
    ConfinedSequenceAncestorGuard,
    ConfinedSequenceBinding,
    ConfinedSequenceCleanup,
    ConfinedSequenceDirectoryObservation,
    ConfinedSequenceFileBinding,
    ConfinedSequenceFileObservation,
    ConfinedSequenceLimits,
    ConfinedSequenceObservation,
    ConfinedSequencePhysicalEffect,
    ConfinedSequencePreconditions,
    ConfinedSequencePrimaryFailure,
    ConfinedSequenceRefusalEvidence,
    ConfinedSequenceResourceEvidence,
    ConfinedSequenceStep,
    ConfinedSequenceStepResult,
)
_WIRE_IDS = {
    ConfinedSequenceAncestorGuard: "aware.file-system.confined-sequence-ancestor-guard.v1",
    ConfinedSequenceBinding: "aware.file-system.confined-sequence-binding.v1",
    ConfinedSequenceCleanup: "aware.file-system.confined-sequence-cleanup.v1",
    ConfinedSequenceDirectoryObservation: "aware.file-system.confined-sequence-directory-observation.v1",
    ConfinedSequenceFileBinding: "aware.file-system.confined-sequence-file-binding.v1",
    ConfinedSequenceFileObservation: "aware.file-system.confined-sequence-file-observation.v1",
    ConfinedSequenceLimits: "aware.file-system.confined-sequence-limits.v1",
    ConfinedSequenceObservation: "aware.file-system.confined-sequence-observation.v1",
    ConfinedSequencePhysicalEffect: "aware.file-system.confined-sequence-physical-effect.v1",
    ConfinedSequencePreconditions: "aware.file-system.confined-sequence-preconditions.v1",
    ConfinedSequencePrimaryFailure: "aware.file-system.confined-sequence-primary-failure.v1",
    ConfinedSequenceRefusalEvidence: "aware.file-system.confined-sequence-refusal-evidence.v1",
    ConfinedSequenceResourceEvidence: "aware.file-system.confined-sequence-resource-evidence.v1",
    ConfinedSequenceStep: "aware.file-system.confined-sequence-step.v1",
    ConfinedSequenceStepResult: "aware.file-system.confined-sequence-step-result.v1",
}
_LIMIT_CAPS = {
    "ancestor_guards": 4096,
    "binding_metadata_bytes": 2097152,
    "created_ancestor_paths": 1024,
    "file_bytes": 1048576,
    "file_transitions": 1024,
    "input_files": 4096,
    "path_components": 64,
    "path_utf8_bytes": 1024,
    "physical_step_count": 12288,
    "retained_before_and_after_bytes": 33554432,
    "scratch_paths": 1024,
    "simultaneous_live_scratch": 1,
    "simultaneous_owned_descriptors": 96,
}


class ConfinedSequenceRefusal(RuntimeError):
    def __init__(self, code, *, evidence=None):
        self.code = code
        self.evidence = evidence
        super().__init__(code)


class RetainedConfinedFileSequence:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use_original_file_sequence_factory")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("file_sequence_cannot_be_subclassed")

    def __copy__(self):
        raise TypeError("file_sequence_cannot_be_copied")

    def __deepcopy__(self, memo):
        raise TypeError("file_sequence_cannot_be_copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("file_sequence_cannot_be_serialized")


_HANDLES = {}
_OS = {
    name: getattr(os, name)
    for name in (
        "open",
        "close",
        "fstat",
        "stat",
        "lstat",
        "write",
        "fsync",
        "fchmod",
        "mkdir",
        "link",
        "unlink",
        "replace",
    )
}
_WRITER = native._confined_file_writer_steps
_WRITER_CODE = _WRITER.__code__
_STEP_TYPE = native._ConfinedWriterStep
_MEMBER_ROWS = {
    cls: tuple((field.name, vars(cls)[field.name]) for field in fields(cls))
    for cls in _VALUE_TYPES
}
_VALUE_BASELINES = tuple(
    (cls.__name__, cls, cls.__init__, cls.__init__.__code__) for cls in _VALUE_TYPES
)
_STEP_SLOTS = tuple(
    (field.name, vars(_STEP_TYPE)[field.name]) for field in fields(_STEP_TYPE)
)
_MEMBER_ROWS_BY_ID = {id(cls): (cls, rows) for cls, rows in _MEMBER_ROWS.items()}
_REQUEST_TYPE = native.ConfinedFileMutationRequest
_REQUEST_SLOTS = tuple(
    (f.name, vars(_REQUEST_TYPE)[f.name]) for f in fields(_REQUEST_TYPE)
)
_REQUEST_INIT = (_REQUEST_TYPE.__init__, _REQUEST_TYPE.__init__.__code__)
_REQUEST_POST = (_REQUEST_TYPE.__post_init__, _REQUEST_TYPE.__post_init__.__code__)
_UNKNOWN = ConfinedSequenceFileObservation(
    "not_observed", None, None, None, None, None, None, None, None
)
_NONE_FAILURE = ConfinedSequencePrimaryFailure("none", None, None, None, None, False)
_MODE = "legacy_kernel_umask_restore_existing_v1"


def _path(value):
    if (
        type(value) is not str
        or not value
        or normalize("NFC", value) != value
        or len(value.encode("utf-8")) > 1024
        or len(value.split("/")) > 64
    ):
        raise ConfinedSequenceRefusal("canonical_sequence_path_required")
    return native._relative_path(value)


def _adopt_read(state, ledger):
    unknown = (
        ledger.acquisition_unknown or ledger.release_unknown or ledger.context_unknown
    )
    state.ledger_complete = state.ledger_complete and not unknown
    for row in ledger.resources:
        state.resources.append(
            {
                "ref": row.resource_ref,
                "path": row.path,
                "kind": row.kind,
                "fd": None,
                "identity": None,
                "attempted": row.spent,
                "outcome": "unknown" if unknown else "confirmed",
                "ownership": "unknown" if unknown else "released",
            }
        )


def _snapshot(root, path, state=None):
    """Original descriptor reader, with checked cleanup and no mutation."""
    if state is not None and len(state.resources) + len(path.split("/")) + 1 > 16384:
        raise ConfinedSequenceRefusal("sequence_resource_record_limit")
    try:
        view, info, ledger = native._observe_confined_file_with_custody(
            root=root, path=path, maximum_bytes=1048576
        )
    except native.ConfinedFileObservationError as error:
        if state is not None:
            ledger = getattr(error, "_original_read_ledger", None)
            if type(ledger) is native._ReadLedger:
                _adopt_read(state, ledger)
            else:
                state.ledger_complete = False
        raise
    if state is not None:
        _adopt_read(state, ledger)
    if view.observation.outcome is not native.ConfinedObservationOutcome.OBSERVED:
        raise ConfinedSequenceRefusal("sequence_source_unavailable")
    if not view.observation.exists:
        return ConfinedSequenceFileObservation(
            "observed", False, None, None, None, None, None, None, None
        ), None
    if type(info) is not os.stat_result or not stat.S_ISREG(info.st_mode):
        raise ConfinedSequenceRefusal("sequence_regular_file_required")
    return ConfinedSequenceFileObservation(
        "observed",
        True,
        info.st_dev,
        info.st_ino,
        info.st_mode,
        view.observation.size_bytes,
        info.st_mtime_ns,
        info.st_ctime_ns,
        view.observation.content_digest,
    ), view.observation.content


def _directory(root, path):
    try:
        info = _OS["lstat"](root / path)
    except FileNotFoundError:
        return ConfinedSequenceDirectoryObservation(
            "observed", False, None, None, None, None, None
        )
    if not stat.S_ISDIR(info.st_mode):
        raise ConfinedSequenceRefusal("sequence_directory_required")
    return ConfinedSequenceDirectoryObservation(
        "observed",
        True,
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def confined_sequence_value_to_payload(value) -> dict[str, Any]:
    """Closed original owner metadata; no handle or candidate body projection."""

    remaining = 2097152
    nodes = 0

    def charge(count):
        nonlocal remaining
        remaining -= count
        if remaining < 0:
            raise ConfinedSequenceRefusal("sequence_metadata_limit")

    def convert(item, depth=0):
        nonlocal nodes
        nodes += 1
        if depth > 64 or nodes > 262144:
            raise ConfinedSequenceRefusal("sequence_structure_limit")
        cls = type(item)
        original = _MEMBER_ROWS_BY_ID.get(id(cls))
        if original is not None and original[0] is cls:
            rows = original[1]
            if any(vars(cls).get(name) is not slot for name, slot in rows):
                raise ConfinedSequenceRefusal("sequence_original_slot_changed")
            skeleton = {
                "contract": _WIRE_IDS[cls],
                "value": {name: None for name, _ in rows},
            }
            charge(
                len(
                    json.dumps(
                        skeleton,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
                - 4 * len(rows)
            )
            return {
                "contract": _WIRE_IDS[cls],
                "value": {
                    name: convert(slot.__get__(item, cls), depth + 1)
                    for name, slot in rows
                },
            }
        if cls is tuple:
            if len(item) > 16384:
                raise ConfinedSequenceRefusal("sequence_array_limit")
            charge(2 + max(0, len(item) - 1))
            return [convert(child, depth + 1) for child in item]
        if item is None or cls in (str, int, bool):
            charge(
                len(
                    json.dumps(item, ensure_ascii=False, separators=(",", ":")).encode(
                        "utf-8"
                    )
                )
            )
            return item
        raise ConfinedSequenceRefusal("sequence_original_metadata_required")

    payload = cast(dict[str, Any], convert(value))
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > 2097152:
        raise ConfinedSequenceRefusal("sequence_metadata_limit")
    return payload


@dataclass
class _SequenceState:
    root: Path
    root_identity: tuple[int, int]
    requests: tuple[native.ConfinedFileMutationRequest, ...]
    limits: ConfinedSequenceLimits
    provider_ref: str
    generation: str
    preparation_ref: str
    pid: int
    thread: int
    binding: object = None
    phase: str = "preparing"
    next_ordinal: int = 0
    file_ordinal: int = 0
    generator: object = None
    pending: object = None
    io: object = None
    effects: tuple[ConfinedSequencePhysicalEffect, ...] = ()
    resources: list[dict[str, Any]] = field(default_factory=list)
    pins: dict[str, Any] = field(default_factory=dict)
    dir_pins: dict[str, Any] = field(default_factory=dict)
    scratch: dict[str, Any] = field(default_factory=dict)
    scratch_unlink_attempted: set[str] = field(default_factory=set)
    completed_files: set[int] = field(default_factory=set)
    primary: object = _NONE_FAILURE
    ledger_complete: bool = True
    released: bool = False
    busy: bool = False
    cleanup: object = None


class _SequenceIO:
    """Original physical custody, not an injected callback or Issue verifier."""

    def __init__(self, state):
        self.state = state
        self.active = {}
        self.stage = "sequence_io"
        self.cleanup_mode = False
        # Publish original cleanup custody before a fallible acquisition or
        # observation. Constructor failure must not strand this owner's fds.
        state.io = self
        self.root_fd = self.open(
            state.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )

    def _resource(self, path, kind, descriptor=None):
        state = self.state
        if (
            len(state.resources) >= 16384
            or sum(row["ownership"] in ("owned", "unknown") for row in state.resources)
            >= state.limits.simultaneous_owned_descriptors
        ):
            raise ConfinedSequenceRefusal("sequence_resource_limit")
        row = {
            "ref": "sequence-resource:" + uuid4().hex,
            "path": path,
            "kind": kind,
            "fd": descriptor,
            "identity": None,
            "attempted": False,
            "outcome": "unknown",
            "ownership": "owned",
            "scratch_path": Path(path).relative_to(state.root).as_posix()
            if kind == "scratch_descriptor"
            else None,
            "scratch_exists": False,
        }
        state.resources.append(row)
        return row

    def open(self, path, flags, mode=0o777, **kwargs):
        parent = kwargs.get("dir_fd")
        if parent is None:
            locator = str(self.state.root) if type(path) is type(Path()) else str(path)
        else:
            row = self.active.get(parent)
            if row is None:
                raise ConfinedSequenceRefusal("sequence_parent_not_owned")
            prefix = row["path"]
            locator = (
                str(Path(prefix) / path)
                if prefix.startswith("/")
                else str(PurePosixPath(prefix) / path)
            )
        kind = (
            "scratch_descriptor"
            if flags & os.O_CREAT
            else "root_descriptor"
            if flags & os.O_DIRECTORY and parent is None
            else "directory_descriptor"
            if flags & os.O_DIRECTORY
            else "file_descriptor"
        )
        resource = self._resource(locator, kind)
        try:
            descriptor = _OS["open"](path, flags, mode, **kwargs)
        except BaseException as error:
            if isinstance(error, OSError) and error.errno in {
                errno.ENOENT,
                errno.ENOTDIR,
                errno.EACCES,
                errno.EPERM,
                errno.ELOOP,
                errno.ENAMETOOLONG,
                errno.EEXIST,
            }:
                resource["ownership"] = "released"
                resource["outcome"] = "confirmed"
            else:
                resource["ownership"] = "unknown"
                self.state.ledger_complete = False
            raise
        resource["fd"] = descriptor
        relative = resource["scratch_path"]
        resource["scratch_exists"] = relative is not None
        try:
            self.active[descriptor] = resource
            if relative is not None:
                # Creation returned, but identity observation has not. Retain
                # residue without issuing an identity-based unlink right.
                self.state.scratch[relative] = None
            info = _OS["fstat"](descriptor)
            resource["identity"] = info.st_dev, info.st_ino
        except BaseException:
            if relative is not None:
                self.state.ledger_complete = False
            raise
        if relative is not None:
            self.state.scratch[relative] = resource["identity"]
        return descriptor

    def close(self, descriptor):
        resource = self.active.pop(descriptor, None)
        if resource is None:
            # The preallocated acquisition row also covers an interrupted
            # active-map publication. It is original custody, not a reread.
            resource = next(
                (
                    row
                    for row in reversed(self.state.resources)
                    if row["fd"] == descriptor and not row["attempted"]
                ),
                None,
            )
        if resource is None or resource["attempted"]:
            raise ConfinedSequenceRefusal("sequence_release_right_unavailable")
        resource["attempted"] = True
        try:
            _OS["close"](descriptor)
        except BaseException:
            resource["ownership"] = "unknown"
            self.state.ledger_complete = False
            raise
        resource["ownership"] = "released"
        resource["outcome"] = "confirmed"

    def write(self, descriptor, content):
        if descriptor not in self.active:
            raise ConfinedSequenceRefusal("sequence_write_descriptor_unavailable")
        return _OS["write"](descriptor, content)

    def fsync(self, descriptor):
        if descriptor not in self.active:
            raise ConfinedSequenceRefusal("sequence_sync_descriptor_unavailable")
        return _OS["fsync"](descriptor)

    def fchmod(self, descriptor, mode):
        if descriptor not in self.active:
            raise ConfinedSequenceRefusal("sequence_mode_descriptor_unavailable")
        return _OS["fchmod"](descriptor, mode)

    def mkdir(self, name, **kwargs):
        return _OS["mkdir"](name, **kwargs)

    def link(self, *args, **kwargs):
        return _OS["link"](*args, **kwargs)

    def replace(self, *args, **kwargs):
        result = _OS["replace"](*args, **kwargs)
        self._forget_scratch(args[0], kwargs["src_dir_fd"])
        return result

    def _scratch_path(self, name, parent):
        row = self.active.get(parent)
        if row is None:
            raise ConfinedSequenceRefusal("sequence_parent_not_owned")
        return (Path(row["path"]) / name).relative_to(self.state.root).as_posix()

    def _forget_scratch(self, name, parent):
        path = self._scratch_path(name, parent)
        for row in self.state.resources:
            if row.get("scratch_path") == path:
                row["scratch_exists"] = False
        self.state.scratch.pop(path, None)

    def unlink(self, name, **kwargs):
        path = self._scratch_path(name, kwargs["dir_fd"])
        if path in self.state.scratch_unlink_attempted:
            raise ConfinedSequenceRefusal("sequence_scratch_unlink_already_attempted")
        identity = self.state.scratch.get(path)
        if identity is None:
            # Collision or lost creation result gives no right to remove a name.
            raise FileNotFoundError("sequence_scratch_not_owned")
        current = _OS["stat"](name, dir_fd=kwargs["dir_fd"], follow_symlinks=False)
        if (current.st_dev, current.st_ino) != identity:
            self.state.ledger_complete = False
            raise ConfinedSequenceRefusal("sequence_scratch_identity_changed")
        self.state.scratch_unlink_attempted.add(path)
        try:
            result = _OS["unlink"](name, **kwargs)
        except BaseException:
            self.state.ledger_complete = False
            raise
        # Spend the attempt before dispatch; erase residue only after its
        # successful return. Lost/failed returns remain uncertain without retry.
        self._forget_scratch(name, kwargs["dir_fd"])
        return result


def _resources(state):
    return tuple(
        ConfinedSequenceResourceEvidence(
            row["ref"],
            state.provider_ref,
            row["kind"],
            row["path"],
            row["ownership"],
            row["attempted"],
            row["outcome"],
            (),
        )
        for row in state.resources
    )


def _issued(handle):
    if type(handle) is not RetainedConfinedFileSequence:
        raise ConfinedSequenceRefusal("original_file_sequence_required")
    pair = _HANDLES.get(id(handle))
    if pair is None or pair[0]() is not handle:
        raise ConfinedSequenceRefusal("original_file_sequence_required")
    state = pair[1]
    if (state.pid, state.thread) != (os.getpid(), threading.get_ident()):
        raise ConfinedSequenceRefusal("sequence_origin_mismatch")
    return state


def _check_current(state):
    if state.released or state.phase == "retired":
        raise ConfinedSequenceRefusal("sequence_retired")
    if (
        native._confined_file_writer_steps is not _WRITER
        or _WRITER.__code__ is not _WRITER_CODE
    ):
        raise ConfinedSequenceRefusal("sequence_original_writer_changed")
    for name, original in _OS.items():
        if getattr(os, name) is not original:
            raise ConfinedSequenceRefusal("sequence_native_binding_changed")
    for name, cls, constructor, code in _VALUE_BASELINES:
        if (
            globals().get(name) is not cls
            or cls.__init__ is not constructor
            or constructor.__code__ is not code
        ):
            raise ConfinedSequenceRefusal("sequence_metadata_constructor_changed")
        if any(
            vars(cls).get(field) is not descriptor
            for field, descriptor in _MEMBER_ROWS[cls]
        ):
            raise ConfinedSequenceRefusal("sequence_original_slot_changed")
    if any(
        vars(_STEP_TYPE).get(field) is not descriptor
        for field, descriptor in _STEP_SLOTS
    ):
        raise ConfinedSequenceRefusal("sequence_writer_slot_changed")
    info = _OS["lstat"](state.root)
    if (
        not stat.S_ISDIR(info.st_mode)
        or (info.st_dev, info.st_ino) != state.root_identity
    ):
        raise ConfinedSequenceRefusal("sequence_root_changed")
    for path, expected in state.dir_pins.items():
        if _directory(state.root, path) != expected:
            raise ConfinedSequenceRefusal("sequence_ancestor_drift")
    for path, (expected, body) in state.pins.items():
        actual, actual_body = _snapshot(state.root, path, state)
        if actual != expected or actual_body != body:
            raise ConfinedSequenceRefusal("sequence_input_drift")


def _failure(state, error, stage):
    if state.primary.state == "none":
        state.primary = ConfinedSequencePrimaryFailure(
            "observed",
            state.provider_ref,
            stage,
            getattr(error, "code", "sequence_step_failed"),
            type(error).__name__,
            not isinstance(error, Exception),
        )
    state.phase = "retired"


def _scratch_residue(state):
    residue = set(state.scratch)
    residue.update(
        row["scratch_path"] for row in state.resources if row.get("scratch_exists")
    )
    return tuple(sorted(residue))


def _observation(state):
    return ConfinedSequenceObservation(
        state.binding,
        state.phase,
        state.next_ordinal,
        state.effects,
        _resources(state),
        _scratch_residue(state),
        state.primary,
        state.ledger_complete,
    )


def _refuse(state, error, stage):
    _failure(state, error, stage)
    evidence = ConfinedSequenceRefusalEvidence(
        code=getattr(error, "code", "sequence_step_failed"),
        cause_type=type(error).__name__,
        preparation_ref=state.preparation_ref,
        observation=_observation(state),
        cleanup=state.cleanup,
        primary_failure=state.primary,
        ledger_complete=state.ledger_complete,
    )
    return ConfinedSequenceRefusal(evidence.code, evidence=evidence)


def _step_for(
    state, ordinal, file_ordinal, kind, path, guards, target, scratch, *, mode=None
):
    request = state.requests[file_ordinal]
    return ConfinedSequenceStep(
        ordinal,
        file_ordinal,
        kind,
        path,
        (),
        ConfinedSequencePreconditions(state.root_identity, guards, target, scratch),
        _MODE,
        mode,
        "sha256:" + hashlib.sha256(request.content).hexdigest(),
        len(request.content),
        (),
        (),
    )


def _schedule(state):
    files, ancestors, steps = [], {}, []
    already_created = set()
    total_bodies = 0
    for index, request in enumerate(state.requests):
        before, body = _snapshot(state.root, request.path, state)
        if (
            before.exists != request.expected_exists
            or before.content_sha256 != request.expected_content_digest
        ):
            raise ConfinedSequenceRefusal("sequence_request_baseline_changed")
        state.pins[request.path] = (before, body)
        total_bodies += len(request.content) + (len(body) if body is not None else 0)
        if total_bodies > state.limits.retained_before_and_after_bytes:
            raise ConfinedSequenceRefusal("sequence_body_limit")
        # Prepared names must be inspectable in a data-only preview and usable
        # by a fresh one-process apply. Identity/bytes determine the same name;
        # no hash grants authority, and collision still retires without reselection.
        name_input = json.dumps(
            (
                str(state.root),
                state.root_identity,
                request.path,
                request.expected_exists,
                request.expected_content_digest,
                hashlib.sha256(request.content).hexdigest(),
            ),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        scratch_name = ".aware-cas-" + hashlib.sha256(name_input).hexdigest()
        parent = PurePosixPath(request.path).parent
        scratch = str(parent / scratch_name) if str(parent) != "." else scratch_name
        scratch_before, _ = _snapshot(state.root, scratch, state)
        if scratch_before.exists:
            raise ConfinedSequenceRefusal("sequence_scratch_collision")
        guards = []
        parts = request.path.split("/")[:-1]
        for depth in range(1, len(parts) + 1):
            path = "/".join(parts[:depth])
            observation = _directory(state.root, path)
            guard = ConfinedSequenceAncestorGuard(path, observation)
            ancestors.setdefault(path, guard)
            state.dir_pins.setdefault(path, observation)
            guards.append(guard)
            if not observation.exists and path not in already_created:
                if request.kind is not native.ConfinedMutationKind.CREATE:
                    raise ConfinedSequenceRefusal("sequence_update_parent_missing")
                for kind in ("ancestor_create", "ancestor_sync"):
                    steps.append(
                        _step_for(
                            state,
                            len(steps),
                            index,
                            kind,
                            path,
                            tuple(guards),
                            before,
                            scratch_before,
                            mode=0o777 if kind == "ancestor_create" else None,
                        )
                    )
                already_created.add(path)
        files.append(
            ConfinedSequenceFileBinding(
                index,
                request.kind.value,
                request.path,
                before,
                "sha256:" + hashlib.sha256(request.content).hexdigest(),
                len(request.content),
                scratch,
                _MODE,
            )
        )
        mode = 0o666 if not before.exists else stat.S_IMODE(cast(int, before.mode))
        kinds = ["scratch_create", "scratch_write"]
        if before.exists:
            kinds.append("scratch_restore_mode")
        kinds += [
            "scratch_sync",
            "scratch_close",
            "target_link" if not before.exists else "target_replace",
        ]
        if not before.exists:
            kinds.append("scratch_unlink")
        kinds += ["parent_sync"] + ["resource_release"] * (len(parts) + 1)
        for kind in kinds:
            primary = scratch if kind.startswith("scratch_") else request.path
            steps.append(
                _step_for(
                    state,
                    len(steps),
                    index,
                    kind,
                    primary,
                    tuple(guards),
                    before,
                    scratch_before,
                    mode=mode
                    if kind in ("scratch_create", "scratch_restore_mode")
                    else None,
                )
            )
    if (
        len(steps) > state.limits.physical_step_count
        or len(ancestors) > state.limits.ancestor_guards
        or len(already_created) > state.limits.created_ancestor_paths
    ):
        raise ConfinedSequenceRefusal("sequence_footprint_limit")
    # Reserve a conservative closed-record footprint, including final and failed
    # unwind evidence, before the first physical dispatch. Individual maxima are
    # conjunctive; they are not a promise that every maximum-sized tree fits.
    if (
        len(steps) + len(state.requests) * 66
    ) * 1024 > state.limits.binding_metadata_bytes:
        raise ConfinedSequenceRefusal("sequence_evidence_reservation_limit")
    read_rows = sum(len(path.split("/")) + 1 for path in state.pins)
    if len(state.resources) + (len(steps) + 4) * read_rows + len(steps) * 3 > 16384:
        raise ConfinedSequenceRefusal("sequence_resource_reservation_limit")
    blank = ConfinedSequenceBinding(
        provider_ref=state.provider_ref,
        provider_generation=state.generation,
        preparation_ref=state.preparation_ref,
        repository_root=str(state.root),
        root_identity=state.root_identity,
        process_id=state.pid,
        thread_id=state.thread,
        confinement_profile="descriptor_walk_v1",
        mode_policy=_MODE,
        limits=state.limits,
        files=tuple(files),
        ancestor_guards=tuple(ancestors.values()),
        ordered_steps=tuple(steps),
        sequence_sha256="sha256:" + "0" * 64,
    )
    payload = confined_sequence_value_to_payload(blank)
    payload["value"].pop("sequence_sha256")
    digest = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(
                payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode()
        ).hexdigest()
    )
    return replace(blank, sequence_sha256=digest)


def retain_confined_file_sequence(
    *,
    root: Path,
    requests: tuple[native.ConfinedFileMutationRequest, ...],
    limits: ConfinedSequenceLimits,
    confinement_profile: native.ConfinedMutationProfile,
) -> RetainedConfinedFileSequence:
    if (
        type(confinement_profile) is not native.ConfinedMutationProfile
        or confinement_profile is not native.ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    ):
        raise ConfinedSequenceRefusal("sequence_profile_unavailable")
    if (
        type(root) is not type(Path())
        or not root.is_absolute()
        or root.resolve(strict=True) != root
    ):
        raise ConfinedSequenceRefusal("canonical_sequence_root_required")
    if (
        type(confinement_profile) is not native.ConfinedMutationProfile
        or confinement_profile is not native.ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    ):
        raise ConfinedSequenceRefusal("sequence_profile_unavailable")
    if type(limits) is not ConfinedSequenceLimits:
        raise ConfinedSequenceRefusal("original_sequence_limits_required")
    for name, ceiling in _LIMIT_CAPS.items():
        value = getattr(limits, name)
        if type(value) is not int or not 0 < value <= ceiling:
            raise ConfinedSequenceRefusal("sequence_limit_invalid")
    if type(requests) is not tuple or len(requests) > limits.file_transitions:
        raise ConfinedSequenceRefusal("sequence_request_shape_invalid")
    if (
        native.ConfinedFileMutationRequest is not _REQUEST_TYPE
        or _REQUEST_TYPE.__init__ is not _REQUEST_INIT[0]
        or _REQUEST_INIT[0].__code__ is not _REQUEST_INIT[1]
        or _REQUEST_TYPE.__post_init__ is not _REQUEST_POST[0]
        or _REQUEST_POST[0].__code__ is not _REQUEST_POST[1]
        or any(
            vars(_REQUEST_TYPE).get(name) is not slot for name, slot in _REQUEST_SLOTS
        )
    ):
        raise ConfinedSequenceRefusal("sequence_request_constructor_changed")
    detached = []
    paths = set()
    for request in requests:
        if type(request) is not _REQUEST_TYPE:
            raise ConfinedSequenceRefusal("sequence_request_shape_invalid")
        row = {
            name: slot.__get__(request, _REQUEST_TYPE) for name, slot in _REQUEST_SLOTS
        }
        if (
            type(row["kind"]) is not native.ConfinedMutationKind
            or row["kind"]
            not in (
                native.ConfinedMutationKind.CREATE,
                native.ConfinedMutationKind.UPDATE,
            )
            or type(row["content"]) is not bytes
            or type(row["expected_exists"]) is not bool
            or type(row["text_replacements"]) is not tuple
            or row["text_replacements"]
            or len(row["content"]) > limits.file_bytes
            or row["expected_content_digest"] is not None
            and type(row["expected_content_digest"]) is not str
        ):
            raise ConfinedSequenceRefusal("sequence_request_shape_invalid")
        _path(row["path"])
        if row["path"] in paths:
            raise ConfinedSequenceRefusal("sequence_duplicate_path")
        paths.add(row["path"])
        detached.append(
            _REQUEST_TYPE(
                row["kind"],
                row["path"],
                row["expected_exists"],
                row["expected_content_digest"],
                row["content"],
                (),
                limits.file_bytes,
            )
        )
    info = _OS["lstat"](root)
    if not stat.S_ISDIR(info.st_mode):
        raise ConfinedSequenceRefusal("sequence_root_directory_required")
    state = _SequenceState(
        root,
        (info.st_dev, info.st_ino),
        tuple(detached),
        replace(limits),
        "aware.filesystem.file-sequence.v1",
        "sequence-generation:" + uuid4().hex,
        "sequence-preparation:" + uuid4().hex,
        os.getpid(),
        threading.get_ident(),
        resources=[],
        pins={},
        dir_pins={},
        scratch={},
        completed_files=set(),
    )
    try:
        _check_current(state)
        state.io = _SequenceIO(state)
        state.binding = _schedule(state)
        state.phase = "prepared"
        _check_current(state)
        handle = object.__new__(RetainedConfinedFileSequence)
        _HANDLES[id(handle)] = (weakref.ref(handle), state)
        weakref.finalize(handle, _release_state, state)
        return handle
    except BaseException as error:
        _failure(state, error, "preparation")
        _release_state(state)
        raise _refuse(state, error, "preparation") from error


def observe_confined_file_sequence(sequence):
    return _observation(_issued(sequence))


def verify_confined_file_sequence(sequence, *, expected_binding):
    state = _issued(sequence)
    try:
        if type(
            expected_binding
        ) is not ConfinedSequenceBinding or confined_sequence_value_to_payload(
            expected_binding
        ) != confined_sequence_value_to_payload(state.binding):
            raise ConfinedSequenceRefusal("sequence_binding_mismatch")
        _check_current(state)
    except BaseException as error:
        raise _refuse(state, error, "currentness") from error
    return _observation(state)


def _next_writer_step(state, value=None, error=None):
    while True:
        if state.generator is None:
            if state.file_ordinal >= len(state.requests):
                state.pending = None
                return
            request = state.requests[state.file_ordinal]
            scratch = PurePosixPath(
                state.binding.files[state.file_ordinal].scratch_path
            ).name
            state.generator = _WRITER(
                root=state.root,
                request=request,
                _step_mode=True,
                _scratch_name=scratch,
                _io=state.io,
            )
        try:
            state.pending = (
                state.generator.throw(error)
                if error is not None
                else next(state.generator)
                if value is None
                else state.generator.send(value)
            )
            return
        except StopIteration as completed:
            result = completed.value
            state.generator = None
            if (
                result is None
                or result.outcome is not native.ConfinedMutationOutcome.APPLIED
                or not result.durability_confirmed
            ):
                raise ConfinedSequenceRefusal("sequence_original_writer_incomplete")
            path = state.requests[state.file_ordinal].path
            state.pins[path] = _snapshot(state.root, path, state)
            state.completed_files.add(state.file_ordinal)
            state.file_ordinal += 1
            value = error = None


def _run_original_step(state, step):
    if type(step) is not _STEP_TYPE:
        raise ConfinedSequenceRefusal("sequence_original_writer_step_required")
    if step.kind == "scratch_write":
        if (
            step.function is not _BYTE_WRITER
            or _BYTE_WRITER.__code__ is not _BYTE_WRITER_CODE
            or step.arguments[0] is not state.io
        ):
            raise ConfinedSequenceRefusal("sequence_write_helper_changed")
    else:
        name = {
            "ancestor_create": "mkdir",
            "ancestor_sync": "fsync",
            "scratch_create": "open",
            "scratch_restore_mode": "fchmod",
            "scratch_sync": "fsync",
            "scratch_close": "close",
            "target_link": "link",
            "target_replace": "replace",
            "scratch_unlink": "unlink",
            "parent_sync": "fsync",
            "resource_release": "close",
        }.get(step.kind)
        original = _IO_METHODS.get(name) if name is not None else None
        if (
            original is None
            or type(step.function) is not MethodType
            or step.function.__self__ is not state.io
            or step.function.__func__ is not original[0]
            or original[0].__code__ is not original[1]
        ):
            raise ConfinedSequenceRefusal("sequence_physical_dispatch_changed")
    return cast(Any, step.function)(*step.arguments, **step.keywords)


def execute_next_confined_file_step(sequence, *, expected_ordinal):
    state = _issued(sequence)
    if (
        type(expected_ordinal) is not int
        or expected_ordinal != state.next_ordinal
        or state.busy
    ):
        raise _refuse(
            state,
            ConfinedSequenceRefusal("sequence_ordinal_replay_or_mismatch"),
            "ordinal",
        )
    try:
        _check_current(state)
        if state.next_ordinal >= len(state.binding.ordered_steps):
            raise ConfinedSequenceRefusal("sequence_already_complete")
        state.busy = True
        if state.pending is None:
            _next_writer_step(state)
        actual = state.pending
        planned = state.binding.ordered_steps[state.next_ordinal]
        if (
            type(actual) is not _STEP_TYPE
            or actual.kind != planned.kind
            or actual.path != state.requests[planned.file_ordinal].path
            and actual.path != planned.primary_path
        ):
            raise ConfinedSequenceRefusal("sequence_original_schedule_mismatch")
        ordinal = state.next_ordinal
        state.next_ordinal += 1  # Spend before native dispatch, including failures.
        state.phase = "executing"
        before = planned.preconditions.target or _UNKNOWN
        # Reserve the original event before dispatch; late carrier/readback
        # failures cannot erase a known prefix or turn it into zero effects.
        effect = ConfinedSequencePhysicalEffect(
            ordinal,
            planned.kind,
            planned.primary_path,
            planned.auxiliary_paths,
            "attempted",
            "unknown",
            before,
            _UNKNOWN,
            planned.requested_mode,
            None,
            "unknown",
            None,
        )
        state.effects += (effect,)
        effect_slots = dict(_MEMBER_ROWS[ConfinedSequencePhysicalEffect])
        try:
            result = _run_original_step(state, actual)
        except BaseException as error:
            effect_slots["original_error"].__set__(effect, type(error).__name__)
            _failure(state, error, "physical_dispatch")
            raise
        effect_slots["dispatch_state"].__set__(effect, "returned")
        effect_slots["effect_state"].__set__(effect, "applied")
        effect_slots["durability"].__set__(
            effect, "confirmed" if planned.kind.endswith("sync") else "not_confirmed"
        )
        if planned.kind in (
            "ancestor_create",
            "scratch_create",
            "target_link",
            "target_replace",
            "scratch_unlink",
        ):
            changed = (
                planned.primary_path
                if planned.kind == "ancestor_create"
                else state.requests[planned.file_ordinal].path
            )
            affected = {str(PurePosixPath(changed).parent)}
            if planned.kind == "ancestor_create":
                affected.add(changed)
            for path in affected & state.dir_pins.keys():
                before_dir = state.dir_pins[path]
                after_dir = _directory(state.root, path)
                if (
                    not after_dir.exists
                    or before_dir.exists
                    and (before_dir.device, before_dir.inode, before_dir.mode)
                    != (after_dir.device, after_dir.inode, after_dir.mode)
                ):
                    raise ConfinedSequenceRefusal("sequence_original_ancestor_changed")
                state.dir_pins[path] = after_dir
        # A target link/replace is an original known postimage. Preserve its
        # observation before advancing the generator or admitting another step.
        if planned.kind in ("target_link", "target_replace", "scratch_unlink"):
            path = state.requests[planned.file_ordinal].path
            observed, body = _snapshot(state.root, path, state)
            if body != state.requests[planned.file_ordinal].content:
                raise ConfinedSequenceRefusal("sequence_original_postimage_changed")
            if planned.kind == "scratch_unlink":
                original = state.pins[path][0]
                if (observed.device, observed.inode, observed.mode) != (
                    original.device,
                    original.inode,
                    original.mode,
                ):
                    raise ConfinedSequenceRefusal("sequence_original_postimage_changed")
            state.pins[path] = observed, body
        state.pending = None
        _next_writer_step(state, result)
        if state.next_ordinal == len(state.binding.ordered_steps):
            if state.pending is not None:
                raise ConfinedSequenceRefusal("sequence_unplanned_suffix")
            state.phase = "completed"
        return ConfinedSequenceStepResult(
            binding=state.binding,
            step_ordinal=ordinal,
            phase=state.phase,
            next_ordinal=state.next_ordinal,
            effect=effect,
            resources=_resources(state),
            primary_failure=state.primary,
            ledger_complete=state.ledger_complete,
        )
    except BaseException as error:
        raise _refuse(state, error, "physical_dispatch") from error
    finally:
        state.busy = False


def _release_state(state):
    if state.released:
        return state.cleanup
    state.released = True
    state.phase = "retired"
    if state.generator is not None:
        state.io.cleanup_mode = True
        terminal = ConfinedSequenceRefusal("sequence_terminal_cleanup")
        try:
            pending = state.generator.throw(terminal)
            for _ in range(128):
                if type(pending) is not _STEP_TYPE or not pending.cleanup:
                    state.ledger_complete = False
                    break
                try:
                    result = _run_original_step(state, pending)
                except BaseException as error:  # noqa: BLE001 -- original unwind continues after interruption
                    pending = state.generator.throw(error)
                else:
                    pending = state.generator.send(result)
        except StopIteration:
            pass
        except BaseException as error:  # noqa: BLE001 -- retain genuine unwind failures, not the injected stop
            if error is not terminal:
                state.ledger_complete = False
        state.generator = state.pending = None
    if state.io is not None:
        for row in reversed(state.resources):
            descriptor = row["fd"]
            if descriptor is None or row["attempted"]:
                continue
            try:
                original, code = _IO_METHODS["close"]
                if original.__code__ is not code:
                    raise ConfinedSequenceRefusal("sequence_cleanup_method_changed")
                original(state.io, descriptor)
            except BaseException:  # noqa: BLE001 -- do not retry uncertain descriptor disposal
                state.ledger_complete = False
    if any(
        row["ownership"] != "released" or row["outcome"] != "confirmed"
        for row in state.resources
    ):
        state.ledger_complete = False
    residue = _scratch_residue(state)
    outcome = "confirmed" if state.ledger_complete and not residue else "unknown"
    state.cleanup = ConfinedSequenceCleanup(
        state.binding,
        "retired",
        _resources(state),
        residue,
        outcome,
        (),
        state.ledger_complete,
    )
    state.requests = ()
    state.pins = {}
    return state.cleanup


def release_confined_file_sequence(sequence):
    return _release_state(_issued(sequence))


_BYTE_WRITER = native._write_confined_bytes
_BYTE_WRITER_CODE = _BYTE_WRITER.__code__
_IO_METHODS = {
    name: (getattr(_SequenceIO, name), getattr(_SequenceIO, name).__code__)
    for name in (
        "open",
        "close",
        "write",
        "fsync",
        "fchmod",
        "mkdir",
        "link",
        "replace",
        "unlink",
    )
}
