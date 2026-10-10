from datetime import UTC, datetime
from pathlib import Path

import pytest
from aware_workspace_runtime import (
    WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF,
    WORKSPACE_REPOSITORY_ACCESS_READINESS_CONTRACT_REF,
    WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
    RepositoryAccessReadinessState,
    RepositoryEntryKind,
    RepositorySnapshotEntry,
    WorkspaceRepositoryAccessReadiness,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSnapshot,
    repository_children_page_payload,
    repository_descriptor_payload,
    repository_entry_ref,
    repository_snapshot_digest,
)
from aware_workspace_runtime.repository_access import (
    WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF,
    RepositoryPathMatchKind,
    WorkspaceRepositoryPathSearchRequest,
    repository_coordinate,
    repository_path_search_page,
)


def test_repository_readiness_is_strict_and_progress_free() -> None:
    readiness = WorkspaceRepositoryAccessReadiness(
        preparation_ref="repository-preparation:opaque",
        workspace_grant_ref="workspace-grant:opaque",
        revision=0,
        state=RepositoryAccessReadinessState.INITIALIZING,
        descriptor=None,
        failure_code=None,
        failure_message=None,
        retryable=False,
        observe_after_milliseconds=50,
    )

    assert readiness.to_payload() == {
        "contract_ref": WORKSPACE_REPOSITORY_ACCESS_READINESS_CONTRACT_REF,
        "authority_kind": "local_uncommitted",
        "preparation_ref": "repository-preparation:opaque",
        "workspace_grant_ref": "workspace-grant:opaque",
        "revision": 0,
        "state": "initializing",
        "descriptor": None,
        "failure_code": None,
        "failure_message": None,
        "retryable": False,
        "observe_after_milliseconds": 50,
    }
    with pytest.raises(ValueError, match="diverge"):
        WorkspaceRepositoryAccessReadiness(
            preparation_ref="repository-preparation:opaque",
            workspace_grant_ref="workspace-grant:opaque",
            revision=0,
            state=RepositoryAccessReadinessState.READY,
            descriptor=None,
            failure_code=None,
            failure_message=None,
            retryable=False,
            observe_after_milliseconds=None,
        )


def _snapshot(
    binding: WorkspaceRepositoryBinding,
    entries: tuple[RepositorySnapshotEntry, ...],
    *,
    cursor: int = 0,
) -> WorkspaceRepositoryObservationSnapshot:
    binding_ref = binding.binding_key
    assert binding_ref is not None
    return WorkspaceRepositoryObservationSnapshot(
        binding_key=binding_ref,
        epoch="epoch-1",
        cursor=cursor,
        observed_at=datetime.now(UTC),
        snapshot_digest=repository_snapshot_digest(entries),
        entries=entries,
    )


def _entry(path: str, size: int = 1) -> RepositorySnapshotEntry:
    return RepositorySnapshotEntry(path=path, size_bytes=size, modified_ns=size)


def test_descriptor_is_minimal_exact_and_visibility_versioned(tmp_path: Path) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    snapshot = _snapshot(binding, (_entry("README.md"), _entry("src/main.py")))

    descriptor = repository_descriptor_payload(snapshot, binding)

    assert descriptor["contract_ref"] == WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF
    assert descriptor["coordinate"] == {
        "repository_binding_ref": binding.binding_key,
        "epoch": "epoch-1",
        "cursor": 0,
        "snapshot_digest": snapshot.snapshot_digest,
        "visibility_policy_ref": WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
        "visibility_policy_version": "canonical-source-v1",
    }
    assert descriptor["observed_source_entry_count"] == 2
    assert "entries" not in descriptor
    root = descriptor["root_entry"]
    assert root["path"] == ""
    assert root["kind"] == "directory"
    assert root["child_posture"] == "available"


def test_child_pages_synthesize_directories_and_use_opaque_continuation(
    tmp_path: Path,
) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    snapshot = _snapshot(
        binding,
        (
            _entry("z.txt"),
            _entry("docs/guide.md"),
            _entry("src/main.py"),
            _entry("README.md"),
            _entry("src/nested/tool.py"),
        ),
    )

    first = repository_children_page_payload(
        snapshot,
        binding,
        parent_path="",
        continuation_ref=None,
        limit=2,
    )

    assert [value["name"] for value in first["entries"]] == ["docs", "src"]
    assert [value["kind"] for value in first["entries"]] == [
        "directory",
        "directory",
    ]
    continuation = first["next_continuation_ref"]
    assert isinstance(continuation, str)
    assert "src" not in continuation
    assert first["complete"] is False

    second = repository_children_page_payload(
        snapshot,
        binding,
        parent_path="",
        continuation_ref=continuation,
        limit=2,
    )
    assert [value["name"] for value in second["entries"]] == ["README.md", "z.txt"]
    assert second["complete"] is True
    assert second["next_continuation_ref"] is None


def test_nested_children_and_entry_refs_are_snapshot_scoped(tmp_path: Path) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    first_snapshot = _snapshot(
        binding, (_entry("src/main.py"), _entry("src/nested/tool.py"))
    )
    page = repository_children_page_payload(
        first_snapshot,
        binding,
        parent_path="src",
        continuation_ref=None,
        limit=10,
    )
    assert [value["name"] for value in page["entries"]] == ["nested", "main.py"]

    old_ref = repository_entry_ref(
        binding_ref=str(binding.binding_key),
        snapshot_digest=first_snapshot.snapshot_digest,
        path="src/main.py",
        kind=RepositoryEntryKind.REGULAR_FILE,
    )
    next_snapshot = _snapshot(
        binding,
        (_entry("src/main.py", 2), _entry("src/nested/tool.py")),
        cursor=1,
    )
    new_ref = repository_entry_ref(
        binding_ref=str(binding.binding_key),
        snapshot_digest=next_snapshot.snapshot_digest,
        path="src/main.py",
        kind=RepositoryEntryKind.REGULAR_FILE,
    )
    assert new_ref != old_ref


def test_large_repository_catalog_page_remains_bounded(tmp_path: Path) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    entries = tuple(_entry(f"files/file-{index:05}.txt") for index in range(10_000))
    snapshot = _snapshot(binding, entries)

    page = repository_children_page_payload(
        snapshot,
        binding,
        parent_path="files",
        continuation_ref=None,
        limit=128,
    )

    assert page["child_count"] == 10_000
    assert page["returned_count"] == 128
    assert len(page["entries"]) == 128
    assert page["complete"] is False
    assert page["next_continuation_ref"].startswith("repository-child-after:")


def test_path_search_is_ranked_and_reuses_tree_entry_identity(tmp_path: Path) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    snapshot = _snapshot(
        binding,
        (
            _entry("docs/guide.md"),
            _entry("src/guided_reader.dart"),
            _entry("guide.md"),
            _entry("packages/ui/src/grid.dart"),
        ),
    )
    page = repository_path_search_page(
        snapshot,
        binding,
        WorkspaceRepositoryPathSearchRequest(
            query_ref="repository-query:1",
            query="guide.md",
            expected_coordinate=repository_coordinate(snapshot, binding),
        ),
    )

    assert page.contract_ref == WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF
    assert [match.entry.path for match in page.matches] == [
        "guide.md",
        "docs/guide.md",
    ]
    assert all(
        match.match_kind is RepositoryPathMatchKind.EXACT_NAME for match in page.matches
    )
    tree = repository_children_page_payload(
        snapshot,
        binding,
        parent_path="",
        continuation_ref=None,
        limit=10,
    )
    tree_entry = next(entry for entry in tree["entries"] if entry["path"] == "guide.md")
    assert page.matches[0].entry.entry_ref == tree_entry["entry_ref"]
    assert page.coordinate == repository_coordinate(snapshot, binding)


def test_path_search_pages_with_opaque_query_bound_continuation(
    tmp_path: Path,
) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    snapshot = _snapshot(
        binding,
        tuple(_entry(f"src/tool-{index}.dart") for index in range(5)),
    )
    coordinate = repository_coordinate(snapshot, binding)
    first = repository_path_search_page(
        snapshot,
        binding,
        WorkspaceRepositoryPathSearchRequest(
            query_ref="repository-query:2",
            query="tool",
            expected_coordinate=coordinate,
            maximum_results=2,
        ),
    )

    assert first.returned_count == 2
    assert first.matched_count == 5
    assert first.next_continuation_ref is not None
    assert "tool" not in first.next_continuation_ref
    assert first.complete is False

    second = repository_path_search_page(
        snapshot,
        binding,
        WorkspaceRepositoryPathSearchRequest(
            query_ref="repository-query:2",
            query="tool",
            expected_coordinate=coordinate,
            continuation_ref=first.next_continuation_ref,
            maximum_results=2,
        ),
    )
    assert second.continuation_ref == first.next_continuation_ref
    assert [match.entry.path for match in first.matches] != [
        match.entry.path for match in second.matches
    ]

    with pytest.raises(ValueError, match="continuation is stale"):
        repository_path_search_page(
            snapshot,
            binding,
            WorkspaceRepositoryPathSearchRequest(
                query_ref="repository-query:changed",
                query="tool",
                expected_coordinate=coordinate,
                continuation_ref=first.next_continuation_ref,
                maximum_results=2,
            ),
        )


def test_path_search_rejects_stale_observation_coordinate(tmp_path: Path) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    first = _snapshot(binding, (_entry("src/main.py"),))
    second = _snapshot(binding, (_entry("src/main.py", 2),), cursor=1)

    with pytest.raises(ValueError, match="coordinate is stale"):
        repository_path_search_page(
            second,
            binding,
            WorkspaceRepositoryPathSearchRequest(
                query_ref="repository-query:stale",
                query="main",
                expected_coordinate=repository_coordinate(first, binding),
            ),
        )


def test_path_search_reports_bounded_incomplete_scan(tmp_path: Path) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    snapshot = _snapshot(
        binding,
        tuple(_entry(f"files/file-{index:05}.txt") for index in range(10_000)),
    )
    page = repository_path_search_page(
        snapshot,
        binding,
        WorkspaceRepositoryPathSearchRequest(
            query_ref="repository-query:bounded",
            query="file",
            expected_coordinate=repository_coordinate(snapshot, binding),
            maximum_results=25,
            maximum_examined=250,
        ),
    )

    assert page.examined_count == 250
    assert page.matched_count == 250
    assert page.returned_count == 25
    assert page.incomplete is True
    assert page.complete is False
    assert page.duration_microseconds >= 0


def test_path_search_large_catalog_materializes_only_bounded_page(
    tmp_path: Path,
) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    snapshot = _snapshot(
        binding,
        tuple(
            _entry(f"packages/pkg-{index:05}/lib/search_target.dart")
            for index in range(100_000)
        ),
    )

    page = repository_path_search_page(
        snapshot,
        binding,
        WorkspaceRepositoryPathSearchRequest(
            query_ref="repository-query:performance",
            query="search_target",
            expected_coordinate=repository_coordinate(snapshot, binding),
            maximum_results=50,
            maximum_examined=100_000,
        ),
    )

    assert page.examined_count == 100_000
    assert page.matched_count == 100_000
    assert page.returned_count == 50
    assert len(page.matches) == 50
    assert page.duration_microseconds < 2_000_000


@pytest.mark.parametrize("parent", ["missing", "src/main.py", "../src", "/src"])
def test_child_page_rejects_unknown_file_or_unconfined_parent(
    tmp_path: Path, parent: str
) -> None:
    binding = WorkspaceRepositoryBinding(tmp_path)
    snapshot = _snapshot(binding, (_entry("src/main.py"),))
    with pytest.raises(ValueError):
        repository_children_page_payload(
            snapshot,
            binding,
            parent_path=parent,
            continuation_ref=None,
            limit=10,
        )
