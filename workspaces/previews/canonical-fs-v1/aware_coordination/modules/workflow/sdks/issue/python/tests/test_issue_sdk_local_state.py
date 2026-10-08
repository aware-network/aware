from __future__ import annotations

import multiprocessing
import os
import stat
from pathlib import Path

import pytest
from aware_file_system import local_json_state as storage
from aware_issue_sdk import (
    bootstrap_issue_state_from_doc,
    load_workflow_issue_state_store,
    local_state,
    resolve_repo_relative_path,
    stable_issue_id,
)


def test_sdk_compatibility_cache_uses_the_original_filesystem_owner():
    for name in storage.__all__:
        if name != "JsonDocument":
            assert getattr(local_state, name) is getattr(storage, name)


def test_sdk_invalid_cache_preserves_original_bytes(tmp_path: Path):
    state_path = tmp_path / "state.json"
    original = b'{"issues_by_id": {}} trailing'
    state_path.write_bytes(original)
    with pytest.raises(ValueError, match="Invalid issue-state JSON"):
        load_workflow_issue_state_store(state_path=state_path)
    assert state_path.read_bytes() == original


def test_sdk_late_durability_failure_retains_written_cache_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    state_path = tmp_path / "state.json"
    actual_fsync = storage.os.fsync
    actual_replace = storage.os.replace
    replacements = []

    def replace(source, target):
        replacements.append((source, target))
        actual_replace(source, target)

    def fsync(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("directory durability unconfirmed")
        actual_fsync(descriptor)

    monkeypatch.setattr(storage.os, "replace", replace)
    monkeypatch.setattr(storage.os, "fsync", fsync)
    store = local_state.WorkflowIssueStateStore()
    with pytest.raises(OSError, match="durability unconfirmed"):
        local_state.save_workflow_issue_state_store(state_path=state_path, store=store)
    assert len(replacements) == 1
    assert load_workflow_issue_state_store(state_path=state_path) == store


def _bootstrap_distinct_issue(repo_root: str, state_path: str, worker: int) -> None:
    root = Path(repo_root)
    issue_path = root / "docs" / "issues" / f"worker-{worker}.md"
    issue_path.write_text(
        "\n".join(
            [
                f"# Issue: Worker {worker}",
                "",
                f"- Tag: `fb/test/worker-{worker}`",
                "- Status: In Progress",
                f"- Owner: `codex-worker-{worker}`",
                "",
                "## Ownership Scope",
                f"- `workspaces/worker-{worker}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    bootstrap_issue_state_from_doc(
        repo_root=root,
        issue_doc_path=issue_path,
        state_path=Path(state_path),
    )


def test_issue_sdk_bootstraps_local_issue_state_from_markdown(tmp_path: Path) -> None:
    issue_path = tmp_path / "docs" / "issues" / "2026" / "05" / "07" / "fb.md"
    state_path = tmp_path / ".aware" / "workflow_issue" / "state.json"
    issue_path.parent.mkdir(parents=True)
    issue_path.write_text(
        "\n".join(
            [
                "# Issue: SDK state rail",
                "",
                "- Tag: `fb/2026-05-07/sdk-state-rail`",
                "- Status: In Progress",
                "- Owner: `codex-test`",
                "",
                "## Ownership Scope",
                "- `workspaces/aware_coordination/modules/workflow/sdks/issue`",
                "- `workspaces/aware_coordination/modules/social/sdks/social`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = bootstrap_issue_state_from_doc(
        repo_root=tmp_path,
        issue_doc_path=issue_path,
        state_path=state_path,
    )
    store = load_workflow_issue_state_store(state_path=state_path)
    entry = store.issues_by_id[str(result.issue_id)]

    assert result.issue_id == stable_issue_id(tag="fb/2026-05-07/sdk-state-rail")
    assert result.issue_tag == "fb/2026-05-07/sdk-state-rail"
    assert result.status_token == "in_progress"
    assert result.owner_session_id == "codex-test"
    assert result.ownership_scope == [
        "workspaces/aware_coordination/modules/workflow/sdks/issue",
        "workspaces/aware_coordination/modules/social/sdks/social",
    ]
    assert entry.title == "SDK state rail"


def test_issue_sdk_rejects_repo_relative_path_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Path escapes repo root"):
        resolve_repo_relative_path(repo_root=tmp_path, raw_path="../outside.md")


def test_issue_sdk_bootstrap_preserves_concurrent_distinct_issues(
    tmp_path: Path,
) -> None:
    issues_dir = tmp_path / "docs" / "issues"
    issues_dir.mkdir(parents=True)
    state_path = tmp_path / ".aware" / "workflow_issue" / "state.json"
    context = multiprocessing.get_context("spawn")
    workers = [
        context.Process(
            target=_bootstrap_distinct_issue,
            args=(str(tmp_path), str(state_path), worker),
        )
        for worker in range(8)
    ]

    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=20)
        assert worker.exitcode == 0

    store = load_workflow_issue_state_store(state_path=state_path)
    assert len(store.issues_by_id) == 8
    assert set(store.issue_id_by_tag) == {
        f"fb/test/worker-{worker}" for worker in range(8)
    }
