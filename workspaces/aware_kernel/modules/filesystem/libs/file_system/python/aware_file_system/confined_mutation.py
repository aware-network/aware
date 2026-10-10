from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
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


def mutate_confined_file(
    *,
    root: Path,
    request: ConfinedFileMutationRequest,
    confinement_profile: ConfinedMutationProfile = (
        ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    ),
) -> ConfinedFileMutationResult:
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

    def perform() -> ConfinedFileMutationResult:
        nonlocal parent_descriptor, temporary_name, before_content, before_exists
        nonlocal effect_attempted
        nonlocal \
            before_digest, \
            before_size, \
            after_content, \
            effect_applied, \
            durability_confirmed
        try:
            parent_descriptor = _open_parent(
                root=root_path,
                path=request.path,
                descriptors=descriptors,
                create_missing=request.kind is ConfinedMutationKind.CREATE,
            )
            leaf = PurePosixPath(request.path).name
            current = _read_current(
                parent_descriptor=parent_descriptor,
                leaf=leaf,
                maximum_bytes=request.maximum_bytes,
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
                os.unlink(leaf, dir_fd=parent_descriptor)
                effect_applied = True
                os.fsync(parent_descriptor)
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
            temporary_name = f".aware-cas-{os.getpid()}-{uuid4().hex}"
            mode = 0o666 if before_stat is None else stat.S_IMODE(before_stat.st_mode)
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
                    os.link(
                        temporary_name,
                        leaf,
                        src_dir_fd=parent_descriptor,
                        dst_dir_fd=parent_descriptor,
                        follow_symlinks=False,
                    )
                    effect_applied = True
                except FileExistsError:
                    return _result(
                        request,
                        outcome=ConfinedMutationOutcome.CONFLICT,
                        before_exists=False,
                        error_code="target_created_concurrently",
                    )
                os.unlink(temporary_name, dir_fd=parent_descriptor)
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
                os.replace(
                    temporary_name,
                    leaf,
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=parent_descriptor,
                )
                effect_applied = True
                temporary_name = None
            os.fsync(parent_descriptor)
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
        result = perform()
    finally:
        cleanup_failed = False
        if temporary_name is not None and parent_descriptor is not None:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except FileNotFoundError:
                pass
            except OSError:
                cleanup_failed = True
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
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


def _open_parent(
    *,
    root: Path,
    path: str,
    descriptors: list[int],
    create_missing: bool = False,
) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current = os.open(root, flags)
    descriptors.append(current)
    for part in PurePosixPath(path).parts[:-1]:
        try:
            next_descriptor = os.open(part, flags, dir_fd=current)
        except FileNotFoundError:
            if not create_missing:
                raise
            try:
                os.mkdir(part, dir_fd=current)
            except FileExistsError:
                pass
            else:
                os.fsync(current)
            next_descriptor = os.open(part, flags, dir_fd=current)
        current = next_descriptor
        descriptors.append(current)
    return current


def _read_current(
    *, parent_descriptor: int, leaf: str, maximum_bytes: int
) -> tuple[bytes | None, os.stat_result | None] | str:
    try:
        path_stat = os.stat(leaf, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None, None
    if not stat.S_ISREG(path_stat.st_mode):
        return "target_is_not_regular_file"
    # A regular source can be substituted with a FIFO between stat and open.
    # Nonblocking open prevents an untrusted replacement from hanging readback;
    # the original stat comparison still rejects that changed identity/type.
    descriptor = os.open(
        leaf,
        os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
        dir_fd=parent_descriptor,
    )
    try:
        before = os.fstat(descriptor)
        if not _same_stat(before, path_stat) or before.st_size > maximum_bytes:
            return "target_changed_or_exceeds_byte_bound"
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
        if len(content) > maximum_bytes or not _same_stat(before, after):
            return "target_changed_or_exceeds_byte_bound"
        return content, after
    finally:
        os.close(descriptor)


def _write_temporary(
    *,
    parent_descriptor: int,
    name: str,
    content: bytes,
    mode: int,
    preserve_mode: bool = False,
) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    descriptor = os.open(name, flags, mode, dir_fd=parent_descriptor)
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("Confined mutation write made no progress")
            view = view[written:]
        if preserve_mode:
            # Creation mode is umask-filtered. Restore the existing file's
            # exact mode after writing (writing can clear special bits).
            os.fchmod(descriptor, mode)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


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
