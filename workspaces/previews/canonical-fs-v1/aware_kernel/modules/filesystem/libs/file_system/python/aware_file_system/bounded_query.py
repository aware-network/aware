"""Confined, bounded metadata queries over an admitted repository root.

This module deliberately owns no cache, watcher, journal, or product-specific
projection.  It is the FileSystem traversal primitive used by the single
Workspace repository authority when a consumer needs less than a full index.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True, slots=True)
class BoundedPathQuery:
    prefixes: tuple[str, ...]
    maximum_depth: int
    maximum_entries: int
    maximum_examined: int
    suffixes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        prefixes = tuple(sorted({_relative_prefix(value) for value in self.prefixes}))
        suffixes = tuple(sorted({_suffix(value) for value in self.suffixes}))
        if not prefixes:
            raise ValueError("Bounded path query requires at least one prefix")
        if self.maximum_depth < 0:
            raise ValueError("Bounded path query maximum depth cannot be negative")
        if self.maximum_entries <= 0:
            raise ValueError("Bounded path query maximum entries must be positive")
        if self.maximum_examined < self.maximum_entries:
            raise ValueError(
                "Bounded path query examination budget must cover its entry budget"
            )
        object.__setattr__(self, "prefixes", prefixes)
        object.__setattr__(self, "suffixes", suffixes)


@dataclass(frozen=True, slots=True)
class BoundedPathMetadata:
    path: str
    size_bytes: int
    modified_ns: int


@dataclass(frozen=True, slots=True)
class BoundedPathQueryResult:
    entries: tuple[BoundedPathMetadata, ...]
    examined_count: int
    truncated: bool
    inaccessible_count: int


def query_bounded_paths(
    *,
    root_path: Path,
    query: BoundedPathQuery,
    include_file: Callable[[str], bool] | None = None,
    include_files: Callable[[tuple[str, ...]], set[str]] | None = None,
    include_directory: Callable[[str], bool] | None = None,
) -> BoundedPathQueryResult:
    """Return deterministic regular-file metadata without following symlinks."""

    root = root_path.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Repository root must be an existing directory: {root}")
    entries: dict[str, BoundedPathMetadata] = {}
    absolute_paths: dict[str, str] = {}
    examined = 0
    inaccessible = 0
    truncated = False

    for prefix in query.prefixes:
        prefix_path = root.joinpath(*PurePosixPath(prefix).parts)
        try:
            prefix_stat = prefix_path.stat(follow_symlinks=False)
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError:
            inaccessible += 1
            continue
        if os.path.islink(prefix_path):
            continue
        if not os.path.isdir(prefix_path):
            examined += 1
            if examined > query.maximum_examined:
                truncated = True
                break
            if (
                os.path.isfile(prefix_path)
                and _matches_suffix(prefix, query.suffixes)
                and (include_file is None or include_file(str(prefix_path)))
            ):
                entries[prefix] = BoundedPathMetadata(
                    path=prefix,
                    size_bytes=prefix_stat.st_size,
                    modified_ns=prefix_stat.st_mtime_ns,
                )
                absolute_paths[prefix] = str(prefix_path)
            continue

        pending: list[tuple[Path, str, int]] = [(prefix_path, prefix, 0)]
        while pending:
            directory, relative_directory, depth = pending.pop()
            try:
                children = sorted(
                    os.scandir(directory),
                    key=lambda value: (value.name.casefold(), value.name),
                    reverse=True,
                )
            except OSError:
                inaccessible += 1
                continue
            for child in children:
                examined += 1
                if examined > query.maximum_examined:
                    truncated = True
                    break
                child_relative = f"{relative_directory}/{child.name}"
                try:
                    if child.is_symlink():
                        continue
                    if child.is_dir(follow_symlinks=False):
                        child_depth = depth + 1
                        if child_depth < query.maximum_depth and (
                            include_directory is None or include_directory(child.path)
                        ):
                            pending.append(
                                (Path(child.path), child_relative, child_depth)
                            )
                        continue
                    if not child.is_file(follow_symlinks=False):
                        continue
                    file_depth = depth + 1
                    if file_depth > query.maximum_depth or not _matches_suffix(
                        child.name, query.suffixes
                    ):
                        continue
                    if include_file is not None and not include_file(child.path):
                        continue
                    metadata = child.stat(follow_symlinks=False)
                except OSError:
                    inaccessible += 1
                    continue
                entries[child_relative] = BoundedPathMetadata(
                    path=child_relative,
                    size_bytes=metadata.st_size,
                    modified_ns=metadata.st_mtime_ns,
                )
                absolute_paths[child_relative] = child.path
                if include_files is None and len(entries) >= query.maximum_entries:
                    truncated = True
                    break
            if truncated:
                break
        if truncated:
            break

    if include_files is not None:
        included_absolute = include_files(tuple(absolute_paths.values()))
        entries = {
            path: entry
            for path, entry in entries.items()
            if absolute_paths[path] in included_absolute
        }
    ordered_paths = sorted(entries)
    if len(ordered_paths) > query.maximum_entries:
        ordered_paths = ordered_paths[: query.maximum_entries]
        truncated = True
    return BoundedPathQueryResult(
        entries=tuple(entries[path] for path in ordered_paths),
        examined_count=examined,
        truncated=truncated,
        inaccessible_count=inaccessible,
    )


def _relative_prefix(value: str) -> str:
    normalized = value.strip().replace("\\", "/").rstrip("/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or path.as_posix() != normalized
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"Bounded query prefix must be relative: {value!r}")
    return normalized


def _suffix(value: str) -> str:
    normalized = value.strip()
    if not normalized or "/" in normalized or "\\" in normalized:
        raise ValueError(f"Bounded query suffix is invalid: {value!r}")
    return normalized


def _matches_suffix(value: str, suffixes: tuple[str, ...]) -> bool:
    return not suffixes or value.endswith(suffixes)
