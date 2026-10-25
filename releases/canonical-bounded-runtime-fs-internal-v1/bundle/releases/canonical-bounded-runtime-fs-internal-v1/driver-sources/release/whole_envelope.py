"""Typed compatibility composition over an exact original Protocol installer.

This module supplies neither an archive parser nor a filesystem writer. Trusted
release metadata binds the original driver/verifier and whole envelope. A plan
is a revalidated description, not mutation authority or continuous confinement.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class WholeEnvelopeArtifact:
    release_id: str
    product_revision: str
    envelope_name: str
    envelope_size: int
    envelope_sha256: str
    payload_sha256: str
    driver_sha256: str
    verifier_sha256: str
    platform: str = "linux_x86_64"
    python_minor: str = "3.12"
    runtime_mode: str = "external"


@dataclass(frozen=True)
class SuppliedRuntimeSelection:
    """Reviewed ordinary selection, not a native receipt or restored custody.

    The non-Python entrance must separately establish its original extraction
    completion before executing this interpreter. These fields correlate that
    selection; they do not authenticate a publisher or certify native ABI fit.
    """

    root: Path
    root_identity: tuple[int, int, int, int]
    python_sha256: str
    python_version: tuple[int, int, int]
    bootstrap_sha256: str
    archive_sha256: str
    roster_sha256: str
    grade: Literal["ordinary_supplied_runtime_selection"] = (
        "ordinary_supplied_runtime_selection"
    )
    authorizes_native_profile: Literal[False] = False


@dataclass(frozen=True)
class WholeEnvelopeInstallRequest:
    artifact: WholeEnvelopeArtifact
    bundle_root: Path
    installation_root: Path
    python_executable: Path
    timeout_seconds: int = 600
    supplied_runtime: SuppliedRuntimeSelection | None = None


@dataclass(frozen=True)
class WholeEnvelopeInstallPlan:
    request: WholeEnvelopeInstallRequest
    fingerprint: str
    environment: Path
    python_executable: Path
    runtime_observation: bytes
    runtime_stderr: bytes
    installation_root_identity: tuple[int, int, int, int]


@dataclass(frozen=True)
class WholeEnvelopeInstallResult:
    plan: WholeEnvelopeInstallPlan
    returncode: int
    stdout: bytes
    stderr: bytes
    original_receipt_json: bytes
    retained_source_and_notices: Path
    activation: Literal["not_requested"] = "not_requested"


@dataclass(frozen=True)
class RuntimeProbeEvidence:
    invocation: Literal["returned", "unknown"]
    stdout: bytes
    stderr: bytes
    returncode: int | None


class WholeEnvelopeInstallError(RuntimeError):
    """Original request, phase, streams and invocation uncertainty survive failure."""

    def __init__(
        self,
        request: WholeEnvelopeInstallRequest,
        phase: str,
        invocation: Literal["not_invoked", "returned", "unknown"],
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        returncode: int | None = None,
        runtime_probe: RuntimeProbeEvidence | None = None,
    ):
        super().__init__(phase)
        self.request = request
        self.phase = phase
        self.invocation = invocation
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.runtime_probe = runtime_probe
        self.install_effects = (
            "not_invoked" if invocation == "not_invoked" else "unknown"
        )
        self.output_capture = "complete" if invocation == "returned" else invocation
        self.cleanup = "not_observed"
        self.authorizes_retry = False


def _decode(body: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_receipt_key")
            result[key] = value
        return result

    return json.loads(body, object_pairs_hook=pairs)


def _path(path: Path) -> Path:
    if not isinstance(path, Path) or not path.is_absolute() or ".." in path.parts:
        raise ValueError("explicit_absolute_path_required")
    for current in (path, *path.parents):
        if current.is_symlink():
            raise ValueError("symlink_path_refused")
    return path


def _identity(path: Path):
    value = path.stat()
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _private_root(path: Path):
    _path(path)
    value = path.stat()
    if (
        not stat.S_ISDIR(value.st_mode)
        or value.st_uid != os.geteuid()
        or stat.S_IMODE(value.st_mode) != 0o700
    ):
        raise ValueError("existing_owned_private_installation_root_required")
    return value.st_dev, value.st_ino, value.st_uid, stat.S_IMODE(value.st_mode)


@dataclass(frozen=True, slots=True)
class ArchiveBodyRequest:
    path: Path
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True, eq=False)
class ArchiveBodyObservation:
    request: ArchiveBodyRequest
    request_snapshot: tuple[Path, str, int]
    body: bytes
    original_returns: tuple[object, ...]
    original_file: tuple
    cleanup: Literal["not_observed"] = "not_observed"
    authorizes_native_profile: Literal[False] = False


@dataclass
class _FileReadState:
    phase: str = "selection"
    invocation: Literal["not_invoked", "unknown", "returned"] = "not_invoked"
    original_returns: list[object] = field(default_factory=list)
    chunks: list[bytes] = field(default_factory=list)
    bytes_read: int = 0
    close_attempted: bool = False
    close_returned: bool = False
    secondary_causes: list[BaseException] = field(default_factory=list)


class ArchiveBodyObservationError(RuntimeError):
    def __init__(self, request, snapshot, state):
        super().__init__("archive_body_" + state.phase)
        self.request = request
        self.request_snapshot = snapshot
        self.phase = state.phase
        self.invocation = state.invocation
        self.original_returns = tuple(state.original_returns)
        self.validated_chunks = tuple(state.chunks)
        self.bytes_read = state.bytes_read
        self.close_attempted = state.close_attempted
        self.close_returned = state.close_returned
        self.secondary_causes = tuple(state.secondary_causes)
        self.cleanup = "not_observed"
        self.authorizes_retry = False
        self.authorizes_native_profile = False


def _read_input_file(path, expected, size, state, *, capture):
    """Single original stream for legacy hashes and bounded body observations.

    Original path checks are observational bookends, not descriptor confinement.
    Capture additionally correlates the opened descriptor before reading it.
    A returned close is retained, never promoted to a FileSystem cleanup ledger.
    """
    state.phase = "path"
    state.invocation = "unknown"
    resolved = _path(path)
    if capture:
        state.original_returns.append(resolved)
    state.phase = "preimage"
    before = _identity(path)
    if capture:
        state.original_returns.append(before)
    if not path.is_file() or (size is not None and before[2] != size):
        raise ValueError("regular_bound_input_required")
    digest = hashlib.sha256()
    maximum_size = size if size is not None else 0
    stream = None
    primary = None
    try:
        state.phase = "open"
        stream = path.open("rb")
        if capture:
            state.original_returns.append(stream)
            state.phase = "descriptor"
            descriptor = os.fstat(stream.fileno())
            state.original_returns.append(descriptor)
            identity = (
                descriptor.st_dev,
                descriptor.st_ino,
                descriptor.st_size,
                descriptor.st_mtime_ns,
                descriptor.st_ctime_ns,
            )
            if not stat.S_ISREG(descriptor.st_mode) or identity != before:
                raise ValueError("opened_file_identity_mismatch")
        state.phase = "read"
        while True:
            amount = 1024 * 1024
            if capture:
                amount = min(amount, maximum_size + 1 - state.bytes_read)
                if amount <= 0:
                    raise ValueError("archive_body_size_exceeded")
            chunk = stream.read(amount)
            if capture:
                state.original_returns.append(chunk)
                if type(chunk) is not bytes or len(chunk) > amount:
                    raise TypeError("bounded_original_bytes_return_required")
            if chunk == b"":
                break
            digest.update(chunk)
            if capture:
                state.chunks.append(chunk)
                state.bytes_read += len(chunk)
                if state.bytes_read > maximum_size:
                    raise ValueError("archive_body_size_exceeded")
    except BaseException as error:  # noqa: BLE001 - settle original stream on interruption
        primary = error
    finally:
        if stream is not None:
            state.close_attempted = True
            try:
                closed = stream.close()
                state.close_returned = True
                if capture:
                    state.original_returns.append(closed)
            except BaseException as error:  # noqa: BLE001 - preserve close interruption
                if primary is None:
                    state.phase = "close"
                    primary = error
                else:
                    state.secondary_causes.append(error)
    if primary is not None:
        if not capture and state.secondary_causes:
            # Preserve legacy context-manager precedence for a combined failure.
            raise state.secondary_causes[-1] from primary
        raise primary
    state.phase = "postimage"
    if capture:
        state.original_returns.append(_path(path))
    after = _identity(path)
    if capture:
        state.original_returns.append(after)
    if after != before:
        raise ValueError("input_changed_during_observation")
    if capture and state.bytes_read != size:
        raise ValueError("archive_body_size_mismatch")
    actual = digest.hexdigest()
    if expected is not None and actual != expected:
        raise ValueError("input_digest_mismatch")
    state.invocation = "returned"
    return path.as_posix(), before, actual


def _file(path: Path, expected: str | None, size: int | None = None):
    return _read_input_file(path, expected, size, _FileReadState(), capture=False)


def observe_archive_body(request: ArchiveBodyRequest) -> ArchiveBodyObservation:
    """Bounded compressed bytes only; no parser, resource approval or authority."""
    state = _FileReadState()
    snapshot = None
    try:
        if type(request) is not ArchiveBodyRequest:
            raise TypeError("original_archive_body_request_required")
        if (
            type(request.path) is not type(Path())
            or not request.path.is_absolute()
            or ".." in request.path.parts
            or len(str(request.path).encode("utf-8", "strict")) > 4096
            or any(ord(char) < 32 or ord(char) == 127 for char in str(request.path))
            or type(request.sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", request.sha256) is None
            or type(request.size_bytes) is not int
            or not 0 < request.size_bytes <= 2**30
        ):
            raise ValueError("bounded_exact_archive_body_selection_required")
        snapshot = (request.path, request.sha256, request.size_bytes)
        original = _read_input_file(*snapshot, state, capture=True)
        state.phase = "selection_guard"
        if (
            type(request.path) is not type(snapshot[0])
            or type(request.sha256) is not str
            or type(request.size_bytes) is not int
            or (request.path, request.sha256, request.size_bytes) != snapshot
        ):
            raise ValueError("archive_body_selection_changed")
        state.phase = "body"
        body = b"".join(state.chunks)
        return ArchiveBodyObservation(
            request, snapshot, body, tuple(state.original_returns), original
        )
    except BaseException as error:
        raise ArchiveBodyObservationError(request, snapshot, state) from error


BACKING_IO_WINDOW = 32768
BACKING_MAX_READ_CALLS = 65538


@dataclass(frozen=True, slots=True, eq=False)
class ImmutableByteBacking:
    body: bytes
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class BackingReadStep:
    offset: int
    requested_bytes: int
    original_return: object
    validated_bytes: int
    prefix_sha256: str


@dataclass(frozen=True, slots=True, eq=False)
class BackingComparisonRequest:
    original_file_request: ArchiveBodyRequest
    expected_backing: ImmutableByteBacking


@dataclass(frozen=True, slots=True, eq=False)
class GuardedBackingObservation:
    original_request: ArchiveBodyRequest
    request_snapshot: tuple
    backing: ImmutableByteBacking
    original_returns: tuple[object, ...]
    steps: tuple[BackingReadStep, ...]
    original_file: tuple
    close_attempted: bool
    close_returned: bool
    cleanup: Literal["not_observed"] = "not_observed"
    authorizes_native_profile: Literal[False] = False


@dataclass(frozen=True, slots=True, eq=False)
class BackingComparisonObservation:
    original_request: BackingComparisonRequest
    request_snapshot: tuple
    expected_backing: ImmutableByteBacking
    original_returns: tuple[object, ...]
    steps: tuple[BackingReadStep, ...]
    original_file: tuple
    validated_bytes: int
    actual_sha256: str
    close_attempted: bool
    close_returned: bool
    cleanup: Literal["not_observed"] = "not_observed"
    original_raw_read_bytes_retained: Literal[False] = False
    authorizes_native_profile: Literal[False] = False


@dataclass
class _BackingReadState:
    phase: str = "selection"
    invocation: str = "not_invoked"
    original_returns: list[object] = field(default_factory=list)
    steps: list[BackingReadStep] = field(default_factory=list)
    prefix_bytes: int = 0
    prefix_sha256: str = field(default_factory=lambda: hashlib.sha256(b"").hexdigest())
    window_offset: int | None = None
    actual_window: bytes | None = None
    expected_window: bytes | None = None
    window_observation: str = "not_observed"
    close_attempted: bool = False
    close_returned: bool = False
    secondary_causes: list[BaseException] = field(default_factory=list)


class GuardedBackingError(RuntimeError):
    def __init__(self, request, snapshot, backing, state, cause):
        super().__init__("guarded_backing_" + state.phase)
        self.original_request = request
        self.request_snapshot = snapshot
        self.phase = state.phase
        self.invocation = state.invocation
        self.expected_backing = backing
        self.original_returns = tuple(state.original_returns)
        self.steps = tuple(state.steps)
        self.validated_prefix_bytes = state.prefix_bytes
        self.validated_prefix_sha256 = state.prefix_sha256
        self.window_offset = state.window_offset
        self.actual_window = state.actual_window
        self.expected_window = state.expected_window
        self.window_observation = state.window_observation
        self.acquired_prefix_bytes_unavailable = (
            backing is None and state.prefix_bytes > 0
        )
        self.raw_capture_complete = False
        self.close_attempted = state.close_attempted
        self.close_returned = state.close_returned
        self.primary_cause = cause
        self.secondary_causes = tuple(state.secondary_causes)
        self.cleanup = "not_observed"
        self.authorizes_retry = False
        self.authorizes_native_profile = False


def _backing_snapshot(backing, *, verify_digest):
    if (
        type(backing) is not ImmutableByteBacking
        or type(backing.body) is not bytes
        or type(backing.size_bytes) is not int
        or not 0 <= backing.size_bytes <= 2**30
        or len(backing.body) != backing.size_bytes
        or type(backing.sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", backing.sha256) is None
    ):
        raise ValueError("exact_immutable_byte_backing_required")
    if verify_digest and hashlib.sha256(backing.body).hexdigest() != backing.sha256:
        raise ValueError("immutable_backing_digest_mismatch")
    return backing.body, backing.size_bytes, backing.sha256


def borrow_immutable_backing(body: bytes) -> ImmutableByteBacking:
    """Retain the same immutable expectation bytes,not authority or a new copy."""
    if type(body) is not bytes or len(body) > 2**30:
        raise ValueError("exact_bounded_immutable_bytes_required")
    return ImmutableByteBacking(body, len(body), hashlib.sha256(body).hexdigest())


def _guarded_file_snapshot(request):
    if (
        type(request) is not ArchiveBodyRequest
        or type(request.path) is not type(Path())
        or not request.path.is_absolute()
        or ".." in request.path.parts
        or len(str(request.path).encode("utf-8", "strict")) > 4096
        or any(ord(char) < 32 or ord(char) == 127 for char in str(request.path))
        or type(request.sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", request.sha256) is None
        or type(request.size_bytes) is not int
        or not 0 < request.size_bytes <= 2**30
    ):
        raise ValueError("bounded_exact_archive_body_selection_required")
    return request.path, request.sha256, request.size_bytes


def _run_guarded_backing(original_request, *, comparison):
    """Single opt-in readinto engine in the original stream owner.

    Legacy read/return APIs above remain unchanged. New successful evidence
    contains actual readinto counts,not copied original raw-read byte objects.
    """
    state = _BackingReadState()
    snapshot = backing = backing_snapshot = None
    expected_body = b""
    stage = scratch = None
    try:
        if comparison:
            if type(original_request) is not BackingComparisonRequest:
                raise TypeError("original_backing_comparison_request_required")
            request = original_request.original_file_request
            backing = original_request.expected_backing
            backing_snapshot = _backing_snapshot(backing, verify_digest=True)
            expected_body = backing_snapshot[0]
        else:
            request = original_request
        file_snapshot = _guarded_file_snapshot(request)
        path, expected_digest, size = file_snapshot
        snapshot = (file_snapshot, backing_snapshot) if comparison else file_snapshot
        if comparison and (
            backing_snapshot is None or backing_snapshot[1:] != (size, expected_digest)
        ):
            raise ValueError("backing_file_request_mismatch")

        def current():
            if _guarded_file_snapshot(request) != file_snapshot:
                raise ValueError("guarded_file_selection_changed")
            if comparison:
                if backing_snapshot is None:
                    raise ValueError("original_backing_snapshot_required")
                now = _backing_snapshot(backing, verify_digest=False)
                if (
                    original_request.original_file_request is not request
                    or original_request.expected_backing is not backing
                    or now[0] is not backing_snapshot[0]
                    or now[1:] != backing_snapshot[1:]
                ):
                    raise ValueError("guarded_backing_selection_changed")

        state.phase, state.invocation = "path", "unknown"
        resolved = _path(path)
        state.original_returns.append(resolved)
        state.invocation = "returned"
        if type(resolved) is not type(path) or resolved != path:
            raise ValueError("original_guarded_path_required")
        current()
        state.phase, state.invocation = "preimage", "unknown"
        before = _identity(path)
        state.original_returns.append(before)
        state.invocation = "returned"
        if (
            type(before) is not tuple
            or len(before) != 5
            or any(type(x) is not int for x in before)
            or before[2] != size
        ):
            raise ValueError("regular_bound_input_required")
        state.invocation = "unknown"
        regular = path.is_file()
        state.original_returns.append(regular)
        state.invocation = "returned"
        if regular is not True:
            raise ValueError("regular_bound_input_required")
        current()
        # Only acquisition owns full staging;comparisons have one small window.
        state.phase, state.invocation = "staging", "unknown"
        if not comparison:
            stage = bytearray(size)
        scratch = bytearray(BACKING_IO_WINDOW)
        state.invocation = "returned"
        digest = hashlib.sha256()
        stream = None
        primary = None
        try:
            state.phase, state.invocation = "open", "unknown"
            stream = path.open("rb")
            state.original_returns.append(stream)
            state.invocation = "returned"
            current()
            state.phase, state.invocation = "descriptor", "unknown"
            info = os.fstat(stream.fileno())
            state.original_returns.append(info)
            state.invocation = "returned"
            if (
                type(info) is not os.stat_result
                or not stat.S_ISREG(info.st_mode)
                or (
                    info.st_dev,
                    info.st_ino,
                    info.st_size,
                    info.st_mtime_ns,
                    info.st_ctime_ns,
                )
                != before
            ):
                raise ValueError("opened_file_identity_mismatch")
            current()
            for _ in range(BACKING_MAX_READ_CALLS):
                offset = state.prefix_bytes
                amount = min(BACKING_IO_WINDOW, size - offset) if offset < size else 1
                storage = stage if stage is not None and offset < size else scratch
                start = offset if storage is stage else 0
                state.phase = "readinto"
                state.window_offset = offset
                state.window_observation = "unknown"
                state.actual_window = state.expected_window = None
                current()
                with (
                    memoryview(storage) as whole,
                    whole[start : start + amount] as window,
                ):
                    state.invocation = "unknown"
                    count = stream.readinto(window)
                    state.original_returns.append(count)
                    state.invocation = "returned"
                    current()
                    if type(count) is not int or not 0 <= count <= amount:
                        raise ValueError("bounded_original_readinto_count_required")
                    state.window_observation = "observed"
                    if count == 0:
                        state.actual_window = b""
                        state.expected_window = (
                            expected_body[offset : offset + amount]
                            if comparison
                            else None
                        )
                        state.steps.append(
                            BackingReadStep(
                                offset, amount, count, 0, digest.hexdigest()
                            )
                        )
                        if offset != size:
                            raise ValueError("guarded_backing_early_eof")
                        break
                    if offset == size:
                        state.actual_window = bytes(window[:count])
                        state.expected_window = b"" if comparison else None
                        state.steps.append(
                            BackingReadStep(
                                offset, amount, count, 0, digest.hexdigest()
                            )
                        )
                        raise ValueError("guarded_backing_growth")
                    matched = count
                    if comparison:
                        with memoryview(expected_body) as expected:
                            if window[:count] != expected[offset : offset + count]:
                                for index in range(count):
                                    if window[index] != expected[offset + index]:
                                        matched = index
                                        break
                    digest.update(window[:matched])
                    state.prefix_bytes += matched
                    state.prefix_sha256 = digest.hexdigest()
                    state.steps.append(
                        BackingReadStep(
                            offset, amount, count, matched, state.prefix_sha256
                        )
                    )
                    if matched != count:
                        state.actual_window = bytes(window[:count])
                        state.expected_window = expected_body[offset : offset + amount]
                        raise ValueError("guarded_backing_bytes_mismatch")
            else:
                raise ValueError("guarded_backing_read_capacity_exceeded")
        except BaseException as cause:  # noqa: BLE001 - settle once,preserve original read interruption
            primary = cause
        finally:
            if stream is not None:
                saved = state.phase, state.invocation
                had_primary = primary is not None
                state.phase, state.invocation = "close", "unknown"
                state.close_attempted = True
                try:
                    closed = stream.close()
                    state.close_returned = True
                    state.original_returns.append(closed)
                    state.invocation = "returned"
                    if closed is not None:
                        raise ValueError("original_guarded_close_return_required")
                except BaseException as cause:  # noqa: BLE001 - never repeat close or replace primary
                    if primary is None:
                        primary = cause
                    else:
                        state.secondary_causes.append(cause)
                if had_primary:
                    state.phase, state.invocation = saved
        if primary is not None:
            raise primary
        state.phase = "postimage"
        current()
        state.invocation = "unknown"
        after_path = _path(path)
        state.original_returns.append(after_path)
        state.invocation = "returned"
        if type(after_path) is not type(path) or after_path != path:
            raise ValueError("original_guarded_path_required")
        current()
        state.invocation = "unknown"
        after = _identity(path)
        state.original_returns.append(after)
        state.invocation = "returned"
        if (
            type(after) is not tuple
            or len(after) != 5
            or any(type(x) is not int for x in after)
            or after != before
        ):
            raise ValueError("input_changed_during_observation")
        current()
        state.phase = "digest"
        actual = digest.hexdigest()
        if state.prefix_bytes != size or actual != expected_digest:
            raise ValueError("input_digest_mismatch")
        original_file = (path.as_posix(), before, actual)
        if comparison:
            if type(backing) is not ImmutableByteBacking:
                raise ValueError("original_backing_reference_required")
            return BackingComparisonObservation(
                original_request,
                snapshot,
                backing,
                tuple(state.original_returns),
                tuple(state.steps),
                original_file,
                size,
                actual,
                state.close_attempted,
                state.close_returned,
            )
        state.phase = "immutable_publication"
        if stage is None:
            raise ValueError("original_owned_staging_required")
        state.invocation = "unknown"
        body = bytes(stage)
        stage = None  # Never retain mutable staging in successful observations.
        state.invocation = "returned"
        current()
        immutable = ImmutableByteBacking(body, size, actual)
        return GuardedBackingObservation(
            request,
            snapshot,
            immutable,
            tuple(state.original_returns),
            tuple(state.steps),
            original_file,
            state.close_attempted,
            state.close_returned,
        )
    except BaseException as cause:
        stage = scratch = None
        raise GuardedBackingError(
            original_request, snapshot, backing, state, cause
        ) from cause


def acquire_guarded_backing(request: ArchiveBodyRequest) -> GuardedBackingObservation:
    return _run_guarded_backing(request, comparison=False)


def compare_guarded_backing(
    request: BackingComparisonRequest,
) -> BackingComparisonObservation:
    return _run_guarded_backing(request, comparison=True)


def _environment(retention_root: Path | None = None):
    environment = {
        k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "LANG", "LC_ALL"}
    }
    environment.update(
        PYTHONDONTWRITEBYTECODE="1",
        PIP_NO_INDEX="1",
        PIP_NO_CACHE_DIR="1",
        PIP_CONFIG_FILE=os.devnull,
    )
    if retention_root is not None:
        environment["TMPDIR"] = str(retention_root)
    return environment


def snapshot_supplied_runtime_selection(
    selected: SuppliedRuntimeSelection | None,
) -> tuple:
    """Validate historical input values without observing files or custody.

    Shared by installation planning and receipt observation. A matching
    snapshot cannot establish current root identity or extraction completion.
    """
    if (
        type(selected) is not SuppliedRuntimeSelection
        or type(selected.grade) is not str
        or selected.grade != "ordinary_supplied_runtime_selection"
        or selected.authorizes_native_profile is not False
    ):
        raise ValueError("explicit_supplied_runtime_selection_required")
    for digest in (
        selected.python_sha256,
        selected.bootstrap_sha256,
        selected.archive_sha256,
        selected.roster_sha256,
    ):
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("exact_supplied_runtime_digest_required")
    if (
        type(selected.python_version) is not tuple
        or len(selected.python_version) != 3
        or any(type(v) is not int or not 0 <= v <= 255 for v in selected.python_version)
        or selected.python_version[:2] != (3, 12)
        or type(selected.root_identity) is not tuple
        or len(selected.root_identity) != 4
        or any(type(v) is not int or v < 0 for v in selected.root_identity)
    ):
        raise ValueError("exact_supplied_runtime_coordinates_required")
    if (
        type(selected.root) is not type(Path())
        or not selected.root.is_absolute()
        or ".." in selected.root.parts
    ):
        raise ValueError("explicit_absolute_path_required")
    return (
        str(selected.root),
        selected.root_identity,
        selected.python_sha256,
        selected.python_version,
        selected.bootstrap_sha256,
        selected.archive_sha256,
        selected.roster_sha256,
        selected.grade,
        selected.authorizes_native_profile,
    )


def supplied_runtime_projection(selected: SuppliedRuntimeSelection | None) -> dict:
    """Exact JSON-compatible historical projection, not a fresh observation."""
    values = snapshot_supplied_runtime_selection(selected)
    names = (
        "root",
        "root_identity",
        "python_sha256",
        "python_version",
        "bootstrap_sha256",
        "archive_sha256",
        "roster_sha256",
        "grade",
        "authorizes_native_profile",
    )
    return {
        name: list(value) if type(value) is tuple else value
        for name, value in zip(names, values, strict=True)
    }


def _supplied_selection(request: WholeEnvelopeInstallRequest) -> dict | None:
    selected = request.supplied_runtime
    if request.artifact.runtime_mode == "external":
        if selected is not None:
            raise ValueError("supplied_selection_cannot_relabel_external_mode")
        return None
    snapshot_supplied_runtime_selection(selected)
    assert type(selected) is SuppliedRuntimeSelection  # narrowed by the validator above
    root = _path(selected.root)
    if _private_root(root) != selected.root_identity:
        raise ValueError("supplied_runtime_root_changed")
    if request.installation_root.is_relative_to(root):
        raise ValueError("installation_inside_supplied_runtime_refused")
    python = root / "python/bin/python3.12"
    if request.python_executable != python:
        raise ValueError("supplied_python_coordinate_mismatch")
    _path(python)
    base = root / "python"
    base_identity = _private_root(base)
    return {
        "root": str(root),
        "root_identity": selected.root_identity,
        "python_sha256": selected.python_sha256,
        "python_version": selected.python_version,
        "bootstrap_sha256": selected.bootstrap_sha256,
        "archive_sha256": selected.archive_sha256,
        "roster_sha256": selected.roster_sha256,
        "prefix": str(base),
        "base_identity": base_identity,
        "stdlib": str(base / "lib/python3.12"),
        "grade": selected.grade,
        "authorizes_native_profile": False,
    }


def observe_supplied_runtime_selection(
    *,
    root: Path,
    python_sha256: str,
    python_version: tuple[int, int, int],
    bootstrap_sha256: str,
    archive_sha256: str,
    roster_sha256: str,
) -> SuppliedRuntimeSelection:
    """Current ordinary root preimage, without admission or dispatch.

    Planning validates every declared field. Re-observation never preserves a
    previously reviewed fingerprint when the root or selection has changed.
    """
    return SuppliedRuntimeSelection(
        root,
        _private_root(root),
        python_sha256,
        python_version,
        bootstrap_sha256,
        archive_sha256,
        roster_sha256,
    )


def _inspect(
    request: WholeEnvelopeInstallRequest, observations: list[RuntimeProbeEvidence]
) -> WholeEnvelopeInstallPlan:
    if (
        type(request) is not WholeEnvelopeInstallRequest
        or type(request.artifact) is not WholeEnvelopeArtifact
    ):
        raise TypeError("typed_whole_envelope_request_required")
    artifact = request.artifact
    if (
        type(request.timeout_seconds) is not int
        or not 1 <= request.timeout_seconds <= 3600
    ):
        raise ValueError("bounded_install_timeout_required")
    if (
        artifact.platform != "linux_x86_64"
        or artifact.python_minor != "3.12"
        or type(artifact.runtime_mode) is not str
        or artifact.runtime_mode not in ("external", "supplied")
        or platform.system() != "Linux"
        or platform.machine() != "x86_64"
    ):
        raise ValueError("qualified_external_python_linux_target_required")
    supplied = _supplied_selection(request)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,127}", artifact.release_id):
        raise ValueError("bounded_release_id_required")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,180}\.tar\.gz", artifact.envelope_name):
        raise ValueError("bounded_envelope_name_required")
    if not re.fullmatch(r"[0-9a-f]{40}", artifact.product_revision):
        raise ValueError("exact_product_revision_required")
    for name in (
        "envelope_sha256",
        "payload_sha256",
        "driver_sha256",
        "verifier_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", getattr(artifact, name)):
            raise ValueError("exact_artifact_digest_required")
    if (
        type(artifact.envelope_size) is not int
        or not 0 < artifact.envelope_size <= 2**30
    ):
        raise ValueError("bounded_envelope_size_required")
    bundle = _path(request.bundle_root)
    private = _private_root(request.installation_root)
    if bundle.is_relative_to(
        request.installation_root
    ) or request.installation_root.is_relative_to(bundle):
        raise ValueError("disjoint_bundle_installation_roots_required")
    target = request.installation_root / "env"
    if target.exists() or target.is_symlink():
        raise ValueError("fresh_environment_required")
    driver = bundle / "protocols/install.py"
    verifier = bundle / "releases" / artifact.release_id / "archive_verifier.py"
    envelope = verifier.parent / artifact.envelope_name
    inputs = [
        _file(driver, artifact.driver_sha256),
        _file(verifier, artifact.verifier_sha256),
        _file(envelope, artifact.envelope_sha256, artifact.envelope_size),
    ]
    # The selected original CLI driver uses these literal bindings. Preserve
    # them rather than adapting an old bundle manifest or executing a new parser.
    constants = {
        node.targets[0].id: node.value.value
        for node in ast.parse(driver.read_bytes()).body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
    }
    expected = {
        "PACKET_SHA": artifact.envelope_sha256,
        "PAYLOAD_SHA": artifact.payload_sha256,
        "VERIFIER_SHA": artifact.verifier_sha256,
        "ARCHIVE": artifact.envelope_name,
    }
    if any(constants.get(k) != v for k, v in expected.items()):
        raise ValueError("original_driver_binding_mismatch")
    python = request.python_executable
    if not isinstance(python, Path) or not python.is_absolute():
        raise ValueError("explicit_python_executable_required")
    python = python.resolve(strict=True)
    inputs.append(
        _file(python, None if supplied is None else supplied["python_sha256"])
    )
    probe_source = (
        "import json,platform,sys; print(json.dumps({'implementation':sys.implementation.name,"
        "'version':list(sys.version_info[:3]),'platform':sys.platform,'machine':platform.machine()}))"
    )
    if supplied is not None:
        probe_source = (
            "import json,platform,sys,sysconfig; print(json.dumps({'implementation':sys.implementation.name,"
            "'version':list(sys.version_info[:3]),'platform':sys.platform,'machine':platform.machine(),"
            "'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,"
            "'stdlib':sysconfig.get_path('stdlib'),'flags':[sys.flags.isolated,sys.flags.ignore_environment,"
            "sys.flags.no_user_site,sys.flags.dont_write_bytecode]}))"
        )
    command = [
        str(python),
        "-I",
        "-B",
        "-c",
        probe_source,
    ]
    try:
        probe = subprocess.run(
            command, env=_environment(), capture_output=True, check=False, timeout=30
        )
    except (Exception, KeyboardInterrupt) as error:
        observations.append(
            RuntimeProbeEvidence(
                "unknown",
                getattr(error, "output", b"") or b"",
                getattr(error, "stderr", b"") or b"",
                None,
            )
        )
        raise
    observations.append(
        RuntimeProbeEvidence("returned", probe.stdout, probe.stderr, probe.returncode)
    )
    if probe.returncode != 0:
        raise subprocess.CalledProcessError(
            probe.returncode, command, probe.stdout, probe.stderr
        )
    observation = _decode(probe.stdout)
    if (
        type(observation) is not dict
        or observation.get("implementation") != "cpython"
        or observation.get("version", [])[:2] != [3, 12]
        or observation.get("platform") != "linux"
        or observation.get("machine") != "x86_64"
    ):
        raise ValueError("observed_python_target_mismatch")
    if supplied is not None and (
        type(observation.get("version")) is not list
        or any(type(v) is not int for v in observation["version"])
        or observation.get("version") != list(supplied["python_version"])
        or observation.get("executable") != str(python)
        or observation.get("prefix") != supplied["prefix"]
        or observation.get("base_prefix") != supplied["prefix"]
        or observation.get("stdlib") != supplied["stdlib"]
        or type(observation.get("flags")) is not list
        or any(type(v) is not int for v in observation["flags"])
        or observation.get("flags") != [1, 1, 1, 1]
        or _supplied_selection(request) != supplied
    ):
        raise ValueError("observed_supplied_runtime_selection_mismatch")
    if any(_identity(Path(row[0])) != row[1] for row in inputs):
        raise ValueError("input_changed_after_runtime_probe")
    if (
        _private_root(request.installation_root) != private
        or target.exists()
        or target.is_symlink()
    ):
        raise ValueError("installation_preimage_changed")
    binding = {
        "artifact": asdict(artifact),
        "inputs": inputs,
        "private_root": private,
        "target": str(target),
        "runtime": observation,
        "runtime_streams": [
            hashlib.sha256(probe.stdout).hexdigest(),
            hashlib.sha256(probe.stderr).hexdigest(),
        ],
        "timeout_seconds": request.timeout_seconds,
    }
    if supplied is not None:
        binding["supplied_runtime"] = supplied
    fingerprint = hashlib.sha256(
        json.dumps(binding, sort_keys=True).encode()
    ).hexdigest()
    return WholeEnvelopeInstallPlan(
        request, fingerprint, target, python, probe.stdout, probe.stderr, private
    )


def plan_whole_envelope_install(
    request: WholeEnvelopeInstallRequest,
) -> WholeEnvelopeInstallPlan:
    """Observe exact inputs and explicit Python; never create installation files."""
    observations: list[RuntimeProbeEvidence] = []
    try:
        return _inspect(request, observations)
    except (Exception, KeyboardInterrupt) as error:
        raise WholeEnvelopeInstallError(
            request,
            "planning",
            "not_invoked",
            runtime_probe=observations[-1] if observations else None,
        ) from error


def install_whole_envelope(
    plan: WholeEnvelopeInstallPlan,
) -> WholeEnvelopeInstallResult:
    """Revalidate a reviewed plan, then call the original driver once. No retry."""
    if type(plan) is not WholeEnvelopeInstallPlan:
        raise TypeError("typed_whole_envelope_plan_required")
    invocation: Literal["not_invoked", "returned", "unknown"] = "not_invoked"
    phase = "revalidation"
    stdout, stderr, returncode = b"", b"", None
    observations: list[RuntimeProbeEvidence] = []
    try:
        fresh = _inspect(plan.request, observations)
        if fresh != plan:
            raise ValueError("installation_plan_stale")
        phase = "driver"
        invocation = "unknown"
        command = [
            str(plan.python_executable),
            "-I",
            "-B",
            str(plan.request.bundle_root / "protocols/install.py"),
            "--python-executable",
            str(plan.python_executable),
            "--venv",
            str(plan.environment),
        ]
        completed = subprocess.run(
            command,
            env=_environment(plan.request.installation_root),
            capture_output=True,
            check=False,
            timeout=plan.request.timeout_seconds,
        )
        invocation = "returned"
        stdout, stderr, returncode = (
            completed.stdout,
            completed.stderr,
            completed.returncode,
        )
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, command, stdout, stderr)
        phase = "result_validation"
        receipt_json = stdout.splitlines()[-1]
        receipt = _decode(receipt_json)
        artifact = plan.request.artifact
        if (
            type(receipt) is not dict
            or receipt.get("status") != "installed"
            or receipt.get("packet_sha256") != artifact.envelope_sha256
            or receipt.get("payload_sha256") != artifact.payload_sha256
            or receipt.get("venv") != str(plan.environment)
        ):
            raise ValueError("original_install_receipt_mismatch")
        if (
            _private_root(plan.request.installation_root)
            != plan.installation_root_identity
        ):
            raise ValueError("installation_root_identity_changed")
        retained = _path(Path(receipt["retained_source_and_notices"]))
        if (
            not retained.is_relative_to(plan.request.installation_root)
            or retained == plan.request.installation_root
            or not retained.is_dir()
            or not plan.environment.is_dir()
        ):
            raise ValueError("retained_installation_evidence_mismatch")
        for name in ("LICENSE", "NOTICE", "SOURCE-INDEX.json", "SHA256SUMS"):
            if not _path(retained / name).is_file():
                raise ValueError("retained_terms_source_missing")
        return WholeEnvelopeInstallResult(
            plan, returncode, stdout, stderr, receipt_json, retained
        )
    except (Exception, KeyboardInterrupt) as error:
        if invocation == "unknown":
            stdout = getattr(error, "output", b"") or b""
            stderr = getattr(error, "stderr", b"") or b""
        raise WholeEnvelopeInstallError(
            plan.request,
            phase,
            invocation,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            runtime_probe=observations[-1] if observations else None,
        ) from error
