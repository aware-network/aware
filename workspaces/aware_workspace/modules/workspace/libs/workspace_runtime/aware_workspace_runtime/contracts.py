from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath

RUNTIME_CONTRACT_VERSION = "0.1"


class ObservationChangeKind(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ObservationGapReason(StrEnum):
    EPOCH_MISMATCH = "epoch_mismatch"
    RETENTION_EXCEEDED = "retention_exceeded"
    CURSOR_AHEAD = "cursor_ahead"


class ObservationRuntimeState(StrEnum):
    NEW = "new"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryBinding:
    root_path: Path
    binding_key: str | None = None
    filter_version: str = "canonical-source-v1"

    def __post_init__(self) -> None:
        root = self.root_path.expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"Repository root must be an existing directory: {root}")
        filter_version = _required_token(self.filter_version, "filter_version")
        binding_key = self.binding_key
        if binding_key is None:
            digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()
            binding_key = f"local-root:{digest}"
        binding_key = _required_token(binding_key, "binding_key")
        object.__setattr__(self, "root_path", root)
        object.__setattr__(self, "binding_key", binding_key)
        object.__setattr__(self, "filter_version", filter_version)


@dataclass(frozen=True, slots=True)
class RepositorySnapshotEntry:
    path: str
    size_bytes: int
    modified_ns: int
    content_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _relative_path(self.path))
        if self.size_bytes < 0:
            raise ValueError("RepositorySnapshotEntry.size_bytes must be non-negative")
        if self.modified_ns < 0:
            raise ValueError("RepositorySnapshotEntry.modified_ns must be non-negative")
        if self.content_digest is not None:
            object.__setattr__(
                self,
                "content_digest",
                _required_token(self.content_digest, "content_digest"),
            )


@dataclass(frozen=True, slots=True)
class RepositoryObservationChange:
    kind: ObservationChangeKind
    path: str
    entry: RepositorySnapshotEntry | None = None

    def __post_init__(self) -> None:
        path = _relative_path(self.path)
        if self.kind is ObservationChangeKind.DELETE:
            if self.entry is not None:
                raise ValueError("Delete changes cannot carry a target entry")
        elif self.entry is None or self.entry.path != path:
            raise ValueError("Create/update changes require a matching target entry")
        object.__setattr__(self, "path", path)


@dataclass(frozen=True, slots=True)
class RepositoryProviderObservation:
    observed_at: datetime
    entries: tuple[RepositorySnapshotEntry, ...]
    changes: tuple[RepositoryObservationChange, ...] = ()
    baseline_entries: tuple[RepositorySnapshotEntry, ...] | None = None
    baseline_observed_at: datetime | None = None
    snapshot_digest: str = field(init=False)

    def __post_init__(self) -> None:
        observed_at = _utc(self.observed_at)
        entries = tuple(sorted(self.entries, key=lambda item: item.path))
        changes = tuple(
            sorted(self.changes, key=lambda item: (item.path, item.kind.value))
        )
        baseline_entries = (
            None
            if self.baseline_entries is None
            else tuple(sorted(self.baseline_entries, key=lambda item: item.path))
        )
        if (baseline_entries is None) != (self.baseline_observed_at is None):
            raise ValueError(
                "Provider baseline entries and observation time must be paired"
            )
        _unique_paths(entries, "provider snapshot")
        _unique_paths(changes, "provider changes")
        if baseline_entries is not None:
            _unique_paths(baseline_entries, "provider baseline snapshot")
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "changes", changes)
        object.__setattr__(self, "baseline_entries", baseline_entries)
        object.__setattr__(
            self,
            "baseline_observed_at",
            None
            if self.baseline_observed_at is None
            else _utc(self.baseline_observed_at),
        )
        object.__setattr__(self, "snapshot_digest", repository_snapshot_digest(entries))

    def reobserve_exact(self, observed_at: datetime) -> RepositoryProviderObservation:
        """Reuse this validated immutable snapshot at a later observation time."""
        value = object.__new__(RepositoryProviderObservation)
        object.__setattr__(value, "observed_at", _utc(observed_at))
        object.__setattr__(value, "entries", self.entries)
        object.__setattr__(value, "changes", ())
        object.__setattr__(value, "baseline_entries", None)
        object.__setattr__(value, "baseline_observed_at", None)
        object.__setattr__(value, "snapshot_digest", self.snapshot_digest)
        return value


@dataclass(frozen=True, slots=True)
class RepositoryPathQuery:
    query_ref: str
    prefixes: tuple[str, ...]
    maximum_depth: int
    maximum_entries: int
    maximum_examined: int
    suffixes: tuple[str, ...] = ()
    query_digest: str = field(init=False)

    def __post_init__(self) -> None:
        query_ref = _required_token(self.query_ref, "query_ref")
        prefixes = tuple(sorted({_relative_path(value) for value in self.prefixes}))
        suffixes = tuple(
            sorted({_required_token(value, "suffix") for value in self.suffixes})
        )
        if not prefixes:
            raise ValueError("Repository path query requires at least one prefix")
        if self.maximum_depth < 0:
            raise ValueError("Repository path query depth cannot be negative")
        if self.maximum_entries <= 0:
            raise ValueError("Repository path query entry budget must be positive")
        if self.maximum_examined < self.maximum_entries:
            raise ValueError(
                "Repository path query examination budget must cover entries"
            )
        digest = hashlib.sha256()
        for value in (
            query_ref,
            *prefixes,
            str(self.maximum_depth),
            str(self.maximum_entries),
            str(self.maximum_examined),
            *suffixes,
        ):
            encoded = value.encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
        object.__setattr__(self, "query_ref", query_ref)
        object.__setattr__(self, "prefixes", prefixes)
        object.__setattr__(self, "suffixes", suffixes)
        object.__setattr__(self, "query_digest", "sha256:" + digest.hexdigest())


@dataclass(frozen=True, slots=True)
class RepositoryProviderQueryObservation:
    query_digest: str
    observed_at: datetime
    entries: tuple[RepositorySnapshotEntry, ...]
    examined_count: int
    truncated: bool
    inaccessible_count: int = 0
    snapshot_digest: str = field(init=False)

    def __post_init__(self) -> None:
        entries = tuple(sorted(self.entries, key=lambda item: item.path))
        _unique_paths(entries, "provider query snapshot")
        if self.examined_count < len(entries):
            raise ValueError("Provider query examined count is inconsistent")
        if self.inaccessible_count < 0:
            raise ValueError("Provider query inaccessible count cannot be negative")
        object.__setattr__(
            self, "query_digest", _required_token(self.query_digest, "query_digest")
        )
        object.__setattr__(self, "observed_at", _utc(self.observed_at))
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "snapshot_digest", repository_snapshot_digest(entries))


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryQuerySnapshot:
    binding_key: str
    epoch: str
    cursor: int
    query_ref: str
    query_digest: str
    observed_at: datetime
    snapshot_digest: str
    entries: tuple[RepositorySnapshotEntry, ...]
    examined_count: int
    truncated: bool
    inaccessible_count: int = 0
    changed_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "binding_key", _required_token(self.binding_key, "binding_key")
        )
        object.__setattr__(self, "epoch", _required_token(self.epoch, "epoch"))
        object.__setattr__(
            self, "query_ref", _required_token(self.query_ref, "query_ref")
        )
        object.__setattr__(
            self, "query_digest", _required_token(self.query_digest, "query_digest")
        )
        if self.cursor < 0:
            raise ValueError("Repository query cursor cannot be negative")
        entries = tuple(sorted(self.entries, key=lambda item: item.path))
        _unique_paths(entries, "repository query snapshot")
        if repository_snapshot_digest(entries) != self.snapshot_digest:
            raise ValueError("Repository query snapshot digest does not match entries")
        changed_paths = tuple(
            sorted({_relative_path(path) for path in self.changed_paths})
        )
        object.__setattr__(self, "observed_at", _utc(self.observed_at))
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "changed_paths", changed_paths)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryObservationSnapshot:
    binding_key: str
    epoch: str
    cursor: int
    observed_at: datetime
    snapshot_digest: str
    entries: tuple[RepositorySnapshotEntry, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "binding_key", _required_token(self.binding_key, "binding_key")
        )
        object.__setattr__(self, "epoch", _required_token(self.epoch, "epoch"))
        if self.cursor < 0:
            raise ValueError("Observation snapshot cursor must be non-negative")
        entries = tuple(sorted(self.entries, key=lambda item: item.path))
        _unique_paths(entries, "observation snapshot")
        digest = repository_snapshot_digest(entries)
        if self.snapshot_digest != digest:
            raise ValueError("Observation snapshot digest does not match entries")
        object.__setattr__(self, "observed_at", _utc(self.observed_at))
        object.__setattr__(self, "entries", entries)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryObservationBatch:
    binding_key: str
    epoch: str
    cursor: int
    observed_at: datetime
    before_snapshot_digest: str
    after_snapshot_digest: str
    changes: tuple[RepositoryObservationChange, ...]
    coalesced: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "binding_key", _required_token(self.binding_key, "binding_key")
        )
        object.__setattr__(self, "epoch", _required_token(self.epoch, "epoch"))
        if self.cursor <= 0:
            raise ValueError("Observation batch cursor must be positive")
        changes = tuple(
            sorted(self.changes, key=lambda item: (item.path, item.kind.value))
        )
        if not changes:
            raise ValueError("Observation batches cannot be empty")
        _unique_paths(changes, "observation batch")
        object.__setattr__(self, "observed_at", _utc(self.observed_at))
        object.__setattr__(self, "changes", changes)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryObservationGap:
    reason: ObservationGapReason
    requested_epoch: str | None
    available_epoch: str
    requested_after_cursor: int
    oldest_available_cursor: int
    current_cursor: int
    reset_snapshot: WorkspaceRepositoryObservationSnapshot


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryObservationReplay:
    epoch: str
    after_cursor: int
    current_cursor: int
    batches: tuple[WorkspaceRepositoryObservationBatch, ...] = ()
    gap: WorkspaceRepositoryObservationGap | None = None

    def __post_init__(self) -> None:
        if self.gap is not None and self.batches:
            raise ValueError("Observation replay cannot contain batches and a gap")


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryObservationCheckpoint:
    consumer_key: str
    epoch: str
    cursor: int
    accepted_at: datetime
    projection_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "consumer_key", _required_token(self.consumer_key, "consumer_key")
        )
        object.__setattr__(self, "epoch", _required_token(self.epoch, "epoch"))
        if self.cursor < 0:
            raise ValueError("Observation checkpoint cursor must be non-negative")
        object.__setattr__(self, "accepted_at", _utc(self.accepted_at))


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryObservationHealth:
    state: ObservationRuntimeState
    epoch: str
    cursor: int
    files_tracked: int
    journal_size: int
    consecutive_failures: int = 0
    last_error: str | None = None
    last_observed_at: datetime | None = None


type RepositoryPathValue = RepositorySnapshotEntry | RepositoryObservationChange


def repository_snapshot_digest(entries: tuple[RepositorySnapshotEntry, ...]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item.path):
        for value in (
            entry.path,
            str(entry.size_bytes),
            str(entry.modified_ns),
            entry.content_digest or "",
        ):
            encoded = value.encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def _relative_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"Repository path must be confined and relative: {value!r}")
    return path.as_posix()


def _required_token(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _unique_paths(values: tuple[RepositoryPathValue, ...], label: str) -> None:
    paths = tuple(item.path for item in values)
    if len(paths) != len(set(paths)):
        raise ValueError(f"{label} paths must be unique")
