"""Retained, cooperative physical source preparation; no Issue authority.

Handles are process-local owner-issued objects, not decoded evidence. The
descriptor-walk profile still requires cooperative topology: retaining an fd
does not prevent another process relocating a directory between checks.
Currentness compares exact bytes and the observed device/inode, mode, size,
nanosecond mtime/ctime and single-link condition. This is not write-history
detection: equal-byte same-inode writes may leave all observed fields identical.
Consumers requiring detection of every intervening write cannot use this profile
as that stronger admission; no continuous exclusion or monotonic change token
is supplied by these observations.
"""

from __future__ import annotations

import os
import stat
import threading
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import NoReturn, Protocol, final
from uuid import uuid4
from weakref import WeakKeyDictionary, finalize

from .confined_mutation import (
    DEFAULT_CONFINED_MUTATION_MAX_BYTES,
    ConfinedMutationEffectState,
    ConfinedMutationProfile,
    _content_digest,
    _read_current,
    _relative_path,
    _same_stat,
    _write_temporary,
)


@dataclass(frozen=True, slots=True)
class RetainedPhysicalEffect:
    path: str
    kind: str
    state: ConfinedMutationEffectState
    durability_confirmed: bool = False
    mode: int | None = None
    before_digest: str | None = None
    after_digest: str | None = None
    after_identity: tuple[int, int] | None = None


class RetainedPhysicalMutationRefusal(RuntimeError):
    def __init__(self, code: str, effects=(), residual_scratch_paths=()):
        super().__init__(code)
        self.code = code
        self.effects = tuple(effects)
        self.residual_scratch_paths = tuple(residual_scratch_paths)


class _RetainedDirectoryState(Protocol):
    root: Path
    root_fd: int | None
    phase: str
    pins: dict[str, os.stat_result | None]
    effects: list[RetainedPhysicalEffect]
    residual_scratch_paths: list[str]


@dataclass
class _State:
    root: Path
    root_fd: int | None
    root_stat: os.stat_result
    target: str
    original: os.stat_result
    before: bytes
    candidate: bytes
    directories: tuple[str, ...]
    pins: dict[str, os.stat_result | None]
    pid: int = field(default_factory=os.getpid)
    phase: str = "issued"
    next_directory: int = 0
    replacement: os.stat_result | None = None
    replacement_verified: bool = False
    effects: list[RetainedPhysicalEffect] = field(default_factory=list)
    residual_scratch_paths: list[str] = field(default_factory=list)
    lock: threading.RLock = field(default_factory=threading.RLock)


_HANDLES: WeakKeyDictionary[RetainedPhysicalMutation, _State] = WeakKeyDictionary()
_DIRECTORY_FLAGS = (
    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
)


@final
class RetainedPhysicalMutation:
    """Use only the factory; its evidence cannot mint or replace a handle."""

    # CPython initializes the weakref slot; construction is intentionally owner-only.
    __slots__: tuple[str, ...] = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("Use retain_confined_manifest_replacement")

    def __copy__(self):
        raise TypeError("Retained physical mutation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Retained physical mutation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Retained physical mutation cannot be serialized")

    @property
    def effects(self) -> tuple[RetainedPhysicalEffect, ...]:
        return tuple(_issued(self).effects)

    @property
    def phase(self) -> str:
        return _issued(self).phase

    def validate_current(self) -> None:
        state = _issued(self)
        with state.lock:
            _check_or_retire(state)

    def prepare_next_directory(self) -> RetainedPhysicalEffect:
        state = _issued(self)
        with state.lock:
            _check_or_retire(state)
            if state.phase not in {
                "issued",
                "preparing",
            } or state.next_directory >= len(state.directories):
                _refuse(state, "directory_transition_invalid")
            path = state.directories[state.next_directory]
            state.phase = "preparing"
            effect = _prepare_directory(state, path)
            state.next_directory += 1
            _check_or_retire(state)
            return effect

    def replace_manifest(self) -> RetainedPhysicalEffect:
        state = _issued(self)
        with state.lock:
            _check_or_retire(state)
            if state.phase not in {
                "issued",
                "preparing",
            } or state.next_directory != len(state.directories):
                _refuse(state, "replacement_transition_invalid")
            parent = None
            if state.before == state.candidate:
                state.replacement = state.original
                state.replacement_verified = True
                state.phase = "replaced"
                effect = RetainedPhysicalEffect(
                    state.target,
                    "manifest",
                    ConfinedMutationEffectState.NONE,
                    mode=stat.S_IMODE(state.original.st_mode),
                    before_digest=_content_digest(state.before),
                    after_digest=_content_digest(state.before),
                    after_identity=_identity(state.original),
                )
                state.effects.append(effect)
                return effect
            scratch = f".aware-cas-{os.getpid()}-{uuid4().hex}"
            scratch_path = str(PurePosixPath(state.target).parent / scratch)
            effect = RetainedPhysicalEffect(
                state.target,
                "manifest",
                ConfinedMutationEffectState.NONE,
                before_digest=_content_digest(state.before),
            )
            try:
                parent = _directory_fd(state, str(PurePosixPath(state.target).parent))
                mode = stat.S_IMODE(state.original.st_mode)
                _write_temporary(
                    parent_descriptor=parent,
                    name=scratch,
                    content=state.candidate,
                    mode=mode,
                    preserve_mode=True,
                )
                expected_inode = os.stat(scratch, dir_fd=parent, follow_symlinks=False)
                _check_or_retire(state)
                effect = RetainedPhysicalEffect(
                    state.target,
                    "manifest",
                    ConfinedMutationEffectState.UNKNOWN,
                    mode=mode,
                    before_digest=_content_digest(state.before),
                )
                os.replace(
                    scratch,
                    PurePosixPath(state.target).name,
                    src_dir_fd=parent,
                    dst_dir_fd=parent,
                )
                scratch = ""
                state.replacement = expected_inode
                state.phase = "replaced"
                effect = RetainedPhysicalEffect(
                    state.target,
                    "manifest",
                    ConfinedMutationEffectState.APPLIED,
                    mode=mode,
                    before_digest=_content_digest(state.before),
                    after_digest=_content_digest(state.candidate),
                    after_identity=_identity(expected_inode),
                )
                state.effects.append(effect)
                _check_or_retire(state)
                os.fsync(parent)
                effect = RetainedPhysicalEffect(
                    state.target,
                    "manifest",
                    ConfinedMutationEffectState.APPLIED,
                    True,
                    mode,
                    _content_digest(state.before),
                    _content_digest(state.candidate),
                    _identity(expected_inode),
                )
                state.effects[-1] = effect
                _check_or_retire(state)
                return effect
            except BaseException as error:  # noqa: BLE001 - retain effects and retire even on interruption
                if not state.effects or state.effects[-1].kind != "manifest":
                    state.effects.append(effect)
                _refuse(
                    state, getattr(error, "code", "manifest_replacement_failed"), error
                )
            finally:
                cleanup_error = None
                if parent is not None and scratch:
                    try:
                        os.unlink(scratch, dir_fd=parent)
                    except FileNotFoundError:
                        pass
                    except OSError as error:
                        state.residual_scratch_paths.append(scratch_path)
                        cleanup_error = error
                if parent is not None:
                    _close_or_retire(state, parent)
                if cleanup_error is not None:
                    _refuse(state, "scratch_cleanup_failed", cleanup_error)

    def finish(self) -> tuple[RetainedPhysicalEffect, ...]:
        state = _issued(self)
        with state.lock:
            _check_or_retire(state)
            if state.phase != "replaced":
                _refuse(state, "finish_transition_invalid")
            _release_root(state)
            state.phase = "consumed"
            return tuple(state.effects)

    def release(self) -> None:
        state = _issued(self)
        with state.lock:
            if state.phase not in {"retired", "consumed"}:
                state.phase = "retired"
                _release_root(state)

    def validate_consumed_current(self) -> None:
        """Read-only original-pin check; never renew mutation authority.

        Temporary descriptors establish a bounded cooperative read horizon,
        not continuous confinement or a new admission. Observed mismatch retires
        it; an unobservable intervening write is not claimed to be detected.
        """
        state = _issued(self)
        with state.lock:
            if state.phase != "consumed":
                _refuse(state, "consumed_identity_required")
            try:
                state.root_fd = os.open(state.root, _DIRECTORY_FLAGS)
                _verify(state)
            except BaseException as error:  # noqa: BLE001 - interrupted revalidation remains terminal
                _refuse(
                    state,
                    getattr(error, "code", "consumed_identity_unavailable"),
                    error,
                )
            finally:
                _release_root(state)


def retain_confined_manifest_replacement(
    *,
    root: Path,
    target_path: str,
    expected_content_digest: str,
    content: bytes,
    directory_paths: tuple[str, ...] = (),
    confinement_profile: ConfinedMutationProfile = ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
) -> RetainedPhysicalMutation:
    if type(confinement_profile) is not ConfinedMutationProfile:
        raise TypeError("Physical profile must be exact")
    if confinement_profile is not ConfinedMutationProfile.DESCRIPTOR_WALK_V1:
        raise RetainedPhysicalMutationRefusal("continuous_root_confinement_unavailable")
    if not all(hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW")):
        raise RetainedPhysicalMutationRefusal("descriptor_profile_unavailable")
    target = _relative_path(target_path)
    if type(content) is not bytes or len(content) > DEFAULT_CONFINED_MUTATION_MAX_BYTES:
        raise ValueError("Candidate must be bounded exact bytes")
    if type(directory_paths) is not tuple or len(directory_paths) > 64:
        raise ValueError("Explicit directory sequence must be a bounded tuple")
    directories = tuple(_relative_path(path) for path in directory_paths)
    if len(set(directories)) != len(directories) or target in directories:
        raise ValueError("Effect paths must be distinct")
    root_path = root.expanduser().absolute()
    root_fd = os.open(root_path, _DIRECTORY_FLAGS)
    state = None
    try:
        root_stat = os.fstat(root_fd)
        # State starts with no candidate authority; opening it is read-only.
        state = _State(
            root_path,
            root_fd,
            root_stat,
            target,
            root_stat,
            b"",
            content,
            directories,
            {},
        )
        for path in (*directories, target):
            parts = PurePosixPath(path).parts
            limit = len(parts) if path in directories else len(parts) - 1
            for index in range(1, limit + 1):
                ancestor = "/".join(parts[:index])
                if ancestor in state.pins:
                    continue
                try:
                    fd = _directory_fd(state, ancestor)
                except FileNotFoundError:
                    if ancestor not in directories or (
                        path in directories
                        and directories.index(ancestor) > directories.index(path)
                    ):
                        raise RetainedPhysicalMutationRefusal(
                            "missing_ancestor_not_explicit"
                        ) from None
                    state.pins[ancestor] = None
                else:
                    try:
                        observed = os.fstat(fd)
                        if observed.st_dev != root_stat.st_dev:
                            raise RetainedPhysicalMutationRefusal(
                                "mount_boundary_unavailable"
                            )
                        state.pins[ancestor] = observed
                    finally:
                        os.close(fd)
        parent = _directory_fd(state, str(PurePosixPath(target).parent))
        try:
            current = _read_current(
                parent_descriptor=parent,
                leaf=PurePosixPath(target).name,
                maximum_bytes=DEFAULT_CONFINED_MUTATION_MAX_BYTES,
            )
        finally:
            os.close(parent)
        if isinstance(current, str) or current[0] is None or current[1] is None:
            raise RetainedPhysicalMutationRefusal("manifest_original_unavailable")
        body, original = current
        assert body is not None and original is not None
        state.before, state.original = body, original
        if state.original.st_nlink != 1 or state.original.st_dev != root_stat.st_dev:
            raise RetainedPhysicalMutationRefusal("manifest_alias_or_mount_unavailable")
        if _content_digest(state.before) != expected_content_digest:
            raise RetainedPhysicalMutationRefusal("manifest_preimage_mismatch")
        _verify(state)
        handle = object.__new__(RetainedPhysicalMutation)
        _HANDLES[handle] = state
        finalize(handle, _abandon, state)
        return handle
    except BaseException:
        os.close(root_fd)
        raise


def _issued(handle: RetainedPhysicalMutation) -> _State:
    state = _HANDLES.get(handle) if type(handle) is RetainedPhysicalMutation else None
    if state is None:
        raise RetainedPhysicalMutationRefusal("physical_handle_not_issued")
    if state.pid != os.getpid():
        _abandon(state)
        raise RetainedPhysicalMutationRefusal(
            "physical_handle_foreign_process", state.effects
        )
    return state


def _identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _directory_fd(state: _RetainedDirectoryState, path: str) -> int:
    if state.root_fd is None:
        raise RetainedPhysicalMutationRefusal("physical_handle_released")
    descriptor = os.dup(state.root_fd)
    try:
        if path != ".":
            for part in PurePosixPath(path).parts:
                next_fd = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_fd
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _verify(state: _State) -> None:
    if state.root_fd is None or _identity(
        os.stat(state.root, follow_symlinks=False)
    ) != _identity(state.root_stat):
        raise RetainedPhysicalMutationRefusal("root_identity_changed")
    for path, expected in state.pins.items():
        try:
            fd = _directory_fd(state, path)
        except FileNotFoundError:
            if expected is not None:
                raise RetainedPhysicalMutationRefusal(
                    "directory_identity_changed"
                ) from None
        else:
            try:
                current = os.fstat(fd)
                if (
                    expected is None
                    or _identity(current) != _identity(expected)
                    or current.st_mode != expected.st_mode
                ):
                    raise RetainedPhysicalMutationRefusal("directory_identity_changed")
            finally:
                os.close(fd)
    parent = _directory_fd(state, str(PurePosixPath(state.target).parent))
    try:
        current = _read_current(
            parent_descriptor=parent,
            leaf=PurePosixPath(state.target).name,
            maximum_bytes=DEFAULT_CONFINED_MUTATION_MAX_BYTES,
        )
    finally:
        os.close(parent)
    expected = state.original if state.replacement is None else state.replacement
    body = state.before if state.replacement is None else state.candidate
    # Replacement changes ctime; bind actual writer-created inode, mode and
    # exact bytes instead of accepting arbitrary equal-byte substitution.
    if isinstance(current, str) or current[0] != body or current[1] is None:
        raise RetainedPhysicalMutationRefusal("manifest_identity_or_bytes_changed")
    observed = current[1]
    if state.replacement is None or state.replacement_verified:
        matches = _same_stat(observed, expected)
    else:
        matches = (
            _identity(observed) == _identity(expected)
            and observed.st_mode == expected.st_mode
        )
    if not matches or observed.st_nlink != 1:
        raise RetainedPhysicalMutationRefusal("manifest_identity_or_bytes_changed")
    if state.replacement is not None and not state.replacement_verified:
        state.replacement = observed
        state.replacement_verified = True


def _check_or_retire(state: _State) -> None:
    if state.phase in {"retired", "consumed"}:
        raise RetainedPhysicalMutationRefusal(
            "physical_handle_terminal", state.effects, state.residual_scratch_paths
        )
    try:
        _verify(state)
    except BaseException as error:  # noqa: BLE001 - interruption must also terminally retire authority
        _refuse(
            state, getattr(error, "code", "physical_currentness_unavailable"), error
        )


def _release_root(state: _RetainedDirectoryState) -> None:
    descriptor = state.root_fd
    state.root_fd = None
    if descriptor is not None:
        _close_or_retire(state, descriptor)


def _close_or_retire(state: _RetainedDirectoryState, descriptor: int) -> None:
    try:
        os.close(descriptor)
    except BaseException as error:  # noqa: BLE001 - interrupted release is not completion
        _refuse(state, "descriptor_cleanup_failed", error)


def _abandon(state: _RetainedDirectoryState) -> None:
    if state.root_fd is not None:
        descriptor, state.root_fd = state.root_fd, None
        state.phase = "retired"
        try:
            os.close(descriptor)
        except OSError:
            pass


def _refuse(
    state: _RetainedDirectoryState, code: str, cause: BaseException | None = None
) -> NoReturn:
    state.phase = "retired"
    _release_root(state)
    raise RetainedPhysicalMutationRefusal(
        code, state.effects, state.residual_scratch_paths
    ) from cause


def _prepare_directory(
    state: _RetainedDirectoryState, path: str
) -> RetainedPhysicalEffect:
    """Original explicit-directory algorithm, shared by both retained writers.

    The enclosing owner validates currentness before and after this effect.
    This private mechanism never creates an unlisted parent or supplies authority.
    """
    parent = None
    effect = RetainedPhysicalEffect(path, "directory", ConfinedMutationEffectState.NONE)
    try:
        if state.pins[path] is None:
            parent = _directory_fd(state, str(PurePosixPath(path).parent))
            effect = RetainedPhysicalEffect(
                path, "directory", ConfinedMutationEffectState.UNKNOWN
            )
            try:
                os.mkdir(PurePosixPath(path).name, mode=0o700, dir_fd=parent)
            except FileExistsError:
                effect = RetainedPhysicalEffect(
                    path, "directory", ConfinedMutationEffectState.NONE
                )
                raise
            effect = RetainedPhysicalEffect(
                path, "directory", ConfinedMutationEffectState.APPLIED
            )
            observed = os.stat(
                PurePosixPath(path).name, dir_fd=parent, follow_symlinks=False
            )
            effect = RetainedPhysicalEffect(
                path,
                "directory",
                ConfinedMutationEffectState.APPLIED,
                mode=stat.S_IMODE(observed.st_mode),
                after_identity=_identity(observed),
            )
            if (
                not stat.S_ISDIR(observed.st_mode)
                or stat.S_IMODE(observed.st_mode) != 0o700
            ):
                raise RetainedPhysicalMutationRefusal(
                    "directory_private_mode_unavailable"
                )
            state.pins[path] = observed
            effect = RetainedPhysicalEffect(
                path,
                "directory",
                ConfinedMutationEffectState.APPLIED,
                mode=0o700,
                after_identity=_identity(observed),
            )
            os.fsync(parent)
            effect = RetainedPhysicalEffect(
                path,
                "directory",
                ConfinedMutationEffectState.APPLIED,
                True,
                0o700,
                after_identity=_identity(observed),
            )
        else:
            existing = state.pins[path]
            assert existing is not None
            effect = RetainedPhysicalEffect(
                path,
                "directory",
                ConfinedMutationEffectState.NONE,
                mode=stat.S_IMODE(existing.st_mode),
            )
        state.effects.append(effect)
        return effect
    except BaseException as error:  # noqa: BLE001 - interruption retains effects
        if not state.effects or state.effects[-1] is not effect:
            state.effects.append(effect)
        _refuse(state, getattr(error, "code", "directory_preparation_failed"), error)
    finally:
        if parent is not None:
            _close_or_retire(state, parent)
