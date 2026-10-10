from __future__ import annotations

import hashlib
from bisect import bisect_left
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath

from .change_evidence import MAX_CONTEXT_REFS, RepositoryChangedEntryKind
from .repository_access import RepositoryObservationCoordinate

MAX_DELTA_CAPTURE_PATHS = 4096
MAX_DELTA_SCOPE_PATHS = 512
MAX_DELTA_CAPTURE_SELECTED_BYTES = 512 * 1024 * 1024
MAX_DELTA_CAPTURE_BODY_BYTES = 16 * 1024 * 1024
MAX_DELTA_CAPTURE_RETAINED_CHANGES = 4096
MAX_DELTA_CAPTURE_RETAINED_BYTES = 512 * 1024 * 1024
MAX_DELTA_CAPTURE_READ_ATTEMPTS = 3


class RepositoryDeltaCapturePathState(StrEnum):
    COVERED = "covered"
    ABSENT = "absent"
    EXCLUDED = "excluded"
    UNSTABLE = "unstable"
    OVER_BUDGET = "over_budget"


class RepositoryContentDeltaState(StrEnum):
    AVAILABLE = "available"
    BINARY = "binary"
    MISSING_PREIMAGE = "missing_preimage"
    MISSING_TARGET = "missing_target"
    UNSTABLE_BODY = "unstable_body"
    OVER_BUDGET = "over_budget"
    EVICTED = "evicted"
    GAP = "gap"


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaCapturePolicy:
    policy_version: str = "delta-first-v1"
    maximum_selected_files: int = 64
    maximum_selected_bytes: int = 4 * 1024 * 1024
    maximum_body_bytes: int = 1024 * 1024
    maximum_retained_changes: int = 256
    maximum_retained_bytes: int = 64 * 1024 * 1024
    maximum_read_attempts: int = 2

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "policy_version", _required(self.policy_version, "policy_version")
        )
        _bounded_positive(
            self.maximum_selected_files,
            MAX_DELTA_CAPTURE_PATHS,
            "maximum_selected_files",
        )
        _bounded_positive(
            self.maximum_selected_bytes,
            MAX_DELTA_CAPTURE_SELECTED_BYTES,
            "maximum_selected_bytes",
        )
        _bounded_positive(
            self.maximum_body_bytes,
            MAX_DELTA_CAPTURE_BODY_BYTES,
            "maximum_body_bytes",
        )
        if self.maximum_body_bytes > self.maximum_selected_bytes:
            raise ValueError("maximum_body_bytes cannot exceed selected byte budget")
        _bounded_positive(
            self.maximum_retained_changes,
            MAX_DELTA_CAPTURE_RETAINED_CHANGES,
            "maximum_retained_changes",
        )
        _bounded_positive(
            self.maximum_retained_bytes,
            MAX_DELTA_CAPTURE_RETAINED_BYTES,
            "maximum_retained_bytes",
        )
        if self.maximum_selected_bytes > self.maximum_retained_bytes:
            raise ValueError("selected byte budget cannot exceed retention byte budget")
        _bounded_positive(
            self.maximum_read_attempts,
            MAX_DELTA_CAPTURE_READ_ATTEMPTS,
            "maximum_read_attempts",
        )


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaCapturePath:
    path: str
    state: RepositoryDeltaCapturePathState
    content_digest: str | None = None
    size_bytes: int | None = None
    body_ref: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        path = _relative_path(self.path)
        digest = _optional_digest(self.content_digest, "content_digest")
        body_ref = _optional(self.body_ref, "body_ref")
        reason = _optional(self.reason, "reason")
        _optional_non_negative(self.size_bytes, "size_bytes")
        if self.state is RepositoryDeltaCapturePathState.COVERED:
            if digest is None or self.size_bytes is None or body_ref is None:
                raise ValueError("Covered capture path requires exact retained body")
            if body_ref != repository_delta_body_ref(digest):
                raise ValueError("Capture path body_ref does not match content digest")
            if reason is not None:
                raise ValueError("Covered capture path cannot carry reason")
        elif self.state is RepositoryDeltaCapturePathState.ABSENT:
            if any(
                value is not None
                for value in (digest, self.size_bytes, body_ref, reason)
            ):
                raise ValueError("Absent capture path cannot carry body state")
        else:
            if digest is not None or body_ref is not None or reason is None:
                raise ValueError(
                    "Unavailable capture path requires only bounded reason"
                )
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "content_digest", digest)
        object.__setattr__(self, "body_ref", body_ref)
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaCapture:
    capture_ref: str
    repository_binding_ref: str
    admitted_coordinate: RepositoryObservationCoordinate
    selection_digest: str
    selected_paths: tuple[str, ...]
    path_states: tuple[WorkspaceRepositoryDeltaCapturePath, ...]
    policy: WorkspaceRepositoryDeltaCapturePolicy
    checkpoint_revision: int
    opened_at: datetime
    updated_at: datetime
    context_refs: tuple[str, ...] = ()
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        _validate_coordinate(self.admitted_coordinate, binding_ref)
        selected_paths = tuple(
            sorted({_relative_path(path) for path in self.selected_paths})
        )
        if not selected_paths:
            raise ValueError("Delta capture requires selected paths")
        if len(selected_paths) != len(self.selected_paths):
            raise ValueError("Delta capture selected paths must be unique")
        if len(selected_paths) > self.policy.maximum_selected_files:
            raise ValueError("Delta capture selected path count exceeds policy")
        selection_digest = repository_delta_selection_digest(selected_paths)
        if self.selection_digest != selection_digest:
            raise ValueError("Delta capture selection digest is not deterministic")
        path_states = tuple(sorted(self.path_states, key=lambda value: value.path))
        if tuple(value.path for value in path_states) != selected_paths:
            raise ValueError(
                "Delta capture requires exactly one state per selected path"
            )
        covered_bytes = sum(
            value.size_bytes or 0
            for value in path_states
            if value.state is RepositoryDeltaCapturePathState.COVERED
        )
        if covered_bytes > self.policy.maximum_selected_bytes:
            raise ValueError("Delta capture covered bytes exceed policy")
        if any(
            (value.size_bytes or 0) > self.policy.maximum_body_bytes
            for value in path_states
            if value.state is RepositoryDeltaCapturePathState.COVERED
        ):
            raise ValueError("Delta capture body exceeds policy")
        if isinstance(self.checkpoint_revision, bool) or self.checkpoint_revision < 0:
            raise ValueError("Delta capture checkpoint revision must be non-negative")
        opened_at = _utc(self.opened_at)
        updated_at = _utc(self.updated_at)
        closed_at = _optional_utc(self.closed_at)
        if updated_at < opened_at or (closed_at is not None and closed_at < updated_at):
            raise ValueError("Delta capture lifecycle timestamps are inconsistent")
        context_refs = _unique_refs(self.context_refs)
        expected_ref = repository_delta_capture_ref(
            repository_binding_ref=binding_ref,
            admitted_coordinate=self.admitted_coordinate,
            selection_digest=selection_digest,
            policy_version=self.policy.policy_version,
        )
        if self.capture_ref != expected_ref:
            raise ValueError("Delta capture ref is not deterministic")
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "selected_paths", selected_paths)
        object.__setattr__(self, "path_states", path_states)
        object.__setattr__(self, "context_refs", context_refs)
        object.__setattr__(self, "opened_at", opened_at)
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(self, "closed_at", closed_at)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryContentDelta:
    delta_ref: str
    capture_ref: str
    repository_binding_ref: str
    before_coordinate: RepositoryObservationCoordinate
    after_coordinate: RepositoryObservationCoordinate
    kind: RepositoryChangedEntryKind
    state: RepositoryContentDeltaState
    path_sequence: int
    capture_checkpoint_revision: int
    old_path: str | None = None
    new_path: str | None = None
    old_content_digest: str | None = None
    new_content_digest: str | None = None
    old_size_bytes: int | None = None
    new_size_bytes: int | None = None
    old_body_ref: str | None = None
    new_body_ref: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        capture_ref = _required(self.capture_ref, "capture_ref")
        _validate_coordinate(self.before_coordinate, binding_ref)
        _validate_coordinate(self.after_coordinate, binding_ref)
        if (
            self.before_coordinate.epoch != self.after_coordinate.epoch
            or self.after_coordinate.cursor <= self.before_coordinate.cursor
        ):
            raise ValueError(
                "Content delta requires one forward observer epoch interval"
            )
        if isinstance(self.path_sequence, bool) or self.path_sequence <= 0:
            raise ValueError("Content delta path sequence must be positive")
        if (
            isinstance(self.capture_checkpoint_revision, bool)
            or self.capture_checkpoint_revision <= 0
        ):
            raise ValueError(
                "Content delta capture checkpoint revision must be positive"
            )
        old_path = _optional_path(self.old_path)
        new_path = _optional_path(self.new_path)
        _validate_change_paths(self.kind, old_path, new_path)
        old_digest = _optional_digest(self.old_content_digest, "old_content_digest")
        new_digest = _optional_digest(self.new_content_digest, "new_content_digest")
        old_body_ref = _optional(self.old_body_ref, "old_body_ref")
        new_body_ref = _optional(self.new_body_ref, "new_body_ref")
        _optional_non_negative(self.old_size_bytes, "old_size_bytes")
        _optional_non_negative(self.new_size_bytes, "new_size_bytes")
        _validate_side(
            path=old_path,
            digest=old_digest,
            size_bytes=self.old_size_bytes,
            body_ref=old_body_ref,
            side="old",
        )
        _validate_side(
            path=new_path,
            digest=new_digest,
            size_bytes=self.new_size_bytes,
            body_ref=new_body_ref,
            side="new",
        )
        reason = _optional(self.reason, "reason")
        if self.state in {
            RepositoryContentDeltaState.AVAILABLE,
            RepositoryContentDeltaState.BINARY,
        }:
            if reason is not None:
                raise ValueError("Available content delta cannot carry reason")
            if old_path is not None and old_body_ref is None:
                raise ValueError("Available content delta requires retained old body")
            if new_path is not None and new_body_ref is None:
                raise ValueError("Available content delta requires retained new body")
            if (self.kind is RepositoryChangedEntryKind.BINARY) != (
                self.state is RepositoryContentDeltaState.BINARY
            ):
                raise ValueError("Binary content delta kind/state must agree")
        elif reason is None:
            raise ValueError("Unavailable content delta requires reason")
        if self.state is RepositoryContentDeltaState.MISSING_PREIMAGE and (
            old_path is None or old_body_ref is not None
        ):
            raise ValueError("Missing-preimage delta requires an unavailable old body")
        if self.state is RepositoryContentDeltaState.MISSING_TARGET and (
            new_path is None or new_body_ref is not None
        ):
            raise ValueError("Missing-target delta requires an unavailable new body")
        expected_ref = repository_content_delta_ref(
            capture_ref=capture_ref,
            repository_binding_ref=binding_ref,
            before_coordinate=self.before_coordinate,
            after_coordinate=self.after_coordinate,
            kind=self.kind,
            old_path=old_path,
            new_path=new_path,
            old_content_digest=old_digest,
            new_content_digest=new_digest,
        )
        if self.delta_ref != expected_ref:
            raise ValueError("Content delta ref is not deterministic")
        object.__setattr__(self, "capture_ref", capture_ref)
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "old_path", old_path)
        object.__setattr__(self, "new_path", new_path)
        object.__setattr__(self, "old_content_digest", old_digest)
        object.__setattr__(self, "new_content_digest", new_digest)
        object.__setattr__(self, "old_body_ref", old_body_ref)
        object.__setattr__(self, "new_body_ref", new_body_ref)
        object.__setattr__(self, "reason", reason)


def validate_repository_delta_capture_advance(
    previous: WorkspaceRepositoryDeltaCapture,
    candidate: WorkspaceRepositoryDeltaCapture,
) -> None:
    if (
        candidate.capture_ref != previous.capture_ref
        or candidate.repository_binding_ref != previous.repository_binding_ref
        or candidate.admitted_coordinate != previous.admitted_coordinate
        or candidate.selection_digest != previous.selection_digest
        or candidate.selected_paths != previous.selected_paths
        or candidate.policy != previous.policy
        or candidate.opened_at != previous.opened_at
    ):
        raise ValueError("Delta capture advance cannot rewrite stable authority")
    if candidate.checkpoint_revision != previous.checkpoint_revision + 1:
        raise ValueError("Delta capture revision must advance by exactly one")
    if candidate.updated_at < previous.updated_at:
        raise ValueError("Delta capture update time cannot move backwards")
    if previous.closed_at is not None:
        raise ValueError("Closed delta capture cannot advance")
    if not set(previous.context_refs).issubset(candidate.context_refs):
        raise ValueError("Delta capture advance cannot erase context refs")


def repository_delta_selection_digest(paths: tuple[str, ...]) -> str:
    normalized = tuple(sorted({_relative_path(path) for path in paths}))
    if not normalized or len(normalized) != len(paths):
        raise ValueError("Delta capture selection must be non-empty and unique")
    digest = hashlib.sha256()
    for value in normalized:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def repository_delta_scope_selection(
    scope_paths: tuple[str, ...],
    *,
    observed_paths: tuple[str, ...],
) -> tuple[str, ...]:
    """Resolve semantic file/directory scope from one resident observation."""

    roots = tuple(sorted(_relative_path(path) for path in scope_paths))
    if not roots or len(roots) > MAX_DELTA_SCOPE_PATHS:
        raise ValueError("Delta capture scope selection exceeds policy")
    if len(set(roots)) != len(roots):
        raise ValueError("Delta capture scope paths must be unique")
    observed = observed_paths
    if any(
        observed[index - 1] >= observed[index]
        for index in range(1, len(observed))
    ):
        raise ValueError("Observed repository paths must be sorted and unique")
    observed_set = frozenset(observed)
    selected: set[str] = set()
    for root in roots:
        matched = False
        if root in observed_set:
            selected.add(root)
            matched = True
        prefix = f"{root}/"
        index = bisect_left(observed, prefix)
        while index < len(observed) and observed[index].startswith(prefix):
            selected.add(observed[index])
            matched = True
            if len(selected) > MAX_DELTA_SCOPE_PATHS:
                raise ValueError("Delta capture scope expansion exceeds policy")
            index += 1
        if not matched:
            selected.add(root)
        if len(selected) > MAX_DELTA_SCOPE_PATHS:
            raise ValueError("Delta capture scope expansion exceeds policy")
    return tuple(sorted(selected))


def repository_delta_selection_shards(
    paths: tuple[str, ...],
    *,
    policy: WorkspaceRepositoryDeltaCapturePolicy,
) -> tuple[tuple[str, ...], ...]:
    """Partition one exact selection without widening a capture policy."""

    normalized = tuple(sorted(_relative_path(path) for path in paths))
    if not normalized or len(normalized) > MAX_DELTA_CAPTURE_PATHS:
        raise ValueError("Delta capture batch selection exceeds policy")
    if len(set(normalized)) != len(normalized):
        raise ValueError("Delta capture batch paths must be unique")
    limit = policy.maximum_selected_files
    return tuple(
        normalized[offset : offset + limit]
        for offset in range(0, len(normalized), limit)
    )


def repository_delta_capture_ref(
    *,
    repository_binding_ref: str,
    admitted_coordinate: RepositoryObservationCoordinate,
    selection_digest: str,
    policy_version: str,
) -> str:
    binding_ref = _required(repository_binding_ref, "repository_binding_ref")
    _validate_coordinate(admitted_coordinate, binding_ref)
    return _digest_ref(
        "workspace-repository-delta-capture",
        binding_ref,
        _coordinate_token(admitted_coordinate),
        _required(selection_digest, "selection_digest"),
        _required(policy_version, "policy_version"),
    )


def repository_delta_body_ref(content_digest: str) -> str:
    return "workspace-repository-body:" + _digest(content_digest, "content_digest")


def repository_content_delta_ref(
    *,
    capture_ref: str,
    repository_binding_ref: str,
    before_coordinate: RepositoryObservationCoordinate,
    after_coordinate: RepositoryObservationCoordinate,
    kind: RepositoryChangedEntryKind,
    old_path: str | None,
    new_path: str | None,
    old_content_digest: str | None,
    new_content_digest: str | None,
) -> str:
    binding_ref = _required(repository_binding_ref, "repository_binding_ref")
    _validate_coordinate(before_coordinate, binding_ref)
    _validate_coordinate(after_coordinate, binding_ref)
    return _digest_ref(
        "workspace-repository-content-delta",
        _required(capture_ref, "capture_ref"),
        binding_ref,
        _coordinate_token(before_coordinate),
        _coordinate_token(after_coordinate),
        kind.value,
        old_path or "",
        new_path or "",
        old_content_digest or "",
        new_content_digest or "",
    )


def _validate_side(
    *,
    path: str | None,
    digest: str | None,
    size_bytes: int | None,
    body_ref: str | None,
    side: str,
) -> None:
    if path is None:
        if any(value is not None for value in (digest, size_bytes, body_ref)):
            raise ValueError(f"Absent {side} side cannot carry body state")
        return
    if body_ref is not None:
        if digest is None or body_ref != repository_delta_body_ref(digest):
            raise ValueError(f"{side} body_ref does not match content digest")
    if digest is None and body_ref is not None:
        raise ValueError(f"{side} body requires content digest")


def _validate_change_paths(
    kind: RepositoryChangedEntryKind, old_path: str | None, new_path: str | None
) -> None:
    if kind is RepositoryChangedEntryKind.CREATE:
        if old_path is not None or new_path is None:
            raise ValueError("Create delta requires only target path")
    elif kind is RepositoryChangedEntryKind.DELETE:
        if old_path is None or new_path is not None:
            raise ValueError("Delete delta requires only prior path")
    elif kind is RepositoryChangedEntryKind.RENAME:
        if old_path is None or new_path is None or old_path == new_path:
            raise ValueError("Rename delta requires distinct paths")
    elif old_path is None or new_path is None or old_path != new_path:
        raise ValueError("Update/binary delta requires one stable path")


def _validate_coordinate(
    coordinate: RepositoryObservationCoordinate, repository_binding_ref: str
) -> None:
    if coordinate.repository_binding_ref != repository_binding_ref:
        raise ValueError("Observation coordinate repository binding differs")
    _required(coordinate.epoch, "coordinate.epoch")
    if isinstance(coordinate.cursor, bool) or coordinate.cursor < 0:
        raise ValueError("Observation coordinate cursor must be non-negative")
    _required(coordinate.snapshot_digest, "coordinate.snapshot_digest")
    _required(coordinate.visibility_policy_ref, "coordinate.visibility_policy_ref")
    _required(
        coordinate.visibility_policy_version, "coordinate.visibility_policy_version"
    )


def _coordinate_token(value: RepositoryObservationCoordinate) -> str:
    return "|".join(
        (
            value.repository_binding_ref,
            value.epoch,
            str(value.cursor),
            value.snapshot_digest,
            value.visibility_policy_ref,
            value.visibility_policy_version,
        )
    )


def _relative_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or normalized != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"Repository path must be normalized and relative: {value!r}")
    return normalized


def _optional_path(value: str | None) -> str | None:
    return None if value is None else _relative_path(value)


def _required(value: str | None, field_name: str) -> str:
    if value is None or not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _optional(value: str | None, field_name: str) -> str | None:
    return None if value is None else _required(value, field_name)


def _digest(value: str, field_name: str) -> str:
    digest = _required(value, field_name)
    if len(digest) != 71 or not digest.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a canonical sha256 digest")
    try:
        int(digest[7:], 16)
    except ValueError as error:
        raise ValueError(f"{field_name} must be a canonical sha256 digest") from error
    if digest != digest.lower():
        raise ValueError(f"{field_name} must be a canonical sha256 digest")
    return digest


def _optional_digest(value: str | None, field_name: str) -> str | None:
    return None if value is None else _digest(value, field_name)


def _unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(_required(value, "context_ref") for value in values)
    if len(normalized) > MAX_CONTEXT_REFS or len(set(normalized)) != len(normalized):
        raise ValueError("context_refs must be unique and bounded")
    return normalized


def _bounded_positive(value: int, maximum: int, field_name: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 < value <= maximum
    ):
        raise ValueError(f"{field_name} must be positive and bounded")


def _optional_non_negative(value: int | None, field_name: str) -> None:
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value < 0
    ):
        raise ValueError(f"{field_name} must be non-negative")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _utc(value)


def _digest_ref(prefix: str, *values: str) -> str:
    digest = hashlib.sha256()
    for value in (prefix, *values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"{prefix}:sha256:{digest.hexdigest()}"
