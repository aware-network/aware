"""Bounded Git reachability evidence under one live Workspace session."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import final

from .contracts import (
    ObservationRuntimeState,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSnapshot,
)
from .observation import WorkspaceRepositoryObservationSession

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_REF = re.compile(r"^[a-z][a-z0-9_.-]{0,63}:[A-Za-z0-9][A-Za-z0-9._:/-]{0,447}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_MAX_REVISIONS = 64
_MAX_REFS = 512
_ZERO_DIGEST = "sha256:" + ("0" * 64)


class WorkspaceRepositoryReachabilityPosture(StrEnum):
    COMPLETE = "complete"
    BLOCKED = "blocked"


class WorkspaceRepositoryReachabilityAuthorityGrade(StrEnum):
    PORTABLE_INPUT = "portable_input"


class WorkspaceRepositoryRevisionPosture(StrEnum):
    REACHABLE = "reachable"
    NOT_REACHABLE = "not_reachable"


class WorkspaceRepositoryReachabilityError(RuntimeError):
    """The request cannot produce consistent portable reachability evidence."""


@final
@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryReachabilityRequest:
    request_ref: str
    revision_refs: tuple[str, ...]

    SCHEMA = "aware.workspace.repository-reachability-request.v1"

    def __post_init__(self) -> None:
        _ref(self.request_ref)
        if (
            type(self.revision_refs) is not tuple
            or not 1 <= len(self.revision_refs) <= _MAX_REVISIONS
            or any(
                type(value) is not str or _COMMIT.fullmatch(value) is None
                for value in self.revision_refs
            )
            or self.revision_refs != tuple(sorted(set(self.revision_refs)))
        ):
            raise ValueError("repository_reachability_revisions_invalid")

    def to_payload(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "schema": self.SCHEMA,
            "request_ref": self.request_ref,
            "revision_refs": list(self.revision_refs),
        }


@final
@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryRevisionReachability:
    revision_ref: str
    posture: WorkspaceRepositoryRevisionPosture
    object_type: str | None
    object_size: int | None
    retaining_ref_names: tuple[str, ...]
    evidence_digest: str

    SCHEMA = "aware.workspace.repository-revision-reachability.v1"

    def __post_init__(self) -> None:
        if (
            type(self.revision_ref) is not str
            or _COMMIT.fullmatch(self.revision_ref) is None
        ):
            raise ValueError("repository_reachability_revision_invalid")
        if type(self.posture) is not WorkspaceRepositoryRevisionPosture:
            raise TypeError("repository_reachability_posture_invalid")
        if self.posture is WorkspaceRepositoryRevisionPosture.REACHABLE:
            if (
                self.object_type != "commit"
                or type(self.object_size) is not int
                or self.object_size < 0
            ):
                raise ValueError("repository_reachability_object_invalid")
            if not self.retaining_ref_names:
                raise ValueError("repository_reachability_membership_missing")
        elif (
            self.object_type is not None
            or self.object_size is not None
            or self.retaining_ref_names
        ):
            raise ValueError("repository_nonmembership_evidence_invalid")
        if (
            type(self.retaining_ref_names) is not tuple
            or self.retaining_ref_names != tuple(sorted(set(self.retaining_ref_names)))
            or any(
                type(value) is not str or not value
                for value in self.retaining_ref_names
            )
        ):
            raise ValueError("repository_reachability_retaining_refs_invalid")
        _digest(self.evidence_digest)
        if self.evidence_digest != _digest_payload(_entry_evidence_payload(self)):
            raise ValueError("repository_reachability_evidence_digest_invalid")

    def to_payload(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "schema": self.SCHEMA,
            "revision_ref": self.revision_ref,
            "posture": self.posture.value,
            "object_type": self.object_type,
            "object_size": self.object_size,
            "retaining_ref_names": list(self.retaining_ref_names),
            "evidence_digest": self.evidence_digest,
        }


@final
@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryReachabilityCounters:
    repository_identity_reads: int
    ref_snapshot_reads: int
    object_identity_reads: int
    ancestry_reads: int
    workspace_currentness_reads: int
    repository_writes: int = 0
    workspace_writes: int = 0

    SCHEMA = "aware.workspace.repository-reachability-counters.v1"

    def __post_init__(self) -> None:
        values = (
            self.repository_identity_reads,
            self.ref_snapshot_reads,
            self.object_identity_reads,
            self.ancestry_reads,
            self.workspace_currentness_reads,
            self.repository_writes,
            self.workspace_writes,
        )
        if any(type(value) is not int or value < 0 for value in values):
            raise ValueError("repository_reachability_counters_invalid")
        if self.repository_writes or self.workspace_writes:
            raise ValueError("repository_reachability_effect_counter_nonzero")

    def to_payload(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "schema": self.SCHEMA,
            "repository_identity_reads": self.repository_identity_reads,
            "ref_snapshot_reads": self.ref_snapshot_reads,
            "object_identity_reads": self.object_identity_reads,
            "ancestry_reads": self.ancestry_reads,
            "workspace_currentness_reads": self.workspace_currentness_reads,
            "repository_writes": self.repository_writes,
            "workspace_writes": self.workspace_writes,
        }


@final
@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceRepositoryReachabilityResult:
    request: WorkspaceRepositoryReachabilityRequest
    binding_key: str
    workspace_epoch: str
    workspace_cursor: int
    workspace_snapshot_digest: str
    git_common_directory_digest: str
    ref_set_digest: str
    authority_grade: WorkspaceRepositoryReachabilityAuthorityGrade
    posture: WorkspaceRepositoryReachabilityPosture
    entries: tuple[WorkspaceRepositoryRevisionReachability, ...]
    blocker_codes: tuple[str, ...]
    counters: WorkspaceRepositoryReachabilityCounters
    result_digest: str

    SCHEMA = "aware.workspace.repository-reachability-result.v1"

    def __post_init__(self) -> None:
        if type(self.request) is not WorkspaceRepositoryReachabilityRequest:
            raise TypeError("repository_reachability_request_not_exact")
        _ref(self.binding_key)
        if type(self.workspace_epoch) is not str or not self.workspace_epoch:
            raise ValueError("repository_reachability_epoch_invalid")
        if type(self.workspace_cursor) is not int or self.workspace_cursor < 0:
            raise ValueError("repository_reachability_cursor_invalid")
        for value in (
            self.workspace_snapshot_digest,
            self.git_common_directory_digest,
            self.ref_set_digest,
            self.result_digest,
        ):
            _digest(value)
        if type(self.posture) is not WorkspaceRepositoryReachabilityPosture:
            raise TypeError("repository_reachability_result_posture_invalid")
        if (
            type(self.authority_grade)
            is not WorkspaceRepositoryReachabilityAuthorityGrade
            or self.authority_grade
            is not WorkspaceRepositoryReachabilityAuthorityGrade.PORTABLE_INPUT
        ):
            raise TypeError("repository_reachability_authority_grade_invalid")
        if (
            type(self.entries) is not tuple
            or any(
                type(item) is not WorkspaceRepositoryRevisionReachability
                for item in self.entries
            )
            or type(self.blocker_codes) is not tuple
            or self.blocker_codes != tuple(sorted(set(self.blocker_codes)))
            or any(type(value) is not str or not value for value in self.blocker_codes)
            or type(self.counters) is not WorkspaceRepositoryReachabilityCounters
        ):
            raise ValueError("repository_reachability_result_invalid")
        if self.posture is WorkspaceRepositoryReachabilityPosture.COMPLETE:
            if (
                tuple(item.revision_ref for item in self.entries)
                != self.request.revision_refs
                or self.blocker_codes
            ):
                raise ValueError("repository_reachability_complete_invalid")
        elif self.entries or not self.blocker_codes:
            raise ValueError("repository_reachability_blocked_invalid")
        if self.result_digest != _result_digest(self):
            raise ValueError("repository_reachability_result_digest_invalid")

    def to_payload(self) -> dict[str, object]:
        self.__post_init__()
        return _result_payload(self, include_digest=True)

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_payload())


@dataclass(frozen=True, slots=True)
class _RepositorySnapshot:
    git_directory: str
    git_common_directory: str
    git_directory_device: int
    git_directory_inode: int
    common_directory_device: int
    common_directory_inode: int
    refs: tuple[tuple[str, str, str | None], ...]
    ref_set_digest: str
    common_directory_digest: str


@dataclass(slots=True)
class _ReadCounters:
    repository_identity_reads: int = 0
    ref_snapshot_reads: int = 0
    object_identity_reads: int = 0
    ancestry_reads: int = 0

    def freeze(
        self, *, workspace_currentness_reads: int
    ) -> WorkspaceRepositoryReachabilityCounters:
        return WorkspaceRepositoryReachabilityCounters(
            self.repository_identity_reads,
            self.ref_snapshot_reads,
            self.object_identity_reads,
            self.ancestry_reads,
            workspace_currentness_reads,
        )


@final
class WorkspaceRepositoryReachabilityReader:
    """Produce portable evidence from one maintained Workspace session."""

    def __init__(self, session: WorkspaceRepositoryObservationSession) -> None:
        if (
            type(session) is not WorkspaceRepositoryObservationSession
            or type(session.binding) is not WorkspaceRepositoryBinding
        ):
            raise TypeError("repository_reachability_session_not_exact")
        self._session = session
        self._binding = session.binding
        self._binding_snapshot = _binding_snapshot(self._binding)
        self._lock = asyncio.Lock()
        self._request: WorkspaceRepositoryReachabilityRequest | None = None
        self._workspace_coordinate_snapshot: (
            tuple[
                WorkspaceRepositoryBinding,
                str,
                WorkspaceRepositoryObservationSnapshot,
            ]
            | None
        ) = None
        self._repository_snapshot: _RepositorySnapshot | None = None
        self._entry_snapshots: tuple[bytes, ...] | None = None
        self._closed = False

    async def observe(
        self, request: WorkspaceRepositoryReachabilityRequest
    ) -> WorkspaceRepositoryReachabilityResult:
        if type(request) is not WorkspaceRepositoryReachabilityRequest:
            raise TypeError("repository_reachability_request_not_exact")
        async with self._lock:
            if self._closed:
                raise WorkspaceRepositoryReachabilityError(
                    "repository_reachability_reader_closed"
                )
            if self._request is not None and request != self._request:
                raise WorkspaceRepositoryReachabilityError(
                    "repository_reachability_invocation_mismatch"
                )
            before = self._workspace_coordinate()
            if (
                self._workspace_coordinate_snapshot is not None
                and not _same_workspace_coordinate(
                    before, self._workspace_coordinate_snapshot
                )
            ):
                raise WorkspaceRepositoryReachabilityError(
                    "repository_reachability_workspace_moved"
                )
            try:
                repository, entries, counters = await asyncio.to_thread(
                    _observe_repository,
                    self._binding.root_path,
                    request.revision_refs,
                )
                after = self._workspace_coordinate()
                if not _same_workspace_coordinate(before, after):
                    raise WorkspaceRepositoryReachabilityError(
                        "repository_reachability_workspace_moved"
                    )
                if (
                    self._workspace_coordinate_snapshot is not None
                    and not _same_workspace_coordinate(
                        after, self._workspace_coordinate_snapshot
                    )
                ):
                    raise WorkspaceRepositoryReachabilityError(
                        "repository_reachability_workspace_moved"
                    )
                result = _complete_result(
                    request=request,
                    binding=self._binding,
                    workspace=before,
                    repository=repository,
                    entries=entries,
                    counters=counters.freeze(workspace_currentness_reads=2),
                )
            except _RepositoryBlocked as blocked:
                return _blocked_result(
                    request=request,
                    binding=self._binding,
                    workspace=before,
                    blocker_code=blocked.code,
                    counters=blocked.counters.freeze(workspace_currentness_reads=1),
                )
            entry_snapshots = tuple(
                _canonical_bytes(entry.to_payload()) for entry in result.entries
            )
            if self._request is not None and (
                repository != self._repository_snapshot
                or entry_snapshots != self._entry_snapshots
            ):
                return _blocked_result(
                    request=request,
                    binding=self._binding,
                    workspace=after,
                    blocker_code="repository_reachability_evidence_moved",
                    counters=counters.freeze(workspace_currentness_reads=2),
                )
            self._request = request
            self._workspace_coordinate_snapshot = before
            self._repository_snapshot = repository
            self._entry_snapshots = entry_snapshots
            return result

    def close(self) -> None:
        self._closed = True
        self._request = None
        self._workspace_coordinate_snapshot = None
        self._repository_snapshot = None
        self._entry_snapshots = None

    def _workspace_coordinate(
        self,
    ) -> tuple[WorkspaceRepositoryBinding, str, WorkspaceRepositoryObservationSnapshot]:
        session = self._session
        if (
            type(session) is not WorkspaceRepositoryObservationSession
            or session is not self._session
            or session.binding is not self._binding
            or _binding_snapshot(session.binding) != self._binding_snapshot
            or not session.authority_admitted
            or session.health.state
            not in {ObservationRuntimeState.RUNNING, ObservationRuntimeState.DEGRADED}
        ):
            raise WorkspaceRepositoryReachabilityError(
                "repository_reachability_workspace_unavailable"
            )
        snapshot = session.current_snapshot
        return self._binding, session.epoch, snapshot


class _RepositoryBlocked(RuntimeError):
    def __init__(self, code: str, counters: _ReadCounters) -> None:
        super().__init__(code)
        self.code = code
        self.counters = counters


def _observe_repository(
    root: Path, revisions: tuple[str, ...]
) -> tuple[
    _RepositorySnapshot,
    tuple[WorkspaceRepositoryRevisionReachability, ...],
    _ReadCounters,
]:
    counters = _ReadCounters()
    try:
        before = _repository_snapshot(root, counters)
        entries: list[WorkspaceRepositoryRevisionReachability] = []
        commit_refs = _commit_refs(root, before.refs, counters)
        for revision in revisions:
            identity = _object_identity(root, revision)
            counters.object_identity_reads += 1
            retaining: list[str] = []
            object_size: int | None = None
            if identity is not None:
                object_type, object_size = identity
                if object_type != "commit":
                    raise _RepositoryBlocked(
                        "repository_revision_object_invalid", counters
                    )
                for ref_name, tip in commit_refs:
                    status = _read_ancestry_status(root, revision, tip)
                    counters.ancestry_reads += 1
                    if status == 0:
                        retaining.append(ref_name)
                    elif status != 1:
                        raise _RepositoryBlocked(
                            "repository_reachability_ancestry_unavailable", counters
                        )
            posture = (
                WorkspaceRepositoryRevisionPosture.REACHABLE
                if retaining
                else WorkspaceRepositoryRevisionPosture.NOT_REACHABLE
            )
            entry = object.__new__(WorkspaceRepositoryRevisionReachability)
            for key, item in {
                "revision_ref": revision,
                "posture": posture,
                "object_type": "commit" if retaining else None,
                "object_size": object_size if retaining else None,
                "retaining_ref_names": tuple(sorted(retaining)),
            }.items():
                object.__setattr__(entry, key, item)
            object.__setattr__(
                entry,
                "evidence_digest",
                _digest_payload(_entry_evidence_payload(entry)),
            )
            entry.__post_init__()
            entries.append(entry)
        after = _repository_snapshot(root, counters)
        if before != after:
            raise _RepositoryBlocked(
                "repository_reachability_repository_moved", counters
            )
        return before, tuple(entries), counters
    except _RepositoryBlocked:
        raise
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as error:
        raise _RepositoryBlocked(
            "repository_reachability_read_unavailable", counters
        ) from error


def _commit_refs(
    root: Path,
    refs: tuple[tuple[str, str, str | None], ...],
    counters: _ReadCounters,
) -> tuple[tuple[str, str], ...]:
    commit_refs: list[tuple[str, str]] = []
    for ref_name, target, peeled in refs:
        tip = peeled if peeled is not None else target
        identity = _object_identity(root, tip)
        counters.object_identity_reads += 1
        if identity is None:
            raise _RepositoryBlocked("repository_ref_object_missing", counters)
        status, commit = _read_commit_peel(root, tip)
        counters.object_identity_reads += 1
        if status == 0:
            if _COMMIT.fullmatch(commit) is None:
                raise _RepositoryBlocked("repository_ref_commit_invalid", counters)
            commit_refs.append((ref_name, commit))
        elif status == 128:
            continue
        else:
            raise _RepositoryBlocked("repository_ref_commit_unavailable", counters)
    if not commit_refs:
        raise _RepositoryBlocked("repository_commit_ref_set_unavailable", counters)
    return tuple(sorted(set(commit_refs)))


def _repository_snapshot(root: Path, counters: _ReadCounters) -> _RepositorySnapshot:
    git_dir = _resolve_git_path(root, _read_absolute_git_directory(root))
    common_dir = _resolve_git_path(root, _read_git_common_directory(root))
    counters.repository_identity_reads += 2
    git_metadata = git_dir.stat()
    common_metadata = common_dir.stat()
    counters.repository_identity_reads += 2
    if (
        not stat.S_ISDIR(git_metadata.st_mode)
        or not stat.S_ISDIR(common_metadata.st_mode)
        or git_dir.is_symlink()
        or common_dir.is_symlink()
    ):
        raise _RepositoryBlocked("repository_git_identity_invalid", counters)
    if _read_shallow_posture(root) != "false":
        raise _RepositoryBlocked("repository_shallow_boundary_ambiguous", counters)
    counters.repository_identity_reads += 1
    for path, code in (
        (
            common_dir / "objects" / "info" / "alternates",
            "repository_alternates_present",
        ),
        (common_dir / "info" / "grafts", "repository_grafts_present"),
    ):
        counters.repository_identity_reads += 1
        if path.exists() or path.is_symlink():
            raise _RepositoryBlocked(code, counters)
    encoded_refs = _read_ref_snapshot(root)
    counters.ref_snapshot_reads += 1
    refs: list[tuple[str, str, str | None]] = []
    for line in encoded_refs.splitlines():
        fields = line.split("\0")
        if len(fields) != 3 or not fields[0] or _COMMIT.fullmatch(fields[1]) is None:
            raise _RepositoryBlocked("repository_ref_snapshot_invalid", counters)
        peeled = fields[2] or None
        if peeled is not None and _COMMIT.fullmatch(peeled) is None:
            raise _RepositoryBlocked("repository_ref_snapshot_invalid", counters)
        if fields[0].startswith("refs/replace/"):
            raise _RepositoryBlocked("repository_replace_refs_present", counters)
        refs.append((fields[0], fields[1], peeled))
    head_status, head = _read_head(root)
    counters.ref_snapshot_reads += 1
    if head_status == 0:
        if _COMMIT.fullmatch(head) is None:
            raise _RepositoryBlocked("repository_head_invalid", counters)
        refs.append(("HEAD", head, None))
    elif head_status != 1:
        raise _RepositoryBlocked("repository_head_unavailable", counters)
    refs_tuple = tuple(sorted(set(refs)))
    if not refs_tuple or len(refs_tuple) > _MAX_REFS:
        raise _RepositoryBlocked("repository_ref_set_unavailable", counters)
    ref_set_digest = _digest_payload(
        {"schema": "aware.workspace.repository-ref-set.v1", "refs": refs_tuple}
    )
    common_digest = _digest_payload(
        {
            "schema": "aware.workspace.git-common-directory-identity.v1",
            "git_directory": str(git_dir),
            "git_directory_device": git_metadata.st_dev,
            "git_directory_inode": git_metadata.st_ino,
            "common_directory": str(common_dir),
            "common_directory_device": common_metadata.st_dev,
            "common_directory_inode": common_metadata.st_ino,
        }
    )
    return _RepositorySnapshot(
        str(git_dir),
        str(common_dir),
        git_metadata.st_dev,
        git_metadata.st_ino,
        common_metadata.st_dev,
        common_metadata.st_ino,
        refs_tuple,
        ref_set_digest,
        common_digest,
    )


def _complete_result(
    *,
    request: WorkspaceRepositoryReachabilityRequest,
    binding: WorkspaceRepositoryBinding,
    workspace: tuple[
        WorkspaceRepositoryBinding, str, WorkspaceRepositoryObservationSnapshot
    ],
    repository: _RepositorySnapshot,
    entries: tuple[WorkspaceRepositoryRevisionReachability, ...],
    counters: WorkspaceRepositoryReachabilityCounters,
) -> WorkspaceRepositoryReachabilityResult:
    _, epoch, snapshot = workspace
    value = object.__new__(WorkspaceRepositoryReachabilityResult)
    values = {
        "request": request,
        "binding_key": str(binding.binding_key),
        "workspace_epoch": epoch,
        "workspace_cursor": snapshot.cursor,
        "workspace_snapshot_digest": snapshot.snapshot_digest,
        "git_common_directory_digest": repository.common_directory_digest,
        "ref_set_digest": repository.ref_set_digest,
        "authority_grade": WorkspaceRepositoryReachabilityAuthorityGrade.PORTABLE_INPUT,
        "posture": WorkspaceRepositoryReachabilityPosture.COMPLETE,
        "entries": entries,
        "blocker_codes": (),
        "counters": counters,
    }
    for key, item in values.items():
        object.__setattr__(value, key, item)
    object.__setattr__(value, "result_digest", _result_digest(value))
    value.__post_init__()
    return value


def _blocked_result(
    *,
    request: WorkspaceRepositoryReachabilityRequest,
    binding: WorkspaceRepositoryBinding,
    workspace: tuple[
        WorkspaceRepositoryBinding, str, WorkspaceRepositoryObservationSnapshot
    ],
    blocker_code: str,
    counters: WorkspaceRepositoryReachabilityCounters,
) -> WorkspaceRepositoryReachabilityResult:
    _, epoch, snapshot = workspace
    value = object.__new__(WorkspaceRepositoryReachabilityResult)
    values = {
        "request": request,
        "binding_key": str(binding.binding_key),
        "workspace_epoch": epoch,
        "workspace_cursor": snapshot.cursor,
        "workspace_snapshot_digest": snapshot.snapshot_digest,
        "git_common_directory_digest": _ZERO_DIGEST,
        "ref_set_digest": _ZERO_DIGEST,
        "authority_grade": WorkspaceRepositoryReachabilityAuthorityGrade.PORTABLE_INPUT,
        "posture": WorkspaceRepositoryReachabilityPosture.BLOCKED,
        "entries": (),
        "blocker_codes": (blocker_code,),
        "counters": counters,
    }
    for key, item in values.items():
        object.__setattr__(value, key, item)
    object.__setattr__(value, "result_digest", _result_digest(value))
    value.__post_init__()
    return value


def _result_payload(
    result: WorkspaceRepositoryReachabilityResult, *, include_digest: bool
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": result.SCHEMA,
        "request": result.request.to_payload(),
        "binding_key": result.binding_key,
        "workspace_epoch": result.workspace_epoch,
        "workspace_cursor": result.workspace_cursor,
        "workspace_snapshot_digest": result.workspace_snapshot_digest,
        "git_common_directory_digest": result.git_common_directory_digest,
        "ref_set_digest": result.ref_set_digest,
        "authority_grade": result.authority_grade.value,
        "posture": result.posture.value,
        "entries": [entry.to_payload() for entry in result.entries],
        "blocker_codes": list(result.blocker_codes),
        "counters": result.counters.to_payload(),
    }
    if include_digest:
        payload["result_digest"] = result.result_digest
    return payload


def _result_digest(result: WorkspaceRepositoryReachabilityResult) -> str:
    return _digest_payload(_result_payload(result, include_digest=False))


def _same_workspace_coordinate(
    left: tuple[
        WorkspaceRepositoryBinding, str, WorkspaceRepositoryObservationSnapshot
    ],
    right: tuple[
        WorkspaceRepositoryBinding, str, WorkspaceRepositoryObservationSnapshot
    ],
) -> bool:
    return left[0] is right[0] and left[1] == right[1] and left[2] is right[2]


def _binding_snapshot(binding: WorkspaceRepositoryBinding) -> tuple[Path, str, str]:
    return binding.root_path, str(binding.binding_key), binding.filter_version


def _entry_evidence_payload(
    entry: WorkspaceRepositoryRevisionReachability,
) -> dict[str, object]:
    return {
        "schema": entry.SCHEMA,
        "revision_ref": entry.revision_ref,
        "posture": entry.posture.value,
        "object_type": entry.object_type,
        "object_size": entry.object_size,
        "retaining_ref_names": list(entry.retaining_ref_names),
    }


def _git_environment() -> dict[str, str]:
    return {
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
    }


def _read_absolute_git_directory(root: Path) -> str:
    completed = subprocess.run(
        ("/usr/bin/git", "-C", str(root), "rev-parse", "--absolute-git-dir"),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_git_environment(),
        timeout=10,
    )
    if completed.returncode != 0:
        raise OSError("repository_absolute_git_directory_read_failed")
    return completed.stdout.decode("utf-8").rstrip("\n")


def _read_git_common_directory(root: Path) -> str:
    completed = subprocess.run(
        ("/usr/bin/git", "-C", str(root), "rev-parse", "--git-common-dir"),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_git_environment(),
        timeout=10,
    )
    if completed.returncode != 0:
        raise OSError("repository_git_common_directory_read_failed")
    return completed.stdout.decode("utf-8").rstrip("\n")


def _read_shallow_posture(root: Path) -> str:
    completed = subprocess.run(
        (
            "/usr/bin/git",
            "-C",
            str(root),
            "rev-parse",
            "--is-shallow-repository",
        ),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_git_environment(),
        timeout=10,
    )
    if completed.returncode != 0:
        raise OSError("repository_shallow_posture_read_failed")
    return completed.stdout.decode("ascii").rstrip("\n")


def _read_ref_snapshot(root: Path) -> str:
    completed = subprocess.run(
        (
            "/usr/bin/git",
            "-C",
            str(root),
            "for-each-ref",
            "--format=%(refname)%00%(objectname)%00%(*objectname)",
        ),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_git_environment(),
        timeout=10,
    )
    if completed.returncode != 0:
        raise OSError("repository_ref_snapshot_read_failed")
    return completed.stdout.decode("utf-8").rstrip("\n")


def _read_head(root: Path) -> tuple[int, str]:
    completed = subprocess.run(
        ("/usr/bin/git", "-C", str(root), "rev-parse", "--verify", "HEAD"),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_git_environment(),
        timeout=10,
    )
    return completed.returncode, completed.stdout.decode("ascii").rstrip("\n")


def _read_commit_peel(root: Path, revision: str) -> tuple[int, str]:
    _commit(revision)
    completed = subprocess.run(
        (
            "/usr/bin/git",
            "-C",
            str(root),
            "rev-parse",
            "--verify",
            f"{revision}^{{commit}}",
        ),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_git_environment(),
        timeout=10,
    )
    return completed.returncode, completed.stdout.decode("ascii").rstrip("\n")


def _read_ancestry_status(root: Path, ancestor: str, descendant: str) -> int:
    _commit(ancestor)
    _commit(descendant)
    completed = subprocess.run(
        (
            "/usr/bin/git",
            "-C",
            str(root),
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_git_environment(),
        timeout=10,
    )
    return completed.returncode


def _object_identity(root: Path, revision: str) -> tuple[str, int] | None:
    _commit(revision)
    completed = subprocess.run(
        (
            "/usr/bin/git",
            "-C",
            str(root),
            "cat-file",
            "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        ),
        check=False,
        input=f"{revision}\n".encode("ascii"),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=_git_environment(),
        timeout=10,
    )
    output = completed.stdout.decode("ascii").strip()
    if completed.returncode != 0:
        raise OSError("repository_object_identity_read_failed")
    if output == f"{revision} missing":
        return None
    fields = output.split(" ")
    if (
        len(fields) != 3
        or fields[0] != revision
        or not fields[1]
        or not fields[2].isdigit()
    ):
        raise OSError("repository_object_identity_invalid")
    return fields[1], int(fields[2])


def _resolve_git_path(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve(strict=True)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest_payload(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _ref(value: str) -> None:
    if type(value) is not str or _REF.fullmatch(value) is None:
        raise ValueError("repository_reachability_ref_invalid")


def _digest(value: str) -> None:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise ValueError("repository_reachability_digest_invalid")


def _commit(value: str) -> None:
    if type(value) is not str or _COMMIT.fullmatch(value) is None:
        raise ValueError("repository_reachability_commit_invalid")


__all__ = [
    "WorkspaceRepositoryReachabilityAuthorityGrade",
    "WorkspaceRepositoryReachabilityCounters",
    "WorkspaceRepositoryReachabilityError",
    "WorkspaceRepositoryReachabilityPosture",
    "WorkspaceRepositoryReachabilityReader",
    "WorkspaceRepositoryReachabilityRequest",
    "WorkspaceRepositoryReachabilityResult",
    "WorkspaceRepositoryRevisionPosture",
    "WorkspaceRepositoryRevisionReachability",
]
