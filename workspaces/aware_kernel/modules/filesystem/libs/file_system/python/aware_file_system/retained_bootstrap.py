"""Single-use absent-file creation under cooperative descriptor confinement.

This is a physical mechanism, not Issue or Protocol authorization. Original
directory traversal, temporary writes, readback and effect carriers are shared
with the existing FileSystem writers. Published bytes are never rolled back.
"""

from __future__ import annotations

import os
import stat
import threading
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import final
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
from .retained_mutation import (
    _DIRECTORY_FLAGS,
    RetainedPhysicalEffect,
    RetainedPhysicalMutationRefusal,
    _abandon,
    _close_or_retire,
    _directory_fd,
    _identity,
    _prepare_directory,
    _refuse,
    _release_root,
)


@dataclass(frozen=True, slots=True)
class BootstrapFileCreation:
    path: str
    content: bytes
    mode: int = 0o644

    def __post_init__(self) -> None:
        _ = _bootstrap_path(self.path)
        if (
            type(self.content) is not bytes
            or len(self.content) > DEFAULT_CONFINED_MUTATION_MAX_BYTES
        ):
            raise ValueError("Bootstrap content must be bounded exact bytes")
        if type(self.mode) is not int or self.mode != 0o644:
            raise ValueError("Bootstrap file mode must be 0644")


@dataclass
class _State:
    root: Path
    root_fd: int | None
    root_stat: os.stat_result
    files: tuple[BootstrapFileCreation, ...]
    directories: tuple[str, ...]
    pins: dict[str, os.stat_result | None]
    pid: int = field(default_factory=os.getpid)
    phase: str = "issued"
    next_directory: int = 0
    next_file: int = 0
    created: dict[str, os.stat_result] = field(default_factory=dict)
    effects: list[RetainedPhysicalEffect] = field(default_factory=list)
    residual_scratch_paths: list[str] = field(default_factory=list)
    lock: threading.RLock = field(default_factory=threading.RLock)


_HANDLES: WeakKeyDictionary[RetainedBootstrapCreation, _State] = WeakKeyDictionary()


@final
class RetainedBootstrapCreation:
    """Owner-issued process-local handle; detached evidence cannot mint one."""

    # CPython initializes the weakref slot; construction is intentionally owner-only.
    __slots__: tuple[str, ...] = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("Use retain_confined_bootstrap_creation")

    def __copy__(self):
        raise TypeError("Retained bootstrap creation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Retained bootstrap creation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Retained bootstrap creation cannot be serialized")

    @property
    def phase(self) -> str:
        return _issued(self).phase

    def observe_effects(self) -> tuple[RetainedPhysicalEffect, ...]:
        state = _issued(self)
        with state.lock:
            return tuple(state.effects)

    def validate_current(self) -> None:
        state = _issued(self)
        with state.lock:
            _check(state)

    def prepare_next_directory(self) -> RetainedPhysicalEffect:
        state = _issued(self)
        with state.lock:
            _check(state)
            if state.phase not in {
                "issued",
                "preparing",
            } or state.next_directory >= len(state.directories):
                _refuse(state, "directory_transition_invalid")
            state.phase = "preparing"
            effect = _prepare_directory(state, state.directories[state.next_directory])
            state.next_directory += 1
            _check(state)
            return effect

    def create_next_file(self) -> RetainedPhysicalEffect:
        state = _issued(self)
        with state.lock:
            _check(state)
            if state.next_directory != len(state.directories) or state.next_file >= len(
                state.files
            ):
                _refuse(state, "creation_transition_invalid")
            candidate = state.files[state.next_file]
            parent = None
            scratch = f".aware-cas-{os.getpid()}-{uuid4().hex}"
            scratch_path = str(PurePosixPath(candidate.path).parent / scratch)
            scratch_identity = None
            cleanup_attempted = False
            effect = RetainedPhysicalEffect(
                candidate.path, "file", ConfinedMutationEffectState.NONE
            )
            state.phase = "creating"
            try:
                parent = _directory_fd(state, str(PurePosixPath(candidate.path).parent))
                _write_temporary(
                    parent_descriptor=parent,
                    name=scratch,
                    content=candidate.content,
                    mode=candidate.mode,
                    preserve_mode=True,
                )
                scratch_stat = os.stat(scratch, dir_fd=parent, follow_symlinks=False)
                scratch_identity = _identity(scratch_stat)
                _check(state)
                effect = RetainedPhysicalEffect(
                    candidate.path, "file", ConfinedMutationEffectState.UNKNOWN
                )
                try:
                    os.link(
                        scratch,
                        PurePosixPath(candidate.path).name,
                        src_dir_fd=parent,
                        dst_dir_fd=parent,
                        follow_symlinks=False,
                    )
                except FileExistsError:
                    effect = RetainedPhysicalEffect(
                        candidate.path, "file", ConfinedMutationEffectState.NONE
                    )
                    raise
                effect = RetainedPhysicalEffect(
                    candidate.path,
                    "file",
                    ConfinedMutationEffectState.APPLIED,
                    mode=candidate.mode,
                    after_digest=_content_digest(candidate.content),
                    after_identity=scratch_identity,
                )
                cleanup_attempted = True
                _dispose_scratch(state, parent, scratch, scratch_path, scratch_identity)
                scratch = ""
                current = _read_current(
                    parent_descriptor=parent,
                    leaf=PurePosixPath(candidate.path).name,
                    maximum_bytes=DEFAULT_CONFINED_MUTATION_MAX_BYTES,
                )
                if (
                    isinstance(current, str)
                    or current[0] != candidate.content
                    or current[1] is None
                ):
                    raise RetainedPhysicalMutationRefusal(
                        "created_file_readback_failed"
                    )
                observed = current[1]
                if (
                    _identity(observed) != scratch_identity
                    or observed.st_nlink != 1
                    or stat.S_IMODE(observed.st_mode) != candidate.mode
                ):
                    raise RetainedPhysicalMutationRefusal(
                        "created_file_identity_changed"
                    )
                state.created[candidate.path] = observed
                os.fsync(parent)
                effect = RetainedPhysicalEffect(
                    candidate.path,
                    "file",
                    ConfinedMutationEffectState.APPLIED,
                    True,
                    candidate.mode,
                    after_digest=_content_digest(candidate.content),
                    after_identity=scratch_identity,
                )
                state.effects.append(effect)
                state.next_file += 1
                _check(state)
                return effect
            except BaseException as error:  # noqa: BLE001 - effects survive interruptions
                if not state.effects or state.effects[-1] is not effect:
                    state.effects.append(effect)
                _refuse(state, getattr(error, "code", "file_creation_failed"), error)
            finally:
                try:
                    if parent is not None and scratch and not cleanup_attempted:
                        _dispose_scratch(
                            state, parent, scratch, scratch_path, scratch_identity
                        )
                finally:
                    if parent is not None:
                        _close_or_retire(state, parent)

    def finish(self) -> tuple[RetainedPhysicalEffect, ...]:
        state = _issued(self)
        with state.lock:
            _check(state)
            if state.next_file != len(state.files):
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


def retain_confined_bootstrap_creation(
    *,
    root: Path,
    files: tuple[BootstrapFileCreation, ...],
    directory_paths: tuple[str, ...],
    confinement_profile: ConfinedMutationProfile = ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
) -> RetainedBootstrapCreation:
    if type(confinement_profile) is not ConfinedMutationProfile:
        raise TypeError("Physical profile must be exact")
    if confinement_profile is not ConfinedMutationProfile.DESCRIPTOR_WALK_V1:
        raise RetainedPhysicalMutationRefusal("continuous_root_confinement_unavailable")
    if not all(
        hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    ):
        raise RetainedPhysicalMutationRefusal("descriptor_profile_unavailable")
    if (
        type(files) is not tuple
        or not 1 <= len(files) <= 3
        or any(type(item) is not BootstrapFileCreation for item in files)
    ):
        raise ValueError("Bootstrap requires one to three exact file values")
    # Detached data is validated again at issuance; it is never admission.
    files = tuple(
        BootstrapFileCreation(item.path, item.content, item.mode) for item in files
    )
    if type(directory_paths) is not tuple or len(directory_paths) > 64:
        raise ValueError("Explicit directory sequence must be a bounded tuple")
    directories = tuple(_bootstrap_path(path) for path in directory_paths)
    paths = (*directories, *(item.path for item in files))
    if len(set(paths)) != len(paths):
        raise ValueError("Effect paths must be distinct")
    root_path = root.expanduser().absolute()
    root_fd = None
    try:
        root_fd = os.open(root_path, _DIRECTORY_FLAGS)
        state = _State(root_path, root_fd, os.fstat(root_fd), files, directories, {})
        for path in paths:
            parts = PurePosixPath(path).parts
            limit = len(parts) if path in directories else len(parts) - 1
            for index in range(1, limit + 1):
                ancestor = "/".join(parts[:index])
                if ancestor in state.pins:
                    continue
                try:
                    descriptor = _directory_fd(state, ancestor)
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
                        observed = os.fstat(descriptor)
                        if observed.st_dev != state.root_stat.st_dev:
                            raise RetainedPhysicalMutationRefusal(
                                "mount_boundary_unavailable"
                            )
                        state.pins[ancestor] = observed
                    finally:
                        os.close(descriptor)
        _verify(state)
        handle = object.__new__(RetainedBootstrapCreation)
        _HANDLES[handle] = state
        _ = finalize(handle, _abandon, state)
        root_fd = None  # custody transferred to the genuine handle
        return handle
    except BaseException as error:
        if isinstance(error, RetainedPhysicalMutationRefusal):
            raise
        raise RetainedPhysicalMutationRefusal("bootstrap_source_unavailable") from error
    finally:
        if root_fd is not None:
            os.close(root_fd)


def _bootstrap_path(value: str) -> str:
    path = _relative_path(value)
    if ".git" in PurePosixPath(path).parts:
        raise ValueError("Bootstrap cannot write Git internals")
    return path


def _issued(handle: RetainedBootstrapCreation) -> _State:
    state = _HANDLES.get(handle) if type(handle) is RetainedBootstrapCreation else None
    if state is None:
        raise RetainedPhysicalMutationRefusal("bootstrap_handle_not_issued")
    if state.pid != os.getpid():
        _abandon(state)
        raise RetainedPhysicalMutationRefusal(
            "bootstrap_handle_foreign_process", state.effects
        )
    return state


def _check(state: _State) -> None:
    if state.phase in {"retired", "consumed"}:
        raise RetainedPhysicalMutationRefusal(
            "bootstrap_handle_terminal", state.effects, state.residual_scratch_paths
        )
    try:
        _verify(state)
    except BaseException as error:  # noqa: BLE001 - interruption retires authority
        _refuse(
            state, getattr(error, "code", "bootstrap_currentness_unavailable"), error
        )


def _verify(state: _State) -> None:
    if state.root_fd is None or _identity(
        os.stat(state.root, follow_symlinks=False)
    ) != _identity(state.root_stat):
        raise RetainedPhysicalMutationRefusal("root_identity_changed")
    for path, expected in state.pins.items():
        try:
            descriptor = _directory_fd(state, path)
        except FileNotFoundError:
            if expected is not None:
                raise RetainedPhysicalMutationRefusal(
                    "directory_identity_changed"
                ) from None
        else:
            try:
                observed = os.fstat(descriptor)
                if (
                    expected is None
                    or _identity(observed) != _identity(expected)
                    or observed.st_mode != expected.st_mode
                ):
                    raise RetainedPhysicalMutationRefusal("directory_identity_changed")
            finally:
                os.close(descriptor)
    for candidate in state.files:
        expected = state.created.get(candidate.path)
        try:
            parent = _directory_fd(state, str(PurePosixPath(candidate.path).parent))
        except FileNotFoundError:
            if expected is not None:
                raise RetainedPhysicalMutationRefusal(
                    "file_parent_identity_changed"
                ) from None
            continue
        try:
            if expected is None:
                try:
                    os.stat(
                        PurePosixPath(candidate.path).name,
                        dir_fd=parent,
                        follow_symlinks=False,
                    )
                except FileNotFoundError:
                    pass
                else:
                    raise RetainedPhysicalMutationRefusal("bootstrap_target_not_absent")
            else:
                current = _read_current(
                    parent_descriptor=parent,
                    leaf=PurePosixPath(candidate.path).name,
                    maximum_bytes=DEFAULT_CONFINED_MUTATION_MAX_BYTES,
                )
                if (
                    isinstance(current, str)
                    or current[0] != candidate.content
                    or current[1] is None
                    or not _same_stat(current[1], expected)
                    or current[1].st_nlink != 1
                ):
                    raise RetainedPhysicalMutationRefusal(
                        "created_file_identity_or_bytes_changed"
                    )
        finally:
            os.close(parent)


def _dispose_scratch(
    state: _State,
    parent: int,
    name: str,
    path: str,
    expected_identity: tuple[int, int] | None,
) -> None:
    try:
        observed = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return
    except BaseException as error:  # noqa: BLE001 - interrupted cleanup stays unknown
        if path not in state.residual_scratch_paths:
            state.residual_scratch_paths.append(path)
        _refuse(state, "scratch_cleanup_unverified", error)
    if expected_identity is None or _identity(observed) != expected_identity:
        if path not in state.residual_scratch_paths:
            state.residual_scratch_paths.append(path)
        _refuse(state, "scratch_cleanup_identity_unverified")
    try:
        os.unlink(name, dir_fd=parent)
    except BaseException as error:  # noqa: BLE001 - cleanup cannot upgrade interruption
        if path not in state.residual_scratch_paths:
            state.residual_scratch_paths.append(path)
        _refuse(state, "scratch_cleanup_failed", error)
