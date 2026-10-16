from __future__ import annotations

import errno
import hashlib
import os
import stat
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any
from unicodedata import normalize
from uuid import uuid4

DEFAULT_CONFINED_MUTATION_MAX_BYTES = 16 * 1024 * 1024


class ConfinedMutationKind(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ConfinedMutationOutcome(StrEnum):
    APPLIED = "applied"
    CONFLICT = "conflict"
    DENIED = "denied"
    FAILED = "failed"


class ConfinedMutationEffectState(StrEnum):
    NONE = "none"
    APPLIED = "applied"
    UNKNOWN = "unknown"


class ConfinedMutationProfile(StrEnum):
    """Physical guarantees, not caller-authored proof of their availability.

    DESCRIPTOR_WALK_V1 preserves the existing cooperative-topology profile.
    It rejects symlink traversal but does not prevent an uncoordinated actor
    relocating an opened directory or replacing a checked target. The current
    backend cannot implement CONTINUOUS_ROOT_V1 and refuses it before I/O.
    """

    DESCRIPTOR_WALK_V1 = "descriptor_walk_v1"
    CONTINUOUS_ROOT_V1 = "continuous_root_v1"


class ConfinedObservationOutcome(StrEnum):
    OBSERVED = "observed"
    DENIED = "denied"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ConfinedFileObservation:
    path: str
    outcome: ConfinedObservationOutcome
    exists: bool
    content_digest: str | None = None
    size_bytes: int | None = None
    content: bytes | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        path = _relative_path(self.path)
        if type(self.outcome) is not ConfinedObservationOutcome:
            raise TypeError("Confined observation outcome must be exact")
        if type(self.exists) is not bool:
            raise TypeError("Confined observation exists must be exact bool")
        content = self.content
        if content is not None and type(content) is not bytes:
            raise TypeError("Confined observation content must be exact bytes")
        if self.outcome is ConfinedObservationOutcome.OBSERVED and self.exists:
            if (
                content is None
                or self.content_digest != _content_digest(content)
                or self.size_bytes != len(content)
                or self.error_code is not None
            ):
                raise ValueError("Observed file evidence is inconsistent")
        elif self.outcome is ConfinedObservationOutcome.OBSERVED:
            if any(
                value is not None
                for value in (
                    self.content_digest,
                    self.size_bytes,
                    content,
                    self.error_code,
                )
            ):
                raise ValueError("Observed absence carries file evidence")
        elif (
            self.exists
            or any(
                value is not None
                for value in (self.content_digest, self.size_bytes, content)
            )
            or not isinstance(self.error_code, str)
            or not self.error_code
        ):
            raise ValueError("Denied/failed observation evidence is inconsistent")
        object.__setattr__(self, "path", path)


@dataclass(frozen=True, slots=True)
class ConfinedFileReadCleanup:
    """Original once-only release knowledge, not recovery or authority."""

    outcome: str
    acquired_count: int | None
    release_attempted_count: int | None
    closed_count: int | None
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.outcome) is not str or self.outcome not in {
            "not_acquired",
            "closed",
            "unknown",
        }:
            raise ValueError("invalid_read_cleanup_outcome")
        counts = (self.acquired_count, self.release_attempted_count, self.closed_count)
        if any(
            value is not None and (type(value) is not int or not 0 <= value <= 65)
            for value in counts
        ):
            raise ValueError("invalid_read_cleanup_count")
        if type(self.diagnostics) is not tuple or len(self.diagnostics) > 16:
            raise ValueError("invalid_read_cleanup_diagnostics")
        for diagnostic in self.diagnostics:
            _read_text(diagnostic, 1024)
        if self.outcome == "not_acquired" and (counts != (0, 0, 0) or self.diagnostics):
            raise ValueError("invalid_not_acquired_cleanup")
        if self.outcome == "closed" and (
            self.acquired_count is None
            or self.acquired_count == 0
            or counts != (self.acquired_count,) * 3
            or self.diagnostics
        ):
            raise ValueError("invalid_closed_cleanup")
        acquired, attempted, closed = counts
        if (
            acquired is not None and attempted is not None and attempted > acquired
        ) or (attempted is not None and closed is not None and closed > attempted):
            raise ValueError("inconsistent_read_cleanup_counts")
        if (
            self.outcome == "unknown"
            and not self.diagnostics
            and (
                counts == (0, 0, 0)
                or acquired is not None
                and counts == (acquired,) * 3
            )
        ):
            raise ValueError("read_cleanup_uncertainty_required")


@dataclass(frozen=True, slots=True)
class ConfinedFileObservationWithCleanup:
    observation: ConfinedFileObservation
    root_locator: str
    path: str
    cleanup: ConfinedFileReadCleanup
    observation_grade: str = "observed_state"
    confinement_profile: str = "descriptor_walk_v1"

    def __post_init__(self) -> None:
        if type(self.observation) is not ConfinedFileObservation:
            raise TypeError("original_file_observation_required")
        self.observation.__post_init__()
        _read_root(self.root_locator)
        _saved_read_path(self.path)
        if self.observation.path != self.path:
            raise ValueError("read_path_correlation_failed")
        if type(self.cleanup) is not ConfinedFileReadCleanup:
            raise TypeError("original_read_cleanup_required")
        self.cleanup.__post_init__()
        if self.cleanup.outcome == "unknown":
            raise ValueError("read_cleanup_unverified")
        if self.observation.exists and self.cleanup.outcome != "closed":
            raise ValueError("read_acquisition_unverified")
        if (
            type(self.observation_grade) is not str
            or self.observation_grade != "observed_state"
        ):
            raise ValueError("unsupported_read_observation_grade")
        if (
            type(self.confinement_profile) is not str
            or self.confinement_profile != "descriptor_walk_v1"
        ):
            raise ValueError("unsupported_read_confinement_profile")


class ConfinedFileObservationError(RuntimeError):
    """A terminal read failure retaining primary cause and original cleanup."""

    _original_read_ledger: _ReadLedger | None = None

    def __init__(
        self,
        code: str,
        *,
        stage: str,
        cause_kind: str,
        root_locator: str | None,
        path: str | None,
        observation: ConfinedFileObservation | None,
        cleanup: ConfinedFileReadCleanup,
    ) -> None:
        for value in (code, stage, cause_kind):
            _read_text(value, 1024)
        if root_locator is not None:
            _read_root(root_locator)
        if path is not None:
            _saved_read_path(path)
        if observation is not None and type(observation) is not ConfinedFileObservation:
            raise TypeError("original_failure_observation_required")
        if type(cleanup) is not ConfinedFileReadCleanup:
            raise TypeError("original_failure_cleanup_required")
        cleanup.__post_init__()
        self.code = code
        self.stage = stage
        self.cause_kind = cause_kind
        self.root_locator = root_locator
        self.path = path
        # This original value was verified before a later failure. Do not
        # rehash it inside error construction and mask that primary failure.
        self.observation = observation
        self.cleanup = cleanup
        super().__init__(code)


def _read_text(value: str, maximum: int) -> None:
    if (
        type(value) is not str
        or not value
        or normalize("NFC", value) != value
        or any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F for c in value)
        or len(value.encode("utf-8")) > maximum
    ):
        raise ValueError("invalid_read_text")


def _read_root(value: str) -> None:
    _read_text(value, 4096)
    parsed = PurePosixPath(value)
    if not parsed.is_absolute() or str(parsed) != value or ".." in parsed.parts:
        raise ValueError("explicit_normalized_read_root_required")


def _saved_read_path(value: str) -> str:
    _read_text(value, 1024)
    path = _relative_path(value)
    if len(PurePosixPath(path).parts) > 64:
        raise ValueError("read_path_component_limit")
    return path


def _cause_kind(error: BaseException) -> str:
    # Fixed metadata bound; original exception remains the in-process cause.
    name = type(error).__name__
    return (
        "".join(c if c.isascii() and (c.isalnum() or c == "_") else "_" for c in name)[
            :128
        ]
        or "BaseException"
    )


@dataclass(slots=True)
class _ReadResource:
    descriptor: int | None = None
    spent: bool = False
    resource_ref: str | None = None
    kind: str | None = None
    path: str | None = None


@dataclass(slots=True)
class _ReadLedger:
    resources: list[_ReadResource] = field(default_factory=list)
    stage: str = "validation"
    acquisition_unknown: bool = False
    release_unknown: bool = False
    context_unknown: bool = False
    attempted: int = 0
    attempts_unknown: bool = False
    closed: int = 0
    diagnostics: list[str] = field(default_factory=list)
    first_cleanup_error: BaseException | None = None

    def diagnostic(self, value: str) -> None:
        if len(self.diagnostics) < 16:
            self.diagnostics.append(value)
        else:
            self.diagnostics[-1] = "cleanup_diagnostics_incomplete"

    def open(
        self,
        path: str | Path,
        flags: int,
        *,
        dir_fd: int | None = None,
        mode: int | None = None,
    ) -> int:
        # Reserve original custody before dispatch; failed allocation cannot
        # leak an already-acquired descriptor.
        resource = _ReadResource(
            resource_ref="read-resource:" + uuid4().hex,
            kind="root_descriptor"
            if dir_fd is None and flags & os.O_DIRECTORY
            else "directory_descriptor"
            if flags & os.O_DIRECTORY
            else "file_descriptor",
            path=str(path)
            if dir_fd is None
            else next(
                (
                    str(Path(row.path) / path)
                    for row in self.resources
                    if row.descriptor == dir_fd and row.path is not None
                ),
                None,
            ),
        )
        self.resources.append(resource)
        descriptor = None
        try:
            if mode is None:
                descriptor = os.open(path, flags, dir_fd=dir_fd)
            else:
                descriptor = os.open(path, flags, mode, dir_fd=dir_fd)
            resource.descriptor = descriptor
        except BaseException as error:
            # Definite POSIX refusal supplies no fd. Interruptions and missing
            # syscall returns do not establish zero acquisition.
            if descriptor is not None:
                object.__setattr__(resource, "descriptor", descriptor)
            elif not isinstance(error, OSError) or error.errno not in {
                errno.ENOENT,
                errno.ENOTDIR,
                errno.EACCES,
                errno.EPERM,
                errno.ELOOP,
                errno.ENAMETOOLONG,
            }:
                self.acquisition_unknown = True
                self.diagnostic(
                    self.stage + ":acquisition_unknown:" + _cause_kind(error)
                )
            raise
        return descriptor

    def close(self, descriptor: int) -> None:
        resource = None
        dispatched = False
        try:
            resource = next(
                item
                for item in self.resources
                if item.descriptor == descriptor and not item.spent
            )
            # Spend first. Never retry a possibly reused descriptor after a
            # missing return or interrupted dispatch/accounting.
            resource.spent = True
            self.attempted += 1
            dispatched = True
            os.close(descriptor)
            self.closed += 1
        except BaseException as error:  # noqa: BLE001 - attempt remaining original closes after interruption
            if resource is not None:
                object.__setattr__(resource, "spent", True)
            if not dispatched:
                self.attempts_unknown = True
            self.release_unknown = True
            self.diagnostic("close_unknown:" + _cause_kind(error))
            if self.first_cleanup_error is None:
                self.first_cleanup_error = error

    def close_all(self) -> None:
        self.close_unspent()

    def cleanup_failure(self, error: BaseException, boundary: str) -> None:
        self.context_unknown = True
        self.diagnostic(boundary + ":" + _cause_kind(error))
        if self.first_cleanup_error is None:
            self.first_cleanup_error = error

    def close_unspent(self) -> None:
        # Continue original custody after an interrupted drain. Already spent
        # rights, including uncertain closes, are never dispatched again.
        for resource in reversed(self.resources):
            if resource.descriptor is not None and not resource.spent:
                self.close(resource.descriptor)

    def snapshot(self) -> ConfinedFileReadCleanup:
        return self.snapshot_value()

    def snapshot_value(self) -> ConfinedFileReadCleanup:
        acquired = (
            None
            if self.acquisition_unknown
            else sum(item.descriptor is not None for item in self.resources)
        )
        closed = None if self.release_unknown else self.closed
        if (
            self.acquisition_unknown
            or self.release_unknown
            or self.context_unknown
            or self.diagnostics
        ):
            outcome = "unknown"
        else:
            outcome = "not_acquired" if acquired == 0 else "closed"
        return ConfinedFileReadCleanup(
            outcome,
            acquired,
            None if self.attempts_unknown else self.attempted,
            closed,
            tuple(self.diagnostics),
        )


@dataclass(frozen=True, slots=True)
class ConfinedTextReplacement:
    old_text: str
    new_text: str

    def __post_init__(self) -> None:
        if not isinstance(self.old_text, str) or not self.old_text:
            raise ValueError("Confined text replacement old_text must be non-empty")
        if not isinstance(self.new_text, str):
            raise ValueError("Confined text replacement new_text must be text")


@dataclass(frozen=True, slots=True)
class ConfinedFileMutationRequest:
    kind: ConfinedMutationKind
    path: str
    expected_exists: bool
    expected_content_digest: str | None
    content: bytes | None = None
    text_replacements: tuple[ConfinedTextReplacement, ...] = ()
    maximum_bytes: int = DEFAULT_CONFINED_MUTATION_MAX_BYTES

    def __post_init__(self) -> None:
        normalized_path = _relative_path(self.path)
        expected_digest = _optional_digest(self.expected_content_digest)
        content = None if self.content is None else bytes(self.content)
        replacements = tuple(self.text_replacements)
        if len(replacements) > 64:
            raise ValueError("Confined text replacements exceed bound")
        if not 0 < self.maximum_bytes <= DEFAULT_CONFINED_MUTATION_MAX_BYTES:
            raise ValueError("Confined mutation byte bound is invalid")
        if content is not None and len(content) > self.maximum_bytes:
            raise ValueError("Confined mutation content exceeds byte bound")
        if self.kind is ConfinedMutationKind.CREATE:
            if (
                self.expected_exists
                or expected_digest is not None
                or content is None
                or replacements
            ):
                raise ValueError("Create requires absent baseline and content")
        elif self.kind is ConfinedMutationKind.UPDATE:
            if (
                not self.expected_exists
                or expected_digest is None
                or ((content is None) == (not replacements))
            ):
                raise ValueError(
                    "Update requires exact baseline and either content or text replacements"
                )
        elif self.kind is ConfinedMutationKind.DELETE and (
            not self.expected_exists
            or expected_digest is None
            or content is not None
            or replacements
        ):
            raise ValueError("Delete requires exact existing baseline and no content")
        object.__setattr__(self, "path", normalized_path)
        object.__setattr__(self, "expected_content_digest", expected_digest)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "text_replacements", replacements)


@dataclass(frozen=True, slots=True)
class ConfinedFileMutationResult:
    kind: ConfinedMutationKind
    path: str
    outcome: ConfinedMutationOutcome
    before_exists: bool
    before_content_digest: str | None
    before_size_bytes: int | None
    after_exists: bool
    after_content_digest: str | None
    after_size_bytes: int | None
    before_content: bytes | None = None
    after_content: bytes | None = None
    error_code: str | None = None
    confinement_profile: ConfinedMutationProfile = (
        ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    )
    # Effect evidence is independent of completion/durability. These are local
    # writer observations, not a transferable source-admission capability.
    effect_applied: bool = False
    durability_confirmed: bool = False
    effect_state: ConfinedMutationEffectState = ConfinedMutationEffectState.NONE

    def __post_init__(self) -> None:
        if type(self.confinement_profile) is not ConfinedMutationProfile:
            raise TypeError("Confined mutation profile must be exact")


@dataclass(frozen=True, slots=True)
class _ConfinedWriterStep:
    """Original writer operation; not a caller-supplied program or authority."""

    kind: str
    path: str
    function: object
    arguments: tuple[Any, ...]
    keywords: dict[str, Any]
    cleanup: bool = False


def _drive_confined_writer(generator):
    """Run the original synchronous API with its unchanged native operations."""
    try:
        step = next(generator)
        while True:
            try:
                result = step.function(*step.arguments, **step.keywords)
            except BaseException as error:  # noqa: BLE001 - original writer unwind also handles interruptions
                step = generator.throw(error)
            else:
                step = generator.send(result)
    except StopIteration as complete:
        return complete.value


def mutate_confined_file(
    *,
    root: Path,
    request: ConfinedFileMutationRequest,
    confinement_profile: ConfinedMutationProfile = ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
) -> ConfinedFileMutationResult:
    """Run the original CREATE/UPDATE/DELETE writer; descriptor walk is cooperative.

    The retained A1 sequence pauses this same writer before its physical steps.
    The synchronous entrance keeps its original mode, error and cleanup behavior.
    """
    return _drive_confined_writer(
        _confined_file_writer_steps(
            root=root, request=request, confinement_profile=confinement_profile
        )
    )


def _confined_file_writer_steps(
    *,
    root: Path,
    request: ConfinedFileMutationRequest,
    confinement_profile: ConfinedMutationProfile = (
        ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    ),
    _step_mode: bool = False,
    _scratch_name: str | None = None,
    _io: Any = os,
):
    """Use the shared primitive under an explicit physical guarantee profile.

    The descriptor walk rejects symlinked path components. Create uses an
    atomic no-replace link; update uses same-directory atomic replacement; and
    delete validates the observed inode immediately before unlink. This is the
    legacy physical byte operation used inside a Workspace-owned serialization
    boundary. That boundary does not exclude arbitrary external topology or
    target changes. Pinned descriptors alone cannot establish continuous root
    confinement; consumers requiring it must not fall back to the legacy
    profile. Refusal precedes even root resolution, traversal and scratch I/O.
    """

    if type(confinement_profile) is not ConfinedMutationProfile:
        raise TypeError("Confined mutation profile must be exact")
    if confinement_profile is ConfinedMutationProfile.CONTINUOUS_ROOT_V1:
        return _result(
            request,
            outcome=ConfinedMutationOutcome.DENIED,
            before_exists=False,
            error_code="continuous_root_confinement_unavailable",
            confinement_profile=confinement_profile,
        )

    root_path = root.expanduser().resolve()
    if not root_path.is_dir():
        raise ValueError("Confined mutation root must be an existing directory")
    required = ("O_DIRECTORY", "O_NOFOLLOW")
    if not all(hasattr(os, name) for name in required):
        return _result(
            request,
            outcome=ConfinedMutationOutcome.DENIED,
            before_exists=False,
            error_code="secure_descriptor_traversal_unavailable",
        )

    descriptors: list[int] = []
    temporary_name: str | None = None
    parent_descriptor: int | None = None
    before_content: bytes | None = None
    before_exists = False
    before_digest: str | None = None
    before_size: int | None = None
    after_content: bytes | None = None
    effect_applied = False
    effect_attempted = False
    durability_confirmed = False

    def failed_effect(error_code: str) -> ConfinedFileMutationResult:
        has_after = effect_applied and request.kind is not ConfinedMutationKind.DELETE
        return _result(
            request,
            outcome=ConfinedMutationOutcome.FAILED,
            before_exists=before_exists,
            before_content_digest=before_digest,
            before_size_bytes=before_size,
            before_content=before_content,
            after_exists=has_after,
            after_content=after_content if has_after else None,
            after_content_digest=(
                _content_digest(after_content)
                if has_after and after_content is not None
                else None
            ),
            after_size_bytes=(
                len(after_content) if has_after and after_content is not None else None
            ),
            effect_applied=effect_applied,
            effect_state=(
                ConfinedMutationEffectState.APPLIED
                if effect_applied
                else ConfinedMutationEffectState.UNKNOWN
                if effect_attempted
                else ConfinedMutationEffectState.NONE
            ),
            durability_confirmed=durability_confirmed,
            error_code=error_code,
        )

    def perform() -> Generator[_ConfinedWriterStep, Any, ConfinedFileMutationResult]:
        nonlocal parent_descriptor, temporary_name, before_content, before_exists
        nonlocal effect_attempted
        nonlocal \
            before_digest, \
            before_size, \
            after_content, \
            effect_applied, \
            durability_confirmed
        try:
            if _step_mode:
                parent_descriptor = yield from _open_parent_steps(
                    root=root_path,
                    path=request.path,
                    descriptors=descriptors,
                    create_missing=request.kind is ConfinedMutationKind.CREATE,
                    _io=_io,
                )
            else:
                parent_descriptor = _open_parent(
                    root=root_path,
                    path=request.path,
                    descriptors=descriptors,
                    create_missing=request.kind is ConfinedMutationKind.CREATE,
                )
            assert parent_descriptor is not None
            leaf = PurePosixPath(request.path).name
            current = _read_current(
                parent_descriptor=parent_descriptor,
                leaf=leaf,
                maximum_bytes=request.maximum_bytes,
                _read_ledger=_io if _step_mode else None,
            )
            if isinstance(current, str):
                return _result(
                    request,
                    outcome=ConfinedMutationOutcome.DENIED,
                    before_exists=False,
                    error_code=current,
                )
            before_content, before_stat = current
            before_exists = before_stat is not None
            before_digest = (
                _content_digest(before_content) if before_content is not None else None
            )
            before_size = len(before_content) if before_content is not None else None

            if before_exists != request.expected_exists:
                return _result(
                    request,
                    outcome=ConfinedMutationOutcome.CONFLICT,
                    before_exists=before_exists,
                    before_content_digest=before_digest,
                    before_size_bytes=before_size,
                    before_content=before_content,
                    error_code="expected_existence_mismatch",
                )
            if request.expected_content_digest != before_digest:
                return _result(
                    request,
                    outcome=ConfinedMutationOutcome.CONFLICT,
                    before_exists=before_exists,
                    before_content_digest=before_digest,
                    before_size_bytes=before_size,
                    before_content=before_content,
                    error_code="expected_content_digest_mismatch",
                )

            if request.kind is ConfinedMutationKind.DELETE:
                assert before_stat is not None
                if not _same_path_state(parent_descriptor, leaf, before_stat):
                    return _result(
                        request,
                        outcome=ConfinedMutationOutcome.CONFLICT,
                        before_exists=True,
                        before_content_digest=before_digest,
                        before_size_bytes=before_size,
                        before_content=before_content,
                        error_code="target_changed_before_delete",
                    )
                effect_attempted = True
                yield _ConfinedWriterStep(
                    "target_delete",
                    request.path,
                    _io.unlink,
                    (leaf,),
                    {"dir_fd": parent_descriptor},
                )
                effect_applied = True
                yield _ConfinedWriterStep(
                    "parent_sync", request.path, _io.fsync, (parent_descriptor,), {}
                )
                durability_confirmed = True
                return _result(
                    request,
                    outcome=ConfinedMutationOutcome.APPLIED,
                    before_exists=True,
                    before_content_digest=before_digest,
                    before_size_bytes=before_size,
                    before_content=before_content,
                )

            after_content = request.content
            if request.text_replacements:
                assert before_content is not None
                transformed = _apply_text_replacements(
                    before_content,
                    request.text_replacements,
                    maximum_bytes=request.maximum_bytes,
                )
                if isinstance(transformed, str):
                    return _result(
                        request,
                        outcome=ConfinedMutationOutcome.CONFLICT,
                        before_exists=True,
                        before_content_digest=before_digest,
                        before_size_bytes=before_size,
                        before_content=before_content,
                        error_code=transformed,
                    )
                after_content = transformed
            assert after_content is not None
            temporary_name = _scratch_name or f".aware-cas-{os.getpid()}-{uuid4().hex}"
            mode = 0o666 if before_stat is None else stat.S_IMODE(before_stat.st_mode)
            if _step_mode:
                yield from _write_temporary_steps(
                    parent_descriptor=parent_descriptor,
                    name=temporary_name,
                    content=after_content,
                    mode=mode,
                    preserve_mode=before_stat is not None,
                    _io=_io,
                    _path=request.path,
                )
            else:
                _write_temporary(
                    parent_descriptor=parent_descriptor,
                    name=temporary_name,
                    content=after_content,
                    mode=mode,
                    preserve_mode=before_stat is not None,
                )
            if request.kind is ConfinedMutationKind.CREATE:
                try:
                    effect_attempted = True
                    yield _ConfinedWriterStep(
                        "target_link",
                        request.path,
                        _io.link,
                        (temporary_name, leaf),
                        {
                            "src_dir_fd": parent_descriptor,
                            "dst_dir_fd": parent_descriptor,
                            "follow_symlinks": False,
                        },
                    )
                    effect_applied = True
                except FileExistsError:
                    return _result(
                        request,
                        outcome=ConfinedMutationOutcome.CONFLICT,
                        before_exists=False,
                        error_code="target_created_concurrently",
                    )
                yield _ConfinedWriterStep(
                    "scratch_unlink",
                    request.path,
                    _io.unlink,
                    (temporary_name,),
                    {"dir_fd": parent_descriptor},
                )
                temporary_name = None
            else:
                assert before_stat is not None
                if not _same_path_state(parent_descriptor, leaf, before_stat):
                    return _result(
                        request,
                        outcome=ConfinedMutationOutcome.CONFLICT,
                        before_exists=True,
                        before_content_digest=before_digest,
                        before_size_bytes=before_size,
                        before_content=before_content,
                        error_code="target_changed_before_replace",
                    )
                effect_attempted = True
                yield _ConfinedWriterStep(
                    "target_replace",
                    request.path,
                    _io.replace,
                    (temporary_name, leaf),
                    {"src_dir_fd": parent_descriptor, "dst_dir_fd": parent_descriptor},
                )
                effect_applied = True
                temporary_name = None
            yield _ConfinedWriterStep(
                "parent_sync", request.path, _io.fsync, (parent_descriptor,), {}
            )
            durability_confirmed = True
            after_digest = _content_digest(after_content)
            return _result(
                request,
                outcome=ConfinedMutationOutcome.APPLIED,
                before_exists=before_exists,
                before_content_digest=before_digest,
                before_size_bytes=before_size,
                before_content=before_content,
                after_exists=True,
                after_content_digest=after_digest,
                after_size_bytes=len(after_content),
                after_content=after_content,
            )
        except (NotADirectoryError, FileNotFoundError, PermissionError):
            if effect_attempted:
                return failed_effect("filesystem_effect_failed_after_application")
            return _result(
                request,
                outcome=ConfinedMutationOutcome.DENIED,
                before_exists=False,
                error_code="path_unavailable_or_unconfined",
            )
        except OSError:
            return failed_effect("filesystem_effect_failed")

    try:
        result = yield from perform()
    finally:
        cleanup_failed = False
        if temporary_name is not None and parent_descriptor is not None:
            try:
                yield _ConfinedWriterStep(
                    "scratch_unlink",
                    request.path,
                    _io.unlink,
                    (temporary_name,),
                    {"dir_fd": parent_descriptor},
                    cleanup=True,
                )
            except FileNotFoundError:
                pass
            except OSError:
                cleanup_failed = True
        for descriptor in reversed(descriptors):
            try:
                yield _ConfinedWriterStep(
                    "resource_release",
                    request.path,
                    _io.close,
                    (descriptor,),
                    {},
                    cleanup=True,
                )
            except OSError:
                cleanup_failed = True

    if cleanup_failed:
        return failed_effect("filesystem_cleanup_failed")
    return result


def observe_confined_file(
    *,
    root: Path,
    path: str,
    maximum_bytes: int = DEFAULT_CONFINED_MUTATION_MAX_BYTES,
) -> ConfinedFileObservation:
    """Read one exact file state through the same descriptor-confined walk."""

    root_path = root.expanduser().resolve()
    normalized_path = _relative_path(path)
    if not 0 < maximum_bytes <= DEFAULT_CONFINED_MUTATION_MAX_BYTES:
        raise ValueError("Confined observation byte bound is invalid")
    if not root_path.is_dir():
        raise ValueError("Confined observation root must be an existing directory")
    if not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
        return ConfinedFileObservation(
            normalized_path,
            ConfinedObservationOutcome.DENIED,
            False,
            error_code="secure_descriptor_traversal_unavailable",
        )

    descriptors: list[int] = []
    try:
        parent_descriptor = _open_parent(
            root=root_path,
            path=normalized_path,
            descriptors=descriptors,
            create_missing=False,
        )
        current = _read_current(
            parent_descriptor=parent_descriptor,
            leaf=PurePosixPath(normalized_path).name,
            maximum_bytes=maximum_bytes,
        )
        if isinstance(current, str):
            return ConfinedFileObservation(
                normalized_path,
                ConfinedObservationOutcome.DENIED,
                False,
                error_code=current,
            )
        content, current_stat = current
        if current_stat is None:
            return ConfinedFileObservation(
                normalized_path, ConfinedObservationOutcome.OBSERVED, False
            )
        assert content is not None
        return ConfinedFileObservation(
            normalized_path,
            ConfinedObservationOutcome.OBSERVED,
            True,
            _content_digest(content),
            len(content),
            content,
        )
    except FileNotFoundError:
        return ConfinedFileObservation(
            normalized_path, ConfinedObservationOutcome.OBSERVED, False
        )
    except (NotADirectoryError, PermissionError):
        return ConfinedFileObservation(
            normalized_path,
            ConfinedObservationOutcome.DENIED,
            False,
            error_code="path_unavailable_or_unconfined",
        )
    except OSError:
        return ConfinedFileObservation(
            normalized_path,
            ConfinedObservationOutcome.FAILED,
            False,
            error_code="filesystem_observation_failed",
        )
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def observe_confined_file_with_cleanup(
    *, root: Path, path: str, maximum_bytes: int = DEFAULT_CONFINED_MUTATION_MAX_BYTES
) -> ConfinedFileObservationWithCleanup:
    """Original bounded descriptor read with once-only cleanup evidence."""
    result, _, _ = _observe_confined_file_with_custody(
        root=root, path=path, maximum_bytes=maximum_bytes
    )
    return result


def _observe_confined_file_with_custody(
    *,
    root: Path,
    path: str,
    maximum_bytes: int = DEFAULT_CONFINED_MUTATION_MAX_BYTES,
) -> tuple[ConfinedFileObservationWithCleanup, os.stat_result | None, _ReadLedger]:
    """Original bounded read plus once-only cleanup, never write authority.

    This explicit-root entrance is additive. Legacy observers retain their
    normalization/error semantics; no physical algorithm is copied here.
    All failures, including interruption, retain original owner evidence.
    """
    ledger = _ReadLedger()
    captured_stat = None
    root_locator = normalized_path = None
    observation = None
    primary = None
    failed_stage = "validation"
    try:
        if not isinstance(root, Path):
            raise TypeError("explicit_path_root_required")
        root_text = str(root)
        _read_root(root_text)
        root_locator = root_text
        # The caller's Path subclass is not a live interpretation callback.
        # Use one detached spelling for validation, traversal and evidence.
        root_path = Path(root_text)
        normalized_path = _saved_read_path(path)
        if (
            type(maximum_bytes) is not int
            or not 0 < maximum_bytes <= DEFAULT_CONFINED_MUTATION_MAX_BYTES
        ):
            raise ValueError("invalid_read_byte_bound")
        ledger.stage = "root_validation"
        if root_path.resolve(strict=True) != root_path:
            raise ValueError("read_root_alias_refused")
        if not root_path.is_dir():
            raise ValueError("read_root_directory_required")
        if not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
            observation = ConfinedFileObservation(
                normalized_path,
                ConfinedObservationOutcome.DENIED,
                False,
                error_code="secure_descriptor_traversal_unavailable",
            )
        else:
            descriptors: list[int] = []
            try:
                parent = _open_parent(
                    root=root_path,
                    path=normalized_path,
                    descriptors=descriptors,
                    create_missing=False,
                    _read_ledger=ledger,
                )
                current = _read_current(
                    parent_descriptor=parent,
                    leaf=PurePosixPath(normalized_path).name,
                    maximum_bytes=maximum_bytes,
                    _read_ledger=ledger,
                )
            except FileNotFoundError as error:
                if error.errno != errno.ENOENT or ledger.acquisition_unknown:
                    raise
                current = (None, None)
            ledger.stage = "observation"
            if isinstance(current, str):
                observation = ConfinedFileObservation(
                    normalized_path,
                    ConfinedObservationOutcome.DENIED,
                    False,
                    error_code=current,
                )
            else:
                content, current_stat = current
                captured_stat = current_stat
                if current_stat is None:
                    observation = ConfinedFileObservation(
                        normalized_path,
                        ConfinedObservationOutcome.OBSERVED,
                        False,
                    )
                else:
                    assert content is not None
                    ledger.stage = "digest"
                    digest = _content_digest(content)
                    ledger.stage = "observation"
                    observation = ConfinedFileObservation(
                        normalized_path,
                        ConfinedObservationOutcome.OBSERVED,
                        True,
                        digest,
                        len(content),
                        content,
                    )
    except BaseException as error:  # noqa: BLE001 - interrupted reads must finish original cleanup
        primary = error
        failed_stage = ledger.stage
    finally:
        try:
            ledger.close_all()
        except BaseException as error:  # noqa: BLE001 - cleanup-boundary interruption cannot erase read evidence
            ledger.cleanup_failure(error, "cleanup_boundary_unknown")
            try:
                ledger.close_unspent()
            except BaseException as continuation_error:  # noqa: BLE001 - retain unresolved original custody without replay
                ledger.cleanup_failure(
                    continuation_error, "cleanup_continuation_unknown"
                )
    try:
        cleanup = ledger.snapshot()
    except BaseException as error:  # noqa: BLE001 - snapshot failure must not mask the original read or reclose resources
        ledger.cleanup_failure(error, "cleanup_snapshot_unknown")
        try:
            # Data-only projection of the same original ledger. Do not replay
            # the failed snapshot entrance or any physical disposal.
            cleanup = ledger.snapshot_value()
        except BaseException as evidence_error:  # noqa: BLE001 - unavailable accounting is unknown, never zero
            ledger.cleanup_failure(evidence_error, "cleanup_accounting_unknown")
            cleanup = ConfinedFileReadCleanup(
                "unknown", None, None, None, tuple(ledger.diagnostics)
            )
    if primary is None and cleanup.outcome == "unknown":
        primary = ledger.first_cleanup_error or RuntimeError("read_cleanup_unverified")
        failed_stage = "cleanup"
    if primary is not None:
        failure = ConfinedFileObservationError(
            "filesystem_read_failed"
            if failed_stage != "cleanup"
            else "filesystem_read_cleanup_unverified",
            stage=failed_stage,
            cause_kind=_cause_kind(primary),
            root_locator=root_locator,
            path=normalized_path,
            observation=observation,
            cleanup=cleanup,
        )
        failure._original_read_ledger = ledger
        raise failure from primary
    assert (
        observation is not None
        and root_locator is not None
        and normalized_path is not None
    )
    try:
        result = ConfinedFileObservationWithCleanup(
            observation,
            root_locator,
            normalized_path,
            cleanup,
        )
        return result, captured_stat, ledger
    except BaseException as error:
        failure = ConfinedFileObservationError(
            "filesystem_read_return_invalid",
            stage="result",
            cause_kind=_cause_kind(error),
            root_locator=root_locator,
            path=normalized_path,
            observation=observation,
            cleanup=cleanup,
        )
        failure._original_read_ledger = ledger
        raise failure from error


def _open_parent(
    *,
    root: Path,
    path: str,
    descriptors: list[int],
    create_missing: bool = False,
    _read_ledger: _ReadLedger | None = None,
    _release_previous: bool = False,
) -> int:
    return _drive_confined_writer(
        _open_parent_steps(
            root=root,
            path=path,
            descriptors=descriptors,
            create_missing=create_missing,
            _read_ledger=_read_ledger,
            _release_previous=_release_previous,
        )
    )


def _open_parent_steps(
    *,
    root: Path,
    path: str,
    descriptors: list[int],
    create_missing: bool = False,
    _read_ledger: _ReadLedger | None = None,
    _release_previous: bool = False,
    _io: Any = os,
):
    if _release_previous and _read_ledger is None:
        raise ValueError("Bounded traversal requires original read custody")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if _read_ledger is not None:
        _read_ledger.stage = "root_open"
    current = (
        _io.open(root, flags)
        if _read_ledger is None
        else _read_ledger.open(root, flags)
    )
    descriptors.append(current)
    prefix = []
    for part in PurePosixPath(path).parts[:-1]:
        prefix.append(part)
        if _read_ledger is not None:
            _read_ledger.stage = "parent_open"
        try:
            next_descriptor = (
                _io.open(part, flags, dir_fd=current)
                if _read_ledger is None
                else _read_ledger.open(part, flags, dir_fd=current)
            )
        except FileNotFoundError:
            if not create_missing:
                raise
            try:
                yield _ConfinedWriterStep(
                    "ancestor_create",
                    "/".join(prefix),
                    _io.mkdir,
                    (part,),
                    {"dir_fd": current},
                )
            except FileExistsError:
                pass
            else:
                yield _ConfinedWriterStep(
                    "ancestor_sync", "/".join(prefix), _io.fsync, (current,), {}
                )
            next_descriptor = _io.open(part, flags, dir_fd=current)
        if _release_previous:
            assert _read_ledger is not None
            _read_ledger.close(current)
            descriptors.remove(current)
        current = next_descriptor
        descriptors.append(current)
    return current


def _read_current(
    *,
    parent_descriptor: int,
    leaf: str,
    maximum_bytes: int,
    _read_ledger: _ReadLedger | None = None,
) -> tuple[bytes | None, os.stat_result | None] | str:
    if _read_ledger is not None:
        _read_ledger.stage = "leaf_stat"
    try:
        path_stat = os.stat(leaf, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None, None
    if not stat.S_ISREG(path_stat.st_mode):
        return "target_is_not_regular_file"
    # A regular source can be substituted with a FIFO between stat and open.
    # Nonblocking open prevents an untrusted replacement from hanging readback;
    # the original stat comparison still rejects that changed identity/type.
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    if _read_ledger is not None:
        _read_ledger.stage = "leaf_open"
    descriptor = (
        os.open(leaf, flags, dir_fd=parent_descriptor)
        if _read_ledger is None
        else _read_ledger.open(leaf, flags, dir_fd=parent_descriptor)
    )
    try:
        if _read_ledger is not None:
            _read_ledger.stage = "leaf_stat_before"
        before = os.fstat(descriptor)
        if not _same_stat(before, path_stat) or before.st_size > maximum_bytes:
            return "target_changed_or_exceeds_byte_bound"
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            if _read_ledger is not None:
                _read_ledger.stage = "read"
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        if _read_ledger is not None:
            _read_ledger.stage = "leaf_stat_after"
        after = os.fstat(descriptor)
        if len(content) > maximum_bytes or not _same_stat(before, after):
            return "target_changed_or_exceeds_byte_bound"
        return content, after
    finally:
        if _read_ledger is None:
            os.close(descriptor)
        else:
            _read_ledger.close(descriptor)


def _write_temporary(
    *,
    parent_descriptor: int,
    name: str,
    content: bytes,
    mode: int,
    preserve_mode: bool = False,
    _io: Any = os,
) -> None:
    _drive_confined_writer(
        _write_temporary_steps(
            parent_descriptor=parent_descriptor,
            name=name,
            content=content,
            mode=mode,
            preserve_mode=preserve_mode,
            _io=_io,
        )
    )


def _write_confined_bytes(_io, descriptor: int, content: bytes) -> None:
    view = memoryview(content)
    while view:
        written = _io.write(descriptor, view)
        if written <= 0:
            raise OSError("Confined mutation write made no progress")
        view = view[written:]


def _write_temporary_steps(
    *,
    parent_descriptor: int,
    name: str,
    content: bytes,
    mode: int,
    preserve_mode: bool = False,
    _io: Any = os,
    _path="",
):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    descriptor = yield _ConfinedWriterStep(
        "scratch_create",
        _path,
        _io.open,
        (name, flags, mode),
        {"dir_fd": parent_descriptor},
    )
    try:
        yield _ConfinedWriterStep(
            "scratch_write",
            _path,
            _write_confined_bytes,
            (_io, descriptor, content),
            {},
        )
        if preserve_mode:
            yield _ConfinedWriterStep(
                "scratch_restore_mode", _path, _io.fchmod, (descriptor, mode), {}
            )
        yield _ConfinedWriterStep("scratch_sync", _path, _io.fsync, (descriptor,), {})
    finally:
        yield _ConfinedWriterStep(
            "scratch_close", _path, _io.close, (descriptor,), {}, cleanup=True
        )


def _apply_text_replacements(
    content: bytes,
    replacements: tuple[ConfinedTextReplacement, ...],
    *,
    maximum_bytes: int,
) -> bytes | str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return "text_replacement_source_not_utf8"
    for replacement in replacements:
        if text.count(replacement.old_text) != 1:
            return "text_replacement_not_unique"
        text = text.replace(replacement.old_text, replacement.new_text, 1)
        if len(text.encode("utf-8")) > maximum_bytes:
            return "text_replacement_exceeds_byte_bound"
    encoded = text.encode("utf-8")
    if encoded == content:
        return "text_replacement_no_content_change"
    return encoded


def _same_path_state(
    parent_descriptor: int, leaf: str, expected: os.stat_result
) -> bool:
    try:
        current = os.stat(leaf, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return _same_stat(current, expected)


def _same_stat(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_mode,
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_mode,
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


def _relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Confined mutation path must be a POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or path == PurePosixPath(".") or ".." in path.parts:
        raise ValueError("Confined mutation path must remain below root")
    normalized = str(path)
    if normalized != value or any(part in {"", "."} for part in path.parts):
        raise ValueError("Confined mutation path must be normalized")
    return normalized


def _optional_digest(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if not normalized.startswith("sha256:") or len(normalized) != 71:
        raise ValueError("Expected content digest must be sha256-prefixed")
    if any(character not in "0123456789abcdef" for character in normalized[7:]):
        raise ValueError("Expected content digest must be hexadecimal")
    return normalized


def _content_digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _result(
    request: ConfinedFileMutationRequest,
    *,
    outcome: ConfinedMutationOutcome,
    before_exists: bool,
    before_content_digest: str | None = None,
    before_size_bytes: int | None = None,
    before_content: bytes | None = None,
    after_exists: bool = False,
    after_content_digest: str | None = None,
    after_size_bytes: int | None = None,
    after_content: bytes | None = None,
    error_code: str | None = None,
    confinement_profile: ConfinedMutationProfile = (
        ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    ),
    effect_applied: bool | None = None,
    durability_confirmed: bool | None = None,
    effect_state: ConfinedMutationEffectState | None = None,
) -> ConfinedFileMutationResult:
    return ConfinedFileMutationResult(
        kind=request.kind,
        path=request.path,
        outcome=outcome,
        before_exists=before_exists,
        before_content_digest=before_content_digest,
        before_size_bytes=before_size_bytes,
        after_exists=after_exists,
        after_content_digest=after_content_digest,
        after_size_bytes=after_size_bytes,
        before_content=before_content,
        after_content=after_content,
        error_code=error_code,
        confinement_profile=confinement_profile,
        effect_state=(
            ConfinedMutationEffectState.APPLIED
            if outcome is ConfinedMutationOutcome.APPLIED
            else ConfinedMutationEffectState.NONE
        )
        if effect_state is None
        else effect_state,
        effect_applied=(
            outcome is ConfinedMutationOutcome.APPLIED
            if effect_applied is None
            else effect_applied
        ),
        durability_confirmed=(
            outcome is ConfinedMutationOutcome.APPLIED
            if durability_confirmed is None
            else durability_confirmed
        ),
    )


# C is additive. These native request/evidence values are not permissions.
def _tree_text(value: str) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or normalize("NFC", value) != value
        or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value)
        or len(value.encode("utf-8")) > 1024
    ):
        raise ValueError("invalid_tree_text")


def _tree_path(value: str) -> str:
    _tree_text(value)
    return _relative_path(value)


def _tree_digest(value: str) -> None:
    _tree_text(value)
    if (
        len(value) != 71
        or not value.startswith("sha256:")
        or any(c not in "0123456789abcdef" for c in value[7:])
    ):
        raise ValueError("invalid_tree_digest")


def _tree_integer(value: int, ceiling: int = 2**64 - 1) -> None:
    if type(value) is not int or not 0 <= value <= ceiling:
        raise ValueError("invalid_tree_integer")


def _tree_identity(value: tuple[int, int]) -> None:
    if type(value) is not tuple or len(value) != 2:
        raise ValueError("invalid_tree_identity")
    for member in value:
        _tree_integer(member)


@dataclass(frozen=True, slots=True)
class ConfinedTreeEntryPin:
    exists: bool
    device: int | None = None
    inode: int | None = None
    size_bytes: int | None = None
    mtime_ns: int | None = None
    ctime_ns: int | None = None
    mode: int | None = None
    link_count: int | None = None
    content_digest: str | None = None

    def __post_init__(self) -> None:
        if type(self.exists) is not bool:
            raise ValueError("invalid_tree_exists")
        numbers = (
            self.device,
            self.inode,
            self.size_bytes,
            self.mtime_ns,
            self.ctime_ns,
            self.mode,
            self.link_count,
        )
        if not self.exists:
            if any(v is not None for v in (*numbers, self.content_digest)):
                raise ValueError("tree_absence_carries_no_preimage")
            return
        for value in numbers:
            _tree_integer(value)
        _tree_integer(self.mode, 0o7777)
        if self.link_count < 1:
            raise ValueError("invalid_tree_link_count")
        if self.content_digest is not None:
            _tree_digest(self.content_digest)


@dataclass(frozen=True, slots=True)
class ConfinedTreeFileTransition:
    path: str
    kind: ConfinedMutationKind
    before: ConfinedTreeEntryPin
    content: bytes | None
    content_digest: str | None
    size_bytes: int | None
    requested_mode: int | None

    def __post_init__(self) -> None:
        _tree_path(self.path)
        if (
            type(self.kind) is not ConfinedMutationKind
            or type(self.before) is not ConfinedTreeEntryPin
        ):
            raise ValueError("original_tree_kind_and_pin_required")
        self.before.__post_init__()
        if self.kind is ConfinedMutationKind.CREATE:
            if self.before.exists:
                raise ValueError("tree_create_requires_absence")
        elif (
            not self.before.exists
            or self.before.content_digest is None
            or self.before.link_count != 1
            or self.before.mode & 0o7000
        ):
            raise ValueError("tree_update_delete_require_ordinary_single_link_preimage")
        if self.kind is ConfinedMutationKind.DELETE:
            if any(
                v is not None
                for v in (
                    self.content,
                    self.content_digest,
                    self.size_bytes,
                    self.requested_mode,
                )
            ):
                raise ValueError("tree_delete_has_no_successor")
        elif (
            type(self.content) is not bytes
            or len(self.content) > DEFAULT_CONFINED_MUTATION_MAX_BYTES
            or type(self.size_bytes) is not int
            or self.size_bytes != len(self.content)
            or self.content_digest != _content_digest(self.content)
            or type(self.requested_mode) is not int
            or self.requested_mode not in (0o644, 0o755)
        ):
            raise ValueError("invalid_exact_tree_successor")


@dataclass(frozen=True, slots=True)
class ConfinedTreeAncestorTransition:
    path: str
    intent: str
    before: ConfinedTreeEntryPin
    requested_mode: int | None

    def __post_init__(self) -> None:
        _tree_path(self.path)
        if (
            type(self.before) is not ConfinedTreeEntryPin
            or type(self.intent) is not str
        ):
            raise ValueError("invalid_tree_ancestor")
        self.before.__post_init__()
        if self.intent == "create":
            if (
                self.before.exists
                or type(self.requested_mode) is not int
                or self.requested_mode != 0o755
            ):
                raise ValueError("tree_ancestor_create_requires_absence_and_0755")
        elif self.intent == "preserve":
            if (
                not self.before.exists
                or self.before.content_digest is not None
                or self.requested_mode is not None
            ):
                raise ValueError("tree_preserved_ancestor_is_read_only")
        else:
            raise ValueError("unsupported_tree_ancestor_intent")


@dataclass(frozen=True, slots=True)
class ConfinedTreeLimits:
    maximum_file_transitions: int = 4096
    maximum_ancestors: int = 4096
    maximum_file_bytes: int = 16 * 1024 * 1024
    maximum_combined_body_bytes: int = 512 * 1024 * 1024
    maximum_metadata_bytes: int = 8 * 1024 * 1024
    maximum_path_utf8_bytes: int = 1024
    maximum_live_descriptors: int = 64

    def __post_init__(self) -> None:
        for value, ceiling in zip(
            (
                self.maximum_file_transitions,
                self.maximum_ancestors,
                self.maximum_file_bytes,
                self.maximum_combined_body_bytes,
                self.maximum_metadata_bytes,
                self.maximum_path_utf8_bytes,
                self.maximum_live_descriptors,
            ),
            (
                4096,
                4096,
                16 * 1024 * 1024,
                512 * 1024 * 1024,
                8 * 1024 * 1024,
                1024,
                64,
            ),
            strict=True,
        ):
            _tree_integer(value, ceiling)
            if value == 0:
                raise ValueError("tree_limits_must_be_positive")


@dataclass(frozen=True, slots=True)
class ConfinedTreeProjectionRequest:
    request_ref: str
    root_identity: tuple[int, int]
    files: tuple[ConfinedTreeFileTransition, ...]
    ancestors: tuple[ConfinedTreeAncestorTransition, ...]
    limits: ConfinedTreeLimits = ConfinedTreeLimits()

    def __post_init__(self) -> None:
        _tree_text(self.request_ref)
        _tree_identity(self.root_identity)
        if type(self.limits) is not ConfinedTreeLimits:
            raise ValueError("original_tree_limits_required")
        self.limits.__post_init__()
        if type(self.files) is not tuple or type(self.ancestors) is not tuple:
            raise ValueError("exact_tree_sequences_required")
        if (
            len(self.files) > self.limits.maximum_file_transitions
            or len(self.ancestors) > self.limits.maximum_ancestors
        ):
            raise ValueError("tree_count_capacity_exceeded")
        if any(
            type(row) is not ConfinedTreeFileTransition for row in self.files
        ) or any(
            type(row) is not ConfinedTreeAncestorTransition for row in self.ancestors
        ):
            raise ValueError("original_tree_transition_values_required")
        for row in (*self.files, *self.ancestors):
            row.__post_init__()
            if len(row.path.encode("utf-8")) > self.limits.maximum_path_utf8_bytes:
                raise ValueError("tree_path_byte_capacity_exceeded")
        names = tuple(row.path for row in self.files)
        directories = tuple(row.path for row in self.ancestors)
        if names != tuple(sorted(set(names))) or directories != tuple(
            sorted(set(directories), key=lambda p: (p.count("/"), p))
        ):
            raise ValueError("tree_sequences_must_have_canonical_unique_order")
        all_paths = set(names) | set(directories)
        if len(all_paths) != len(names) + len(directories):
            raise ValueError("tree_file_ancestor_collision")
        for path in all_paths:
            if any(
                str(parent) not in directories
                for parent in PurePosixPath(path).parents
                if str(parent) != "."
            ):
                raise ValueError("tree_ancestors_must_be_explicit")
        if any(
            parent in names
            for path in all_paths
            for parent in (str(p) for p in PurePosixPath(path).parents)
        ):
            raise ValueError("tree_file_cannot_be_an_ancestor")
        combined = 0
        for row in self.files:
            before_size = row.before.size_bytes or 0
            after_size = row.size_bytes or 0
            if max(before_size, after_size) > self.limits.maximum_file_bytes:
                raise ValueError("tree_file_byte_capacity_exceeded")
            combined += before_size + after_size
        if combined > self.limits.maximum_combined_body_bytes:
            raise ValueError("tree_combined_body_capacity_exceeded")


@dataclass(frozen=True, slots=True)
class ConfinedTreeScratchEffect:
    """Descriptive helper, not a portable root or an issued scratch inode."""

    path: str
    role: str
    ordinal: int
    kind: str
    requested_mode: int | None


@dataclass(frozen=True, slots=True)
class ConfinedTreePreparationObservation:
    preparation_ref: str
    request_ref: str
    request_digest: str
    root_identity: tuple[int, int]
    transition_order: tuple[tuple[int, str, str], ...]
    read_pins: tuple[tuple[str, ConfinedTreeEntryPin], ...]
    scratch_effects: tuple[ConfinedTreeScratchEffect, ...]
    resource_bound: int


@dataclass(frozen=True, slots=True)
class ConfinedTreeResourceCleanup:
    resource_ref: str
    kind: str
    path: str | None
    ownership: str
    cleanup_attempted: bool
    cleanup_state: str
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConfinedTreePhysicalEffect:
    effect_ref: str
    ordinal: int
    path: str
    role: str
    kind: str
    state: ConfinedMutationEffectState
    before_identity: tuple[int, int] | None
    after_identity: tuple[int, int] | None
    before_digest: str | None
    after_digest: str | None
    before_size_bytes: int | None
    after_size_bytes: int | None
    before_mode: int | None
    after_mode: int | None
    durability_confirmed: bool
    error_ref: str | None


@dataclass(frozen=True, slots=True)
class ConfinedTreeCleanupObservation:
    preparation_ref: str | None
    request_ref: str | None
    resources: tuple[ConfinedTreeResourceCleanup, ...]
    residual_scratch: tuple[str, ...]
    cleanup_state: str
    diagnostics: tuple[str, ...]
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class ConfinedTreeTransitionResult:
    preparation_ref: str
    request_ref: str
    ordinal: int
    path: str
    kind: str
    effects: tuple[ConfinedTreePhysicalEffect, ...]
    before: ConfinedTreeEntryPin
    after: ConfinedTreeEntryPin | None
    pending_ordinal: int | None
    effect_state: ConfinedMutationEffectState
    completion_state: str
    durability_confirmed: bool
    convergence_state: str
    error_ref: str | None
    error_code: str | None
    cleanup: ConfinedTreeCleanupObservation


@dataclass(frozen=True, slots=True)
class ConfinedTreeEffectObservation:
    preparation_ref: str
    request_ref: str
    effects: tuple[ConfinedTreePhysicalEffect, ...]
    completed_prefix: int
    pending_ordinal: int | None
    phase: str
    final_entries: tuple[tuple[str, ConfinedTreeEntryPin], ...]
    ledger_complete: bool
    diagnostics: tuple[str, ...]
    residual_scratch: tuple[str, ...]
