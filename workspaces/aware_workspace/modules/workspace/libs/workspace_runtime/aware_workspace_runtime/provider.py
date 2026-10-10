from __future__ import annotations

import asyncio
import os
import stat
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Protocol

from aware_file_system.config import (
    CanonicalSourceFilterConfig,
    Config,
    FileSystemConfig,
)
from aware_file_system.bounded_query import BoundedPathQuery, query_bounded_paths
from aware_file_system.index.file_metadata_cached import FileMetadataCached
from aware_file_system.index.file_system_index import FileSystemIndex
from aware_file_system.observation_backend import (
    BackendObservation,
    ObservationBackend,
    ObservationBackendMode,
)

from .contracts import (
    ObservationChangeKind,
    RepositoryPathQuery,
    RepositoryProviderQueryObservation,
    RepositoryObservationChange,
    RepositoryProviderObservation,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
)


class WorkspaceRepositoryObservationProvider(Protocol):
    @property
    def root_path(self) -> Path: ...

    async def initialize(self) -> RepositoryProviderObservation: ...

    async def poll(self) -> RepositoryProviderObservation: ...

    async def query(
        self, request: RepositoryPathQuery
    ) -> RepositoryProviderQueryObservation: ...

    async def close(self) -> None: ...


class FileSystemIndexObservationProvider:
    """Workspace-facing adapter over one FileSystem incremental index."""

    def __init__(
        self,
        *,
        binding: WorkspaceRepositoryBinding,
        index: FileSystemIndex | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        config = Config(
            file_system=FileSystemConfig(
                root_path=str(binding.root_path),
                generate_tree=False,
                export_json=False,
            ),
            filter=CanonicalSourceFilterConfig(),
        )
        resolved_index = index or FileSystemIndex(
            config,
            cache_dir=str(cache_dir) if cache_dir is not None else None,
        )
        if resolved_index.root_path != binding.root_path:
            raise ValueError(
                "FileSystem index root does not match Workspace repository binding"
            )
        self._binding = binding
        self._index = resolved_index
        self._poll_lock = asyncio.Lock()
        self._advertised_entries: dict[str, RepositorySnapshotEntry] | None = None

    @property
    def root_path(self) -> Path:
        return self._binding.root_path

    @property
    def index(self) -> FileSystemIndex:
        return self._index

    async def initialize(self) -> RepositoryProviderObservation:
        async with self._poll_lock:
            scan_result, current = await asyncio.to_thread(
                self._index.refresh_relative_metadata
            )
        entries = _snapshot_entries(current)
        baseline_available = bool(getattr(scan_result, "baseline_available", False))
        baseline_entries = (
            _snapshot_entries(scan_result.baseline_entries)
            if baseline_available
            else None
        )
        entries_by_path = {entry.path: entry for entry in entries}
        baseline_by_path = (
            None
            if baseline_entries is None
            else {entry.path: entry for entry in baseline_entries}
        )
        self._advertised_entries = {entry.path: entry for entry in entries}
        return RepositoryProviderObservation(
            observed_at=datetime.now(UTC),
            entries=entries,
            changes=(
                ()
                if baseline_by_path is None
                else _observation_changes(baseline_by_path, entries_by_path)
            ),
            baseline_entries=baseline_entries,
            baseline_observed_at=(
                getattr(scan_result, "baseline_observed_at", None)
                if baseline_available
                else None
            ),
        )

    async def poll(self) -> RepositoryProviderObservation:
        async with self._poll_lock:
            _scan_result, current = await asyncio.to_thread(
                self._index.refresh_relative_metadata
            )
        entries_by_path = {entry.path: entry for entry in _snapshot_entries(current)}
        previous = self._advertised_entries
        if previous is None:
            raise RuntimeError("FileSystem observation provider is not initialized")
        changes = _observation_changes(previous, entries_by_path)
        self._advertised_entries = entries_by_path
        return RepositoryProviderObservation(
            observed_at=datetime.now(UTC),
            entries=tuple(entries_by_path.values()),
            changes=changes,
        )

    async def observe_paths(
        self, paths: tuple[str, ...]
    ) -> RepositoryProviderObservation:
        """Observe exact paths without traversing the repository inventory."""

        async with self._poll_lock:
            previous = self._advertised_entries
            if previous is None:
                raise RuntimeError("FileSystem observation provider is not initialized")
            observed = await asyncio.to_thread(
                _observe_exact_path_entries,
                root_path=self._binding.root_path,
                paths=paths,
                include_files=self._index.scanner.filter.included_files,
                previous=previous,
            )
            current = dict(previous)
            for path in paths:
                entry = observed.get(path)
                if entry is None:
                    current.pop(path, None)
                else:
                    current[path] = entry
            changes = _observation_changes(previous, current, selected_paths=paths)
            self._advertised_entries = current
        return RepositoryProviderObservation(
            observed_at=datetime.now(UTC),
            entries=tuple(current.values()),
            changes=changes,
        )

    async def query(
        self, request: RepositoryPathQuery
    ) -> RepositoryProviderQueryObservation:
        async with self._poll_lock:
            result = await asyncio.to_thread(
                query_bounded_paths,
                root_path=self._binding.root_path,
                query=BoundedPathQuery(
                    prefixes=request.prefixes,
                    maximum_depth=request.maximum_depth,
                    maximum_entries=request.maximum_entries,
                    maximum_examined=request.maximum_examined,
                    suffixes=request.suffixes,
                ),
                include_files=self._index.scanner.filter.included_files,
                include_directory=self._index.scanner.filter.should_include_directory,
            )
        return RepositoryProviderQueryObservation(
            query_digest=request.query_digest,
            observed_at=datetime.now(UTC),
            entries=tuple(
                RepositorySnapshotEntry(
                    path=entry.path,
                    size_bytes=entry.size_bytes,
                    modified_ns=entry.modified_ns,
                )
                for entry in result.entries
            ),
            examined_count=result.examined_count,
            truncated=result.truncated,
            inaccessible_count=result.inaccessible_count,
        )

    async def close(self) -> None:
        return None


class FileSystemBackendObservationProvider:
    """Workspace adapter over an explicitly injected neutral FileSystem backend."""

    def __init__(
        self,
        *,
        binding: WorkspaceRepositoryBinding,
        backend_factory: Callable[[], ObservationBackend],
    ) -> None:
        self._binding = binding
        self._backend_factory = backend_factory
        self._backend: ObservationBackend | None = None
        self._last_backend_observation: BackendObservation | None = None
        self._last_provider_observation: RepositoryProviderObservation | None = None
        self._advertised_entries: dict[str, RepositorySnapshotEntry] | None = None
        self._poll_lock = asyncio.Lock()

    @property
    def root_path(self) -> Path:
        return self._binding.root_path

    @property
    def mode(self) -> ObservationBackendMode | None:
        return self._backend.mode if self._backend is not None else None

    @property
    def last_backend_observation(self) -> BackendObservation | None:
        return self._last_backend_observation

    async def initialize(self) -> RepositoryProviderObservation:
        async with self._poll_lock:
            if self._backend is not None:
                raise RuntimeError(
                    "FileSystem observation backend is already initialized"
                )
            backend = await asyncio.to_thread(self._backend_factory)
            try:
                result = await asyncio.to_thread(
                    backend.initialize,
                    "workspace-initialize",
                )
                observation = _workspace_backend_observation(
                    binding=self._binding,
                    result=result,
                    include_changes=False,
                )
            except BaseException:
                await asyncio.to_thread(backend.close)
                raise
            self._backend = backend
            self._last_backend_observation = result
            self._last_provider_observation = observation
            self._advertised_entries = {
                entry.path: entry for entry in observation.entries
            }
            return observation

    async def poll(self) -> RepositoryProviderObservation:
        async with self._poll_lock:
            backend = self._backend
            if backend is None:
                raise RuntimeError("FileSystem observation backend is not initialized")
            previous_backend = self._last_backend_observation
            previous_provider = self._last_provider_observation
            result = await asyncio.to_thread(backend.poll, "workspace-poll")
            if (
                previous_backend is not None
                and previous_provider is not None
                and result.snapshot is previous_backend.snapshot
                and _backend_report_has_no_changes(result.report)
            ):
                observation = previous_provider.reobserve_exact(datetime.now(UTC))
            else:
                candidate = _workspace_backend_observation(
                    binding=self._binding,
                    result=result,
                    include_changes=False,
                )
                previous = self._advertised_entries
                if previous is None:
                    raise RuntimeError(
                        "FileSystem observation backend is not initialized"
                    )
                current = {entry.path: entry for entry in candidate.entries}
                observation = RepositoryProviderObservation(
                    observed_at=candidate.observed_at,
                    entries=candidate.entries,
                    changes=_observation_changes(previous, current),
                )
            self._last_backend_observation = result
            self._last_provider_observation = observation
            self._advertised_entries = {
                entry.path: entry for entry in observation.entries
            }
            return observation

    async def observe_paths(
        self, paths: tuple[str, ...]
    ) -> RepositoryProviderObservation:
        """Advance backend-advertised state from bounded exact metadata reads."""

        async with self._poll_lock:
            previous = self._advertised_entries
            if previous is None:
                raise RuntimeError("FileSystem observation backend is not initialized")
            observed = await asyncio.to_thread(
                _observe_exact_path_entries,
                root_path=self._binding.root_path,
                paths=paths,
                include_files=None,
                previous=previous,
            )
            current = dict(previous)
            for path in paths:
                entry = observed.get(path)
                if entry is None:
                    current.pop(path, None)
                else:
                    current[path] = entry
            observation = RepositoryProviderObservation(
                observed_at=datetime.now(UTC),
                entries=tuple(current.values()),
                changes=_observation_changes(previous, current, selected_paths=paths),
            )
            self._advertised_entries = current
            self._last_provider_observation = observation
            return observation

    async def query(
        self, request: RepositoryPathQuery
    ) -> RepositoryProviderQueryObservation:
        async with self._poll_lock:
            result = await asyncio.to_thread(
                query_bounded_paths,
                root_path=self._binding.root_path,
                query=BoundedPathQuery(
                    prefixes=request.prefixes,
                    maximum_depth=request.maximum_depth,
                    maximum_entries=request.maximum_entries,
                    maximum_examined=request.maximum_examined,
                    suffixes=request.suffixes,
                ),
            )
        return RepositoryProviderQueryObservation(
            query_digest=request.query_digest,
            observed_at=datetime.now(UTC),
            entries=tuple(
                RepositorySnapshotEntry(
                    path=entry.path,
                    size_bytes=entry.size_bytes,
                    modified_ns=entry.modified_ns,
                )
                for entry in result.entries
            ),
            examined_count=result.examined_count,
            truncated=result.truncated,
            inaccessible_count=result.inaccessible_count,
        )

    async def close(self) -> None:
        async with self._poll_lock:
            backend = self._backend
            self._backend = None
            self._last_backend_observation = None
            self._last_provider_observation = None
            self._advertised_entries = None
            if backend is not None:
                await asyncio.to_thread(backend.close)


def _snapshot_entries(
    current: Mapping[str, FileMetadataCached],
) -> tuple[RepositorySnapshotEntry, ...]:
    return tuple(
        RepositorySnapshotEntry(
            path=path,
            size_bytes=metadata.size,
            modified_ns=metadata.mtime_ns,
            content_digest=(metadata.hash if metadata.hash_computed else None),
        )
        for path, metadata in sorted(current.items())
    )


def _observation_changes(
    previous: Mapping[str, RepositorySnapshotEntry],
    current: Mapping[str, RepositorySnapshotEntry],
    *,
    selected_paths: tuple[str, ...] | None = None,
) -> tuple[RepositoryObservationChange, ...]:
    paths = (
        set(previous) | set(current) if selected_paths is None else set(selected_paths)
    )
    changes: list[RepositoryObservationChange] = []
    for path in sorted(paths):
        before = previous.get(path)
        after = current.get(path)
        if before == after:
            continue
        if before is None and after is not None:
            changes.append(
                RepositoryObservationChange(
                    kind=ObservationChangeKind.CREATE,
                    path=path,
                    entry=after,
                )
            )
        elif before is not None and after is None:
            changes.append(
                RepositoryObservationChange(
                    kind=ObservationChangeKind.DELETE,
                    path=path,
                )
            )
        else:
            changes.append(
                RepositoryObservationChange(
                    kind=ObservationChangeKind.UPDATE,
                    path=path,
                    entry=after,
                )
            )
    return tuple(changes)


def _observe_exact_path_entries(
    *,
    root_path: Path,
    paths: tuple[str, ...],
    include_files: Callable[[tuple[str, ...]], set[str]] | None,
    previous: Mapping[str, RepositorySnapshotEntry],
) -> dict[str, RepositorySnapshotEntry]:
    candidates: dict[str, tuple[str, os.stat_result]] = {}
    for path in paths:
        relative = PurePosixPath(path)
        current = root_path
        metadata: os.stat_result | None = None
        try:
            for index, part in enumerate(relative.parts):
                current = current / part
                metadata = current.stat(follow_symlinks=False)
                if stat.S_ISLNK(metadata.st_mode):
                    metadata = None
                    break
                if index < len(relative.parts) - 1 and not stat.S_ISDIR(
                    metadata.st_mode
                ):
                    metadata = None
                    break
        except (FileNotFoundError, NotADirectoryError):
            metadata = None
        if metadata is None or not stat.S_ISREG(metadata.st_mode):
            continue
        candidates[path] = (str(current), metadata)

    if include_files is not None and candidates:
        included = include_files(tuple(value[0] for value in candidates.values()))
        candidates = {
            path: value for path, value in candidates.items() if value[0] in included
        }

    entries: dict[str, RepositorySnapshotEntry] = {}
    for path, (_absolute, metadata) in candidates.items():
        prior = previous.get(path)
        content_digest = (
            prior.content_digest
            if prior is not None
            and prior.size_bytes == metadata.st_size
            and prior.modified_ns == metadata.st_mtime_ns
            else None
        )
        entries[path] = RepositorySnapshotEntry(
            path=path,
            size_bytes=metadata.st_size,
            modified_ns=metadata.st_mtime_ns,
            content_digest=content_digest,
        )
    return entries


def _workspace_backend_observation(
    *,
    binding: WorkspaceRepositoryBinding,
    result: BackendObservation,
    include_changes: bool,
) -> RepositoryProviderObservation:
    snapshot_root = Path(result.snapshot.root_path).resolve()
    if snapshot_root != binding.root_path:
        raise ValueError(
            "FileSystem backend root does not match Workspace repository binding"
        )
    entries = tuple(
        RepositorySnapshotEntry(
            path=entry.path,
            size_bytes=entry.size,
            modified_ns=entry.mtime_ns,
        )
        for entry in result.snapshot.entries
    )
    if not include_changes:
        return RepositoryProviderObservation(
            observed_at=datetime.now(UTC),
            entries=entries,
        )
    entries_by_path = {entry.path: entry for entry in entries}
    changes: list[RepositoryObservationChange] = []
    for path in _report_paths(result.report, "added"):
        changes.append(
            RepositoryObservationChange(
                kind=ObservationChangeKind.CREATE,
                path=path,
                entry=_required_backend_entry(entries_by_path, path),
            )
        )
    for path in _report_paths(result.report, "modified"):
        changes.append(
            RepositoryObservationChange(
                kind=ObservationChangeKind.UPDATE,
                path=path,
                entry=_required_backend_entry(entries_by_path, path),
            )
        )
    for path in _report_paths(result.report, "deleted"):
        if path in entries_by_path:
            raise ValueError(f"Deleted FileSystem backend path remains present: {path}")
        changes.append(
            RepositoryObservationChange(
                kind=ObservationChangeKind.DELETE,
                path=path,
            )
        )
    return RepositoryProviderObservation(
        observed_at=datetime.now(UTC),
        entries=entries,
        changes=tuple(changes),
    )


def _report_paths(report: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = report.get(key)
    if not isinstance(value, list):
        return ()
    paths = tuple(str(item) for item in value)
    if len(paths) != len(set(paths)):
        raise ValueError(f"FileSystem backend report has duplicate {key} paths")
    return paths


def _backend_report_has_no_changes(report: Mapping[str, object]) -> bool:
    return not any(
        _report_paths(report, key) for key in ("added", "modified", "deleted")
    )


def _required_backend_entry(
    entries_by_path: Mapping[str, RepositorySnapshotEntry],
    path: str,
) -> RepositorySnapshotEntry:
    try:
        return entries_by_path[path]
    except KeyError as error:
        raise ValueError(
            f"FileSystem backend change lacks snapshot metadata: {path}"
        ) from error
