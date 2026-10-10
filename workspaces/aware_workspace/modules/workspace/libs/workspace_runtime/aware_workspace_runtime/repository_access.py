from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from pathlib import PurePosixPath
from typing import Any

from .contracts import (
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSnapshot,
)

WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF = "aware.workspace.repository-access.v1"
WORKSPACE_REPOSITORY_ACCESS_READINESS_CONTRACT_REF = (
    "aware.workspace.repository-access-readiness.v1"
)
WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF = (
    "aware.workspace.repository-path-search.v1"
)
WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF = (
    "aware.workspace.repository-visibility.canonical-source.v1"
)
DEFAULT_REPOSITORY_CHILD_PAGE_MAX_ENTRIES = 128
DEFAULT_REPOSITORY_PATH_SEARCH_MAX_RESULTS = 50
MAX_REPOSITORY_PATH_SEARCH_RESULTS = 100
MAX_REPOSITORY_PATH_SEARCH_EXAMINED = 100_000


class RepositoryEntryKind(StrEnum):
    DIRECTORY = "directory"
    REGULAR_FILE = "regular_file"


class RepositoryChildPosture(StrEnum):
    NONE = "none"
    AVAILABLE = "available"


class RepositorySourceReadPosture(StrEnum):
    UNAVAILABLE = "unavailable"
    AVAILABLE = "available"


class RepositoryAccessReadinessState(StrEnum):
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"


class RepositoryPathMatchKind(StrEnum):
    EXACT_NAME = "exact_name"
    NAME_PREFIX = "name_prefix"
    SEGMENT_PREFIX = "segment_prefix"
    SUBSTRING = "substring"
    SUBSEQUENCE = "subsequence"


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryAccessReadiness:
    preparation_ref: str
    workspace_grant_ref: str
    revision: int
    state: RepositoryAccessReadinessState
    descriptor: dict[str, Any] | None
    failure_code: str | None
    failure_message: str | None
    retryable: bool
    observe_after_milliseconds: int | None
    contract_ref: str = WORKSPACE_REPOSITORY_ACCESS_READINESS_CONTRACT_REF
    authority_kind: str = "local_uncommitted"

    def __post_init__(self) -> None:
        if (
            self.contract_ref != WORKSPACE_REPOSITORY_ACCESS_READINESS_CONTRACT_REF
            or self.authority_kind != "local_uncommitted"
            or not self.preparation_ref
            or not self.workspace_grant_ref
            or self.revision < 0
        ):
            raise ValueError("Repository readiness identity is invalid")
        if self.state is RepositoryAccessReadinessState.INITIALIZING:
            valid = (
                self.descriptor is None
                and self.failure_code is None
                and self.failure_message is None
                and not self.retryable
                and self.observe_after_milliseconds is not None
                and 1 <= self.observe_after_milliseconds <= 5_000
            )
        elif self.state is RepositoryAccessReadinessState.READY:
            valid = (
                self.descriptor is not None
                and self.failure_code is None
                and self.failure_message is None
                and not self.retryable
                and self.observe_after_milliseconds is None
            )
        else:
            valid = (
                self.descriptor is None
                and bool(self.failure_code)
                and bool(self.failure_message)
                and self.observe_after_milliseconds is None
            )
        if not valid:
            raise ValueError("Repository readiness fields diverge from state")

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_ref": self.contract_ref,
            "authority_kind": self.authority_kind,
            "preparation_ref": self.preparation_ref,
            "workspace_grant_ref": self.workspace_grant_ref,
            "revision": self.revision,
            "state": self.state.value,
            "descriptor": self.descriptor,
            "failure_code": self.failure_code,
            "failure_message": self.failure_message,
            "retryable": self.retryable,
            "observe_after_milliseconds": self.observe_after_milliseconds,
        }


@dataclass(frozen=True, slots=True)
class RepositoryObservationCoordinate:
    repository_binding_ref: str
    epoch: str
    cursor: int
    snapshot_digest: str
    visibility_policy_ref: str
    visibility_policy_version: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "repository_binding_ref": self.repository_binding_ref,
            "epoch": self.epoch,
            "cursor": self.cursor,
            "snapshot_digest": self.snapshot_digest,
            "visibility_policy_ref": self.visibility_policy_ref,
            "visibility_policy_version": self.visibility_policy_version,
        }


@dataclass(frozen=True, slots=True)
class RepositoryEntry:
    entry_ref: str
    parent_entry_ref: str | None
    path: str
    name: str
    kind: RepositoryEntryKind
    size_bytes: int | None
    modified_ns: int | None
    content_digest: str | None
    child_posture: RepositoryChildPosture
    source_read_posture: RepositorySourceReadPosture

    def to_payload(self) -> dict[str, Any]:
        return {
            "entry_ref": self.entry_ref,
            "parent_entry_ref": self.parent_entry_ref,
            "path": self.path,
            "name": self.name,
            "kind": self.kind.value,
            "size_bytes": self.size_bytes,
            "modified_ns": self.modified_ns,
            "content_digest": self.content_digest,
            "child_posture": self.child_posture.value,
            "source_read_posture": self.source_read_posture.value,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPathSearchRequest:
    query_ref: str
    query: str
    expected_coordinate: RepositoryObservationCoordinate
    continuation_ref: str | None = None
    maximum_results: int = DEFAULT_REPOSITORY_PATH_SEARCH_MAX_RESULTS
    maximum_examined: int = MAX_REPOSITORY_PATH_SEARCH_EXAMINED
    contract_ref: str = WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF

    def __post_init__(self) -> None:
        query_ref = self.query_ref.strip()
        query = self.query.strip().replace("\\", "/")
        if (
            self.contract_ref != WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF
            or not query_ref
            or len(query_ref) > 128
            or not query
            or len(query) > 256
            or self.maximum_results < 1
            or self.maximum_results > MAX_REPOSITORY_PATH_SEARCH_RESULTS
            or self.maximum_examined < self.maximum_results
            or self.maximum_examined > MAX_REPOSITORY_PATH_SEARCH_EXAMINED
            or (self.continuation_ref is not None and not self.continuation_ref)
        ):
            raise ValueError("Repository path search request is invalid")
        object.__setattr__(self, "query_ref", query_ref)
        object.__setattr__(self, "query", query)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPathSearchMatch:
    entry: RepositoryEntry
    score: int
    match_kind: RepositoryPathMatchKind

    def to_payload(self) -> dict[str, Any]:
        return {
            "entry": self.entry.to_payload(),
            "score": self.score,
            "match_kind": self.match_kind.value,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPathSearchPage:
    query_ref: str
    query: str
    coordinate: RepositoryObservationCoordinate
    examined_count: int
    matched_count: int
    returned_count: int
    continuation_ref: str | None
    next_continuation_ref: str | None
    incomplete: bool
    duration_microseconds: int
    matches: tuple[WorkspaceRepositoryPathSearchMatch, ...]
    contract_ref: str = WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF
    authority_kind: str = "local_uncommitted"

    @property
    def complete(self) -> bool:
        return self.next_continuation_ref is None and not self.incomplete

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_ref": self.contract_ref,
            "authority_kind": self.authority_kind,
            "query_ref": self.query_ref,
            "query": self.query,
            "coordinate": self.coordinate.to_payload(),
            "examined_count": self.examined_count,
            "matched_count": self.matched_count,
            "returned_count": self.returned_count,
            "continuation_ref": self.continuation_ref,
            "next_continuation_ref": self.next_continuation_ref,
            "complete": self.complete,
            "incomplete": self.incomplete,
            "duration_microseconds": self.duration_microseconds,
            "matches": [match.to_payload() for match in self.matches],
        }


def repository_coordinate(
    snapshot: WorkspaceRepositoryObservationSnapshot,
    binding: WorkspaceRepositoryBinding,
) -> RepositoryObservationCoordinate:
    binding_ref = binding.binding_key
    if binding_ref is None:  # guarded by WorkspaceRepositoryBinding itself
        raise ValueError("Workspace repository binding identity is unavailable")
    return RepositoryObservationCoordinate(
        repository_binding_ref=binding_ref,
        epoch=snapshot.epoch,
        cursor=snapshot.cursor,
        snapshot_digest=snapshot.snapshot_digest,
        visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
        visibility_policy_version=binding.filter_version,
    )


def repository_entry_ref(
    *,
    binding_ref: str,
    snapshot_digest: str,
    path: str,
    kind: RepositoryEntryKind,
) -> str:
    digest = hashlib.sha256()
    for value in (binding_ref, snapshot_digest, path, kind.value):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"repository-entry:{digest.hexdigest()}"


def repository_descriptor_payload(
    snapshot: WorkspaceRepositoryObservationSnapshot,
    binding: WorkspaceRepositoryBinding,
) -> dict[str, Any]:
    coordinate = repository_coordinate(snapshot, binding)
    root = _directory_entry(
        coordinate=coordinate,
        path="",
        name=binding.root_path.name or "repository",
        has_children=bool(snapshot.entries),
    )
    return {
        "contract_ref": WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF,
        "authority_kind": "local_uncommitted",
        "coordinate": coordinate.to_payload(),
        "root_entry": root.to_payload(),
        "observed_source_entry_count": len(snapshot.entries),
        "catalog_posture": "ready",
    }


def repository_children_page_payload(
    snapshot: WorkspaceRepositoryObservationSnapshot,
    binding: WorkspaceRepositoryBinding,
    *,
    parent_path: str,
    continuation_ref: str | None,
    limit: int,
) -> dict[str, Any]:
    if not 0 < limit <= DEFAULT_REPOSITORY_CHILD_PAGE_MAX_ENTRIES:
        raise ValueError("Repository child page limit must be from 1 through 128")
    parent = _directory_path(parent_path)
    coordinate = repository_coordinate(snapshot, binding)
    children = _direct_children(snapshot.entries, coordinate, parent)
    parent_name = binding.root_path.name or "repository"
    if parent:
        parent_name = PurePosixPath(parent).name
    parent_entry = _directory_entry(
        coordinate=coordinate,
        path=parent,
        name=parent_name,
        has_children=bool(children),
    )
    start = 0
    if continuation_ref is not None:
        if not continuation_ref:
            raise ValueError("Repository child continuation ref cannot be empty")
        matches = [
            index
            for index, entry in enumerate(children)
            if _child_continuation_ref(parent_entry.entry_ref, entry.entry_ref)
            == continuation_ref
        ]
        if len(matches) != 1:
            raise ValueError(
                "Repository child continuation is not present in the exact page set"
            )
        start = matches[0] + 1
    selected = children[start : start + limit]
    complete = start + len(selected) >= len(children)
    next_ref = None
    if not complete and selected:
        next_ref = _child_continuation_ref(
            parent_entry.entry_ref, selected[-1].entry_ref
        )
    return {
        "contract_ref": WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF,
        "authority_kind": "local_uncommitted",
        "coordinate": coordinate.to_payload(),
        "parent_entry_ref": parent_entry.entry_ref,
        "parent_path": parent,
        "child_count": len(children),
        "returned_count": len(selected),
        "continuation_ref": continuation_ref,
        "next_continuation_ref": next_ref,
        "complete": complete,
        "entries": [entry.to_payload() for entry in selected],
    }


def repository_path_search_page(
    snapshot: WorkspaceRepositoryObservationSnapshot,
    binding: WorkspaceRepositoryBinding,
    request: WorkspaceRepositoryPathSearchRequest,
) -> WorkspaceRepositoryPathSearchPage:
    started = time.perf_counter_ns()
    coordinate = repository_coordinate(snapshot, binding)
    if request.expected_coordinate != coordinate:
        raise ValueError("Workspace repository search coordinate is stale")
    query = request.query.casefold()
    examined = min(len(snapshot.entries), request.maximum_examined)
    ranked: list[
        tuple[int, str, str, RepositoryPathMatchKind, RepositorySnapshotEntry]
    ] = []
    for observed in snapshot.entries[:examined]:
        match = _path_match(query, observed.path)
        if match is None:
            continue
        score, kind = match
        ranked.append((-score, observed.path.casefold(), observed.path, kind, observed))
    ranked.sort(key=lambda value: (value[0], len(value[2]), value[1], value[2]))
    query_digest = _path_search_query_digest(request, coordinate)
    start = 0
    if request.continuation_ref is not None:
        for index, (_score, _folded, _path, _kind, observed) in enumerate(ranked):
            entry_ref = repository_entry_ref(
                binding_ref=coordinate.repository_binding_ref,
                snapshot_digest=coordinate.snapshot_digest,
                path=observed.path,
                kind=RepositoryEntryKind.REGULAR_FILE,
            )
            if (
                _path_search_continuation_ref(query_digest, entry_ref)
                == request.continuation_ref
            ):
                start = index + 1
                break
        else:
            raise ValueError("Repository path search continuation is stale")
    selected_ranked = ranked[start : start + request.maximum_results]
    selected = tuple(
        WorkspaceRepositoryPathSearchMatch(
            entry=_file_entry(
                coordinate=coordinate,
                observed=observed,
                parent_entry_ref=repository_entry_ref(
                    binding_ref=coordinate.repository_binding_ref,
                    snapshot_digest=coordinate.snapshot_digest,
                    path=PurePosixPath(observed.path).parent.as_posix()
                    if PurePosixPath(observed.path).parent.as_posix() != "."
                    else "",
                    kind=RepositoryEntryKind.DIRECTORY,
                ),
            ),
            score=-negative_score,
            match_kind=kind,
        )
        for negative_score, _folded, _path, kind, observed in selected_ranked
    )
    has_more = start + len(selected) < len(ranked)
    next_ref = (
        _path_search_continuation_ref(query_digest, selected[-1].entry.entry_ref)
        if has_more and selected
        else None
    )
    return WorkspaceRepositoryPathSearchPage(
        query_ref=request.query_ref,
        query=request.query,
        coordinate=coordinate,
        examined_count=examined,
        matched_count=len(ranked),
        returned_count=len(selected),
        continuation_ref=request.continuation_ref,
        next_continuation_ref=next_ref,
        incomplete=examined < len(snapshot.entries),
        duration_microseconds=(time.perf_counter_ns() - started) // 1_000,
        matches=selected,
    )


def _direct_children(
    entries: tuple[RepositorySnapshotEntry, ...],
    coordinate: RepositoryObservationCoordinate,
    parent_path: str,
) -> tuple[RepositoryEntry, ...]:
    prefix = f"{parent_path}/" if parent_path else ""
    directory_paths: set[str] = set()
    files: dict[str, RepositorySnapshotEntry] = {}
    parent_exists = parent_path == ""
    for observed in entries:
        if observed.path == parent_path:
            raise ValueError("Repository catalog parent is a regular file")
        if not observed.path.startswith(prefix):
            continue
        remainder = observed.path[len(prefix) :]
        if not remainder:
            continue
        parent_exists = True
        first, separator, _tail = remainder.partition("/")
        child_path = f"{prefix}{first}"
        if separator:
            directory_paths.add(child_path)
        else:
            files[child_path] = observed
    if not parent_exists:
        raise ValueError("Repository catalog parent is not present in the snapshot")
    parent_ref = repository_entry_ref(
        binding_ref=coordinate.repository_binding_ref,
        snapshot_digest=coordinate.snapshot_digest,
        path=parent_path,
        kind=RepositoryEntryKind.DIRECTORY,
    )
    children: list[RepositoryEntry] = []
    for path in directory_paths:
        children.append(
            _directory_entry(
                coordinate=coordinate,
                path=path,
                name=PurePosixPath(path).name,
                has_children=True,
                parent_entry_ref=parent_ref,
            )
        )
    for path, observed in files.items():
        children.append(
            _file_entry(
                coordinate=coordinate,
                observed=observed,
                parent_entry_ref=parent_ref,
            )
        )
    return tuple(
        sorted(
            children,
            key=lambda value: (
                0 if value.kind is RepositoryEntryKind.DIRECTORY else 1,
                value.name.casefold(),
                value.name,
            ),
        )
    )


def _directory_entry(
    *,
    coordinate: RepositoryObservationCoordinate,
    path: str,
    name: str,
    has_children: bool,
    parent_entry_ref: str | None = None,
) -> RepositoryEntry:
    return RepositoryEntry(
        entry_ref=repository_entry_ref(
            binding_ref=coordinate.repository_binding_ref,
            snapshot_digest=coordinate.snapshot_digest,
            path=path,
            kind=RepositoryEntryKind.DIRECTORY,
        ),
        parent_entry_ref=parent_entry_ref,
        path=path,
        name=name,
        kind=RepositoryEntryKind.DIRECTORY,
        size_bytes=None,
        modified_ns=None,
        content_digest=None,
        child_posture=(
            RepositoryChildPosture.AVAILABLE
            if has_children
            else RepositoryChildPosture.NONE
        ),
        source_read_posture=RepositorySourceReadPosture.UNAVAILABLE,
    )


def _file_entry(
    *,
    coordinate: RepositoryObservationCoordinate,
    observed: RepositorySnapshotEntry,
    parent_entry_ref: str,
) -> RepositoryEntry:
    return RepositoryEntry(
        entry_ref=repository_entry_ref(
            binding_ref=coordinate.repository_binding_ref,
            snapshot_digest=coordinate.snapshot_digest,
            path=observed.path,
            kind=RepositoryEntryKind.REGULAR_FILE,
        ),
        parent_entry_ref=parent_entry_ref,
        path=observed.path,
        name=PurePosixPath(observed.path).name,
        kind=RepositoryEntryKind.REGULAR_FILE,
        size_bytes=observed.size_bytes,
        modified_ns=observed.modified_ns,
        content_digest=observed.content_digest,
        child_posture=RepositoryChildPosture.NONE,
        source_read_posture=RepositorySourceReadPosture.AVAILABLE,
    )


def _path_match(query: str, path: str) -> tuple[int, RepositoryPathMatchKind] | None:
    folded_path = path.casefold()
    name = PurePosixPath(path).name.casefold()
    length_bonus = max(0, 100 - min(len(folded_path), 100))
    if name == query:
        return 1_000 + length_bonus, RepositoryPathMatchKind.EXACT_NAME
    if name.startswith(query):
        return 900 + length_bonus, RepositoryPathMatchKind.NAME_PREFIX
    if any(segment.startswith(query) for segment in folded_path.split("/")):
        return 800 + length_bonus, RepositoryPathMatchKind.SEGMENT_PREFIX
    if query in name or query in folded_path:
        return 700 + length_bonus, RepositoryPathMatchKind.SUBSTRING
    positions: list[int] = []
    cursor = 0
    for character in query:
        index = folded_path.find(character, cursor)
        if index < 0:
            return None
        positions.append(index)
        cursor = index + 1
    gap = positions[-1] - positions[0] + 1 - len(positions)
    adjacent = sum(1 for left, right in pairwise(positions) if right == left + 1)
    return (
        max(1, 400 + adjacent * 8 - gap + length_bonus),
        RepositoryPathMatchKind.SUBSEQUENCE,
    )


def _path_search_query_digest(
    request: WorkspaceRepositoryPathSearchRequest,
    coordinate: RepositoryObservationCoordinate,
) -> str:
    digest = hashlib.sha256()
    for value in (
        request.query_ref,
        request.query,
        coordinate.repository_binding_ref,
        coordinate.epoch,
        str(coordinate.cursor),
        coordinate.snapshot_digest,
        str(request.maximum_results),
        str(request.maximum_examined),
    ):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def _path_search_continuation_ref(query_digest: str, entry_ref: str) -> str:
    digest = hashlib.sha256(f"{query_digest}\n{entry_ref}".encode()).hexdigest()
    return f"repository-path-search-after:{digest}"


def _directory_path(value: str) -> str:
    if value == "":
        return value
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or path.as_posix() != normalized
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("Repository catalog parent must be a normalized relative path")
    return normalized


def _child_continuation_ref(parent_entry_ref: str, entry_ref: str) -> str:
    digest = hashlib.sha256(f"{parent_entry_ref}\n{entry_ref}".encode()).hexdigest()
    return f"repository-child-after:{digest}"
