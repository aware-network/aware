from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import aware_workspace_operator.commit as commit_module
import pytest
from aware_workspace_operator.commit import (
    _RESIDENT_PROVIDER_TOKEN,
    _authorized_commit_request_fingerprint,
    _git_mutation_lock,
    _GitCommandResult,
    _ResidentCommitAdmissionGrant,
    _ResidentRepositoryCommitProvider,
    _validate_authorized_path_states,
    run_workspace_authorized_commit,
    run_workspace_commit,
    run_workspace_content_commit,
    verify_repository_commit_receipt,
)
from aware_workspace_operator.models import (
    ResidentCommitAdmissionEvidence,
    WorkspaceAuthorizedCommitOptions,
    WorkspaceAuthorizedPathState,
    WorkspaceCommitIssueMetadata,
    WorkspaceCommitOptions,
    WorkspaceContentCommitOptions,
    WorkspaceSuppliedPathContent,
)


@dataclass(frozen=True)
class _GitExpectation:
    args: tuple[str, ...]
    cwd: Path
    result: _GitCommandResult


class _FakeGitRunner:
    def __init__(self, expectations: list[_GitExpectation]) -> None:
        self._expectations = list(expectations)
        self.calls: list[tuple[str, ...]] = []

    def run(self, *, args: tuple[str, ...], cwd: Path) -> _GitCommandResult:
        self.calls.append(args)
        if not self._expectations:
            raise AssertionError(f"Unexpected git call: {args}")
        expected = self._expectations.pop(0)
        assert args == expected.args
        assert cwd == expected.cwd
        return expected.result

    def assert_complete(self) -> None:
        assert not self._expectations, (
            f"Unconsumed expectations: {self._expectations!r}"
        )


def _hold_git_mutation_lock_until_released(
    repo_root_text: str,
    ready: multiprocessing.synchronize.Event,
    release: multiprocessing.synchronize.Event,
) -> None:
    with _git_mutation_lock(
        repo_root=Path(repo_root_text),
        owner_id="codex-lock-holder",
        issue_tag="fb/2026-02-13/holder",
        command_summary="test lock holder",
    ):
        ready.set()
        release.wait(timeout=10)


def _write_issue(
    *,
    repo_root: Path,
    issue_relpath: str,
    owner: str = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    status: str = "In Progress",
    ownership_scope: str = "`owned`",
) -> Path:
    issue_path = repo_root / issue_relpath
    issue_path.parent.mkdir(parents=True, exist_ok=True)
    issue_path.write_text(
        (
            "# Issue: test\n\n"
            "- Slug: `test`\n"
            "- Tag: `fb/2026-02-13/test`\n"
            f"- Status: {status}\n"
            f"- Owner: `{owner}`\n"
            f"- Ownership Scope: {ownership_scope}\n"
        ),
        encoding="utf-8",
    )
    return issue_path


def _write_repo_file(repo_root: Path, relpath: str, content: str = "x\n") -> Path:
    file_path = repo_root / relpath
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _expected_message(*, issue_relpath: str, owner: str) -> str:
    return (
        "ship scoped change\n\n"
        "Issue-Tag: fb/2026-02-13/test\n"
        f"Issue-Path: {issue_relpath}\n"
        f"Owner: {owner}\n"
        "Owned-Paths: owned/file.py"
    )


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    )


def _real_repository(tmp_path: Path) -> tuple[Path, str, str]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init", "-b", "main")
    _git(repo_root, "config", "user.name", "Aware Test")
    _git(repo_root, "config", "user.email", "aware-test@example.invalid")
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="before\n")
    _git(repo_root, "add", "owned/file.py")
    _git(repo_root, "commit", "-m", "seed")
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)
    return repo_root, issue_relpath, owner


def _reject_reference_update(repo_root: Path, *, exit_code: int) -> None:
    hook = repo_root / ".git/hooks/reference-transaction"
    hook.write_text(f"#!/bin/sh\nexit {exit_code}\n", encoding="utf-8")
    hook.chmod(0o755)


def test_repository_commit_receipt_requires_reachable_commit(tmp_path: Path) -> None:
    repo_root, _issue_relpath, _owner = _real_repository(tmp_path)
    reachable = _git(repo_root, "rev-parse", "HEAD").stdout.strip()

    assert (
        verify_repository_commit_receipt(
            repo_root=repo_root,
            publication_receipt_ref=f"git:{reachable}",
        )
        == f"git:{reachable}"
    )
    with pytest.raises(ValueError, match="publication_receipt_issue_mismatch"):
        verify_repository_commit_receipt(
            repo_root=repo_root,
            publication_receipt_ref=f"git:{reachable}",
            expected_issue_ref="fb/2026-02-13/test",
        )

    with pytest.raises(ValueError, match="publication_receipt_malformed"):
        verify_repository_commit_receipt(
            repo_root=repo_root,
            publication_receipt_ref="commit:not-a-git-receipt",
        )
    with pytest.raises(ValueError, match="publication_receipt_commit_absent"):
        verify_repository_commit_receipt(
            repo_root=repo_root,
            publication_receipt_ref="git:" + "a" * 40,
        )


def test_repository_commit_receipt_rejects_unreachable_commit(tmp_path: Path) -> None:
    repo_root, _issue_relpath, _owner = _real_repository(tmp_path)
    tree = _git(repo_root, "rev-parse", "HEAD^{tree}").stdout.strip()
    orphan = subprocess.run(
        ("git", "commit-tree", tree, "-m", "unreachable"),
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Aware Test",
            "GIT_AUTHOR_EMAIL": "aware-test@example.invalid",
            "GIT_COMMITTER_NAME": "Aware Test",
            "GIT_COMMITTER_EMAIL": "aware-test@example.invalid",
        },
    ).stdout.strip()

    with pytest.raises(ValueError, match="publication_receipt_not_reachable"):
        verify_repository_commit_receipt(
            repo_root=repo_root,
            publication_receipt_ref=f"git:{orphan}",
        )


def test_content_supplied_commit_ignores_dirty_worktree_and_replays(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _git(repo_root, "add", issue_relpath)
    _git(repo_root, "commit", "-m", "admit issue")
    expected_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    expected_blob = _git(
        repo_root, "rev-parse", f"{expected_head}:owned/file.py"
    ).stdout.strip()
    expected_issue_blob = _git(
        repo_root, "rev-parse", f"{expected_head}:{issue_relpath}"
    ).stdout.strip()
    _write_repo_file(
        repo_root=repo_root,
        relpath="owned/file.py",
        content="foreign dirty worktree\n",
    )
    options = WorkspaceContentCommitOptions(
        repo_root=repo_root,
        issue_path=issue_relpath,
        path_contents=(
            WorkspaceSuppliedPathContent(
                path="owned/file.py",
                expected_head_blob_oid=expected_blob,
                content_text="supplied postimage\n",
            ),
        ),
        message="publish supplied postimage",
        owner_id=owner,
        expected_head=expected_head,
        expected_repository_ref="refs/heads/main",
        expected_issue_blob_oid=expected_issue_blob,
        semantic_intent_digest="sha256:" + "a" * 64,
        idempotency_ref="goal-mutation:test-content",
    )

    outcome = run_workspace_content_commit(options=options)

    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.reference_update == "cas_applied"
    assert outcome.report.transaction_mode == "isolated_index_atomic_ref_v1"
    assert outcome.report.staged_paths == ["owned/file.py"]
    assert outcome.report.committed_issue_blob_oid == expected_issue_blob
    assert all(call[:2] != ["git", "add"] for call in outcome.report.command_log)
    assert (
        _git(repo_root, "show", "HEAD:owned/file.py").stdout == "supplied postimage\n"
    )
    assert (repo_root / "owned/file.py").read_text() == "foreign dirty worktree\n"

    replay = run_workspace_content_commit(options=options)

    assert replay.exit_code == 0
    assert replay.report.idempotent_replay is True
    assert replay.report.commit_hash == outcome.report.commit_hash


def test_content_supplied_commit_preserves_foreign_staged_target(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _git(repo_root, "add", issue_relpath)
    _git(repo_root, "commit", "-m", "admit issue")
    expected_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    expected_blob = _git(
        repo_root, "rev-parse", f"{expected_head}:owned/file.py"
    ).stdout.strip()
    _write_repo_file(
        repo_root=repo_root, relpath="owned/file.py", content="foreign staged\n"
    )
    _git(repo_root, "add", "owned/file.py")
    staged_blob = _git(repo_root, "rev-parse", ":owned/file.py").stdout.strip()

    outcome = run_workspace_content_commit(
        options=WorkspaceContentCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            path_contents=(
                WorkspaceSuppliedPathContent(
                    path="owned/file.py",
                    expected_head_blob_oid=expected_blob,
                    content_text="published postimage\n",
                ),
            ),
            message="preserve foreign staging",
            owner_id=owner,
            expected_head=expected_head,
            expected_repository_ref="refs/heads/main",
            semantic_intent_digest="sha256:" + "d" * 64,
            idempotency_ref="goal-mutation:test-foreign-stage",
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.reference_update == "cas_applied"
    assert outcome.report.shared_index_projection == "failed"
    assert (
        outcome.report.shared_index_projection_error
        == "foreign_staged_content_preserved"
    )
    assert _git(repo_root, "rev-parse", ":owned/file.py").stdout.strip() == staged_blob
    assert (
        _git(repo_root, "show", "HEAD:owned/file.py").stdout == "published postimage\n"
    )


def test_content_supplied_commit_of_new_path_leaves_shared_projection_clean(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _git(repo_root, "add", issue_relpath)
    _git(repo_root, "commit", "-m", "admit issue")
    expected_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()

    outcome = run_workspace_content_commit(
        options=WorkspaceContentCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            path_contents=(
                WorkspaceSuppliedPathContent(
                    path="owned/new-file.py",
                    expected_head_blob_oid=None,
                    content_text="new committed content\n",
                ),
            ),
            message="publish new supplied path",
            owner_id=owner,
            expected_head=expected_head,
            expected_repository_ref="refs/heads/main",
            semantic_intent_digest="sha256:" + "f" * 64,
            idempotency_ref="goal-mutation:test-new-path-projection",
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.shared_index_projection == "applied"
    assert _git(repo_root, "diff", "--cached", "--name-only").stdout == ""
    assert _git(repo_root, "status", "--short", "--", "owned/new-file.py").stdout == (
        " D owned/new-file.py\n"
    )
    assert (
        _git(repo_root, "show", "HEAD:owned/new-file.py").stdout
        == "new committed content\n"
    )


def test_workspace_commit_of_new_path_leaves_index_and_worktree_clean(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(
        repo_root=repo_root,
        relpath="owned/new-file.py",
        content="new worktree content\n",
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/new-file.py",),
            message="publish new worktree path",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.shared_index_projection == "applied"
    assert _git(repo_root, "status", "--short", "--", "owned/new-file.py").stdout == ""
    assert _git(repo_root, "diff", "--cached", "--name-only").stdout == ""


def test_content_supplied_commit_detects_index_advance_before_atomic_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _git(repo_root, "add", issue_relpath)
    _git(repo_root, "commit", "-m", "admit issue")
    expected_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    expected_blob = _git(
        repo_root, "rev-parse", f"{expected_head}:owned/file.py"
    ).stdout.strip()
    original_check = commit_module._shared_index_matches_expected_paths
    advanced = False

    def advance_after_check(**kwargs: object) -> bool:
        nonlocal advanced
        matched = original_check(**kwargs)  # type: ignore[arg-type]
        if kwargs.get("environment") is not None or advanced:
            return matched
        advanced = True
        _write_repo_file(
            repo_root=repo_root, relpath="owned/file.py", content="foreign staged\n"
        )
        _git(repo_root, "add", "owned/file.py")
        return matched

    monkeypatch.setattr(
        commit_module, "_shared_index_matches_expected_paths", advance_after_check
    )

    outcome = run_workspace_content_commit(
        options=WorkspaceContentCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            path_contents=(
                WorkspaceSuppliedPathContent(
                    path="owned/file.py",
                    expected_head_blob_oid=expected_blob,
                    content_text="published postimage\n",
                ),
            ),
            message="detect index race",
            owner_id=owner,
            expected_head=expected_head,
            expected_repository_ref="refs/heads/main",
            semantic_intent_digest="sha256:" + "e" * 64,
            idempotency_ref="goal-mutation:test-index-race",
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.reference_update == "cas_applied"
    assert outcome.report.shared_index_projection == "failed"
    assert outcome.report.shared_index_projection_error == "shared_index_advanced"
    assert _git(repo_root, "show", ":owned/file.py").stdout == "foreign staged\n"


def _projection_options(
    repo: Path, issue: str, owner: str, *, key: str, content: str,
    path: str = "owned/file.py",
) -> WorkspaceContentCommitOptions:
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    entry = _git(repo, "ls-tree", head, "--", path).stdout.split()
    return WorkspaceContentCommitOptions(
        repo_root=repo, issue_path=issue,
        path_contents=(WorkspaceSuppliedPathContent(
            path=path, expected_head_blob_oid=entry[2] if entry else None,
            content_text=content,
        ),),
        message="projection regression " + key, owner_id=owner,
        expected_head=head, expected_repository_ref="refs/heads/main",
        semantic_intent_digest="sha256:" + hashlib.sha256(key.encode()).hexdigest(),
        idempotency_ref="projection-regression:" + key,
    )


@pytest.mark.parametrize("advance", ["unrelated", "metadata"])
def test_projection_preserves_latest_unrelated_entries_and_metadata_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, advance: str,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    original = commit_module._project_shared_index_atomically

    def advance_index(**kwargs: object) -> str | None:
        if advance == "unrelated":
            _write_repo_file(repo, "foreign.txt", "foreign staged\n")
            _git(repo, "add", "foreign.txt")
        else:
            file = repo / "owned/file.py"
            details = file.stat()
            os.utime(file, ns=(details.st_atime_ns, details.st_mtime_ns + 2_000_000_000))
            _git(repo, "update-index", "--refresh")
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(commit_module, "_project_shared_index_atomically", advance_index)
    outcome = run_workspace_content_commit(options=_projection_options(
        repo, issue, owner, key=advance, content="published\n",
    ))
    assert outcome.exit_code == 0
    assert outcome.report.shared_index_projection == "applied"
    assert _git(repo, "show", ":owned/file.py").stdout == "published\n"
    if advance == "unrelated":
        assert _git(repo, "show", ":foreign.txt").stdout == "foreign staged\n"


@pytest.mark.parametrize("recovery", ["next_publication", "restart_replay"])
@pytest.mark.parametrize("path", ["owned/file.py", "owned/new.py"])
def test_projection_debt_recovers_after_publication_and_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recovery: str, path: str,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    options = _projection_options(repo, issue, owner, key="deferred", content="first\n", path=path)
    with monkeypatch.context() as patch:
        patch.setattr(commit_module, "_project_shared_index_atomically", lambda **kwargs: "shared_index_lock_busy")
        first = run_workspace_content_commit(options=options)
    assert first.exit_code == 0
    assert first.report.shared_index_projection_error == "shared_index_lock_busy"
    debt_root = repo / ".git/aware-transactions"
    assert tuple(debt_root.glob("index-projection-*.json"))
    if recovery == "next_publication":
        # A distinct owner may advance HEAD without touching these paths.
        _write_repo_file(repo, "foreign.txt", "other owner\n")
        _git(repo, "add", "foreign.txt")
        _git(repo, "commit", "-m", "other owner publication")
        second = run_workspace_content_commit(options=_projection_options(
            repo, issue, owner, key="successor", content="second\n", path=path,
        ))
        assert second.exit_code == 0
        assert second.report.shared_index_projection == "applied"
        expected = "second\n"
    else:
        # The new process has no in-memory transaction or supplied recovery state.
        result = subprocess.run(
            [sys.executable, "-c", (
                "import json,sys; from aware_workspace_operator.models import WorkspaceContentCommitOptions; "
                "from aware_workspace_operator.commit import run_workspace_content_commit; "
                "r=run_workspace_content_commit(options=WorkspaceContentCommitOptions.model_validate_json(sys.argv[1])); "
                "print(r.report.model_dump_json()); sys.exit(r.exit_code)"
            ), options.model_dump_json()],
            cwd=repo, capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": str(Path(commit_module.__file__).parent.parent)},
        )
        assert result.returncode == 0, result.stderr + result.stdout
        report = json.loads(result.stdout)
        assert report["idempotent_replay"] is True
        assert report["commit_hash"] == first.report.commit_hash
        assert report["shared_index_projection"] == "applied"
        assert _git(repo, "rev-parse", "HEAD").stdout.strip() == first.report.commit_hash
        expected = "first\n"
    assert _git(repo, "show", ":" + path).stdout == expected
    assert not tuple(debt_root.glob("index-projection-*.json"))


def test_projection_debt_never_overwrites_foreign_staging_or_reauthorizes_consumed_debt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    options = _projection_options(repo, issue, owner, key="deferred", content="first\n")
    with monkeypatch.context() as patch:
        patch.setattr(commit_module, "_project_shared_index_atomically", lambda **kwargs: "shared_index_lock_busy")
        first = run_workspace_content_commit(options=options)
    assert first.exit_code == 0
    _write_repo_file(repo, "owned/file.py", "foreign staged\n")
    _git(repo, "add", "owned/file.py")
    refused = run_workspace_content_commit(options=options)
    assert refused.exit_code == 0  # publication replay is still successful
    assert refused.report.shared_index_projection_error == "foreign_staged_content_preserved"
    assert _git(repo, "show", ":owned/file.py").stdout == "foreign staged\n"
    _write_repo_file(repo, "owned/file.py", "before\n")
    _git(repo, "add", "owned/file.py")
    recovered = run_workspace_content_commit(options=options)
    assert recovered.report.shared_index_projection == "applied"
    # Once satisfied, the old receipt cannot authorize newly staged old bytes.
    _git(repo, "add", "owned/file.py")
    second = run_workspace_content_commit(options=_projection_options(
        repo, issue, owner, key="second", content="second\n",
    ))
    assert second.report.shared_index_projection_error == "foreign_staged_content_preserved"
    assert _git(repo, "show", ":owned/file.py").stdout == "before\n"


@pytest.mark.parametrize("invalid", ["unreachable", "changed_postimage", "unproven", "wrong_parent", "missing_object"])
def test_projection_recovery_requires_exact_published_debt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: str,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    options = _projection_options(repo, issue, owner, key="first", content="first\n")
    with monkeypatch.context() as patch:
        patch.setattr(commit_module, "_project_shared_index_atomically", lambda **kwargs: "shared_index_lock_busy")
        first = run_workspace_content_commit(options=options)
    assert first.exit_code == 0
    debt_path, = (repo / ".git/aware-transactions").glob("index-projection-*.json")
    if invalid == "missing_object":
        payload = json.loads(debt_path.read_text())
        payload["candidate_commit"] = "1" * 40
        debt_path.write_text(json.dumps(payload))
    elif invalid == "unreachable":
        payload = json.loads(debt_path.read_text())
        payload["candidate_commit"] = _git(repo, "commit-tree", _git(repo, "rev-parse", "HEAD^{tree}").stdout.strip(), "-m", "unreachable").stdout.strip()
        debt_path.write_text(json.dumps(payload))
    elif invalid == "wrong_parent":
        payload = json.loads(debt_path.read_text())
        payload["expected_head"] = first.report.commit_hash
        debt_path.write_text(json.dumps(payload))
    elif invalid == "changed_postimage":
        changed = run_workspace_content_commit(options=_projection_options(
            repo, issue, owner, key="changed", content="changed\n",
        ))
        assert changed.report.shared_index_projection == "applied"
        # Restore a stale, now inapplicable record and preimage.
        payload = {"schema_version": "aware.repository-index-projection.v2", "candidate_commit": first.report.commit_hash,
                   "expected_head": options.expected_head, "reference": "refs/heads/main", "paths": ["owned/file.py"],
                   "preimage_heads": {"owned/file.py": options.expected_head}}
        debt_path.write_text(json.dumps(payload))
        _git(repo, "add", "owned/file.py")
    else:
        debt_path.unlink()
    second = run_workspace_content_commit(options=_projection_options(
        repo, issue, owner, key="second", content="second\n",
    ))
    assert second.exit_code == 0
    assert second.report.shared_index_projection_error == "foreign_staged_content_preserved"
    assert _git(repo, "show", ":owned/file.py").stdout == "before\n"


def test_authorized_commit_replay_repairs_deferred_projection_without_new_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, owner = _real_repository(tmp_path)
    _write_repo_file(repo, "owned/file.py", "authorized postimage\n")
    options = WorkspaceAuthorizedCommitOptions(
        repo_root=repo, target_paths=("owned/file.py",), message="authorized recovery",
        owner_id=owner, idempotency_ref="authorized:projection-recovery",
    )
    with monkeypatch.context() as patch:
        patch.setattr(commit_module, "_project_shared_index_atomically", lambda **kwargs: "shared_index_lock_busy")
        first = run_workspace_authorized_commit(options=options)
    assert first.exit_code == 0
    second = run_workspace_authorized_commit(options=options)
    assert second.exit_code == 0
    assert second.report.idempotent_replay is True
    assert second.report.commit_hash == first.report.commit_hash
    assert second.report.shared_index_projection == "applied"
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == first.report.commit_hash
    assert _git(repo, "show", ":owned/file.py").stdout == "authorized postimage\n"


def test_projection_carries_original_preimage_through_multiple_deferred_publications(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    with monkeypatch.context() as patch:
        patch.setattr(commit_module, "_project_shared_index_atomically", lambda **kwargs: "shared_index_lock_busy")
        first = run_workspace_content_commit(options=_projection_options(
            repo, issue, owner, key="first", content="first\n",
        ))
        assert first.exit_code == 0
        options = _projection_options(repo, issue, owner, key="second", content="second\n")
        second = run_workspace_content_commit(options=options)
        assert second.exit_code == 0
    assert _git(repo, "show", ":owned/file.py").stdout == "before\n"
    recovered = run_workspace_content_commit(options=options)
    assert recovered.exit_code == 0
    assert recovered.report.shared_index_projection == "applied"
    assert recovered.report.commit_hash == second.report.commit_hash
    assert _git(repo, "show", ":owned/file.py").stdout == "second\n"
    assert not tuple((repo / ".git/aware-transactions").glob("index-projection-*.json"))


def test_projection_lock_refusal_retains_native_lock_and_releases_own_lock_on_error(
    tmp_path: Path,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    options = _projection_options(repo, issue, owner, key="busy", content="first\n")
    lock = repo / ".git/index.lock"
    lock.write_text("other writer lock\n")
    first = run_workspace_content_commit(options=options)
    assert first.exit_code == 0
    assert first.report.shared_index_projection_error == "shared_index_lock_busy"
    assert lock.read_text() == "other writer lock\n"
    lock.unlink()
    recovered = run_workspace_content_commit(options=options)
    assert recovered.report.shared_index_projection == "applied"
    assert not lock.exists()


def test_projection_recovers_after_process_exit_between_reference_cas_and_projection(
    tmp_path: Path,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    options = _projection_options(repo, issue, owner, key="crash", content="after crash\n")
    result = subprocess.run(
        [sys.executable, "-c", (
            "import os,sys; import aware_workspace_operator.commit as m; "
            "from aware_workspace_operator.models import WorkspaceContentCommitOptions; "
            "m._project_shared_index_atomically=lambda **kwargs: os._exit(73); "
            "m.run_workspace_content_commit(options=WorkspaceContentCommitOptions.model_validate_json(sys.argv[1]))"
        ), options.model_dump_json()],
        cwd=repo, capture_output=True, text=True, check=False,
        env={**os.environ, "PYTHONPATH": str(Path(commit_module.__file__).parent.parent)},
    )
    assert result.returncode == 73, result.stderr
    committed = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert _git(repo, "show", "HEAD:owned/file.py").stdout == "after crash\n"
    assert _git(repo, "show", ":owned/file.py").stdout == "before\n"
    recovered = run_workspace_content_commit(options=options)
    assert recovered.exit_code == 0
    assert recovered.report.idempotent_replay is True
    assert recovered.report.commit_hash == committed
    assert recovered.report.shared_index_projection == "applied"
    assert _git(repo, "show", ":owned/file.py").stdout == "after crash\n"


def test_projection_cleanup_cannot_remove_a_successor_writers_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    lock = repo / ".git/index.lock"
    original_replace = os.replace

    def successor_lock(source: object, destination: object) -> None:
        original_replace(source, destination)  # type: ignore[arg-type]
        if Path(str(destination)) == repo / ".git/index":
            lock.write_text("successor writer\n")

    monkeypatch.setattr(os, "replace", successor_lock)
    outcome = run_workspace_content_commit(options=_projection_options(
        repo, issue, owner, key="successor-lock", content="published\n",
    ))
    assert outcome.exit_code == 0
    assert outcome.report.shared_index_projection == "applied"
    assert lock.read_text() == "successor writer\n"


@pytest.mark.parametrize("crash_at", ["before_replace", "after_replace"])
@pytest.mark.parametrize("path", ["owned/file.py", "owned/new.py"])
def test_consumed_projection_debt_cannot_overwrite_later_staging_after_crash(
    tmp_path: Path, crash_at: str, path: str,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    options = _projection_options(repo, issue, owner, key="spent-debt", content="published\n", path=path)
    script = """
import os
import sys
from pathlib import Path
import aware_workspace_operator.commit as module
from aware_workspace_operator.models import WorkspaceContentCommitOptions

original_replace = os.replace
index = Path.cwd() / '.git/index'
mode = sys.argv[2]

def crash_replace(source, destination):
    if Path(destination) == index:
        if mode == 'before_replace':
            os._exit(73)
        original_replace(source, destination)
        os._exit(74)
    return original_replace(source, destination)

os.replace = crash_replace
module.run_workspace_content_commit(
    options=WorkspaceContentCommitOptions.model_validate_json(sys.argv[1])
)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, options.model_dump_json(), crash_at],
        cwd=repo, text=True, capture_output=True, check=False,
        env={**os.environ, "PYTHONPATH": str(Path(commit_module.__file__).parent.parent)},
    )
    assert result.returncode == (73 if crash_at == "before_replace" else 74), result.stderr
    committed = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert _git(repo, "show", "HEAD:" + path).stdout == "published\n"
    debt_root = repo / ".git/aware-transactions"
    assert not tuple(debt_root.glob("index-projection-*.json"))
    if crash_at == "before_replace":
        # The dead process's native lock needs explicit reconciliation too.
        lock = repo / ".git/index.lock"
        assert lock.is_file()
        lock.unlink()
    # A new staged edit may deliberately equal the original preimage, including
    # an absent preimage for a newly committed path. Spent debt cannot admit it.
    if not _git(repo, "ls-files", "--", path).stdout:
        blob = _git(repo, "rev-parse", "HEAD:" + path).stdout.strip()
        _git(repo, "update-index", "--add", "--cacheinfo", "100644", blob, path)
    _git(repo, "restore", "--staged", "--source=" + options.expected_head, "--", path)
    _write_repo_file(repo, "foreign.txt", "foreign staging\n")
    _git(repo, "add", "foreign.txt")
    entries = _git(repo, "ls-files", "--stage").stdout
    replay = run_workspace_content_commit(options=options)
    assert replay.exit_code == 0
    assert replay.report.idempotent_replay is True
    assert replay.report.commit_hash == committed
    assert replay.report.shared_index_projection_error == "foreign_staged_content_preserved"
    assert _git(repo, "ls-files", "--stage").stdout == entries
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == committed


def test_authorized_detached_head_replay_repairs_only_index_and_preserves_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, owner = _real_repository(tmp_path)
    _git(repo, "checkout", "--detach", "HEAD")
    _write_repo_file(repo, "owned/file.py", "detached postimage\n")
    options = WorkspaceAuthorizedCommitOptions(
        repo_root=repo, target_paths=("owned/file.py",), message="detached recovery",
        owner_id=owner, idempotency_ref="authorized:detached-projection-recovery",
    )
    with monkeypatch.context() as patch:
        patch.setattr(commit_module, "_project_shared_index_atomically", lambda **kwargs: "shared_index_lock_busy")
        first = run_workspace_authorized_commit(options=options)
    assert first.exit_code == 0
    assert first.report.updated_reference == "HEAD"
    _write_repo_file(repo, "foreign.txt", "foreign staging\n")
    _git(repo, "add", "foreign.txt")
    replay = run_workspace_authorized_commit(options=options)
    assert replay.exit_code == 0
    assert replay.report.idempotent_replay is True
    assert replay.report.commit_hash == first.report.commit_hash
    assert replay.report.shared_index_projection == "applied"
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == first.report.commit_hash
    assert _git(repo, "show", ":owned/file.py").stdout == "detached postimage\n"
    assert _git(repo, "show", ":foreign.txt").stdout == "foreign staging\n"


def test_legacy_v1_debt_cannot_authorize_restaged_preimage(
    tmp_path: Path,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    options = _projection_options(repo, issue, owner, key="legacy-debt", content="published\n")
    first = run_workspace_content_commit(options=options)
    assert first.exit_code == 0
    assert first.report.shared_index_projection == "applied"
    debt_path = repo / ".git/aware-transactions/index-projection-legacy.json"
    debt_path.write_text(json.dumps({
        "schema_version": "aware.repository-index-projection.v1",
        "candidate_commit": first.report.commit_hash,
        "expected_head": options.expected_head,
        "reference": "refs/heads/main",
        "paths": ["owned/file.py"],
        "preimage_heads": {"owned/file.py": options.expected_head},
    }))
    _git(repo, "add", "owned/file.py")
    entries = _git(repo, "ls-files", "--stage").stdout
    replay = run_workspace_content_commit(options=options)
    assert replay.exit_code == 0
    assert replay.report.shared_index_projection_error == "foreign_staged_content_preserved"
    assert _git(repo, "ls-files", "--stage").stdout == entries
    assert debt_path.is_file()  # no invented migration or cleanup of legacy debt


def test_projection_preserves_unmerged_entries_and_ignores_malformed_debt(
    tmp_path: Path,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    blob = _git(repo, "rev-parse", "HEAD:owned/file.py").stdout.strip()
    subprocess.run(
        ["git", "update-index", "--index-info"], cwd=repo, check=True,
        input=(f"0 {'0' * 40}\towned/file.py\n"
               f"100644 {blob} 1\towned/file.py\n"
               f"100644 {blob} 2\towned/file.py\n"),
        text=True, capture_output=True,
    )
    entries = _git(repo, "ls-files", "--stage").stdout
    debt_root = repo / ".git/aware-transactions"
    debt_root.mkdir()
    (debt_root / "index-projection-broken.json").write_text('{"broken":')
    outcome = run_workspace_content_commit(options=_projection_options(
        repo, issue, owner, key="unmerged", content="published\n",
    ))
    assert outcome.exit_code == 0
    assert outcome.report.shared_index_projection_error == "foreign_staged_content_preserved"
    assert _git(repo, "ls-files", "--stage").stdout == entries


@pytest.mark.parametrize("path", ["owned/file with spaces.py", "owned/new.py"])
def test_projection_handles_exact_paths_and_preserves_partial_debt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str,
) -> None:
    repo, issue, owner = _real_repository(tmp_path)
    _git(repo, "add", issue)
    _git(repo, "commit", "-m", "admit issue")
    first_options = _projection_options(repo, issue, owner, key="first", content="first\n")
    first_options = first_options.model_copy(update={"path_contents": (
        *first_options.path_contents,
        WorkspaceSuppliedPathContent(path=path, expected_head_blob_oid=None, content_text="new\n"),
    )})
    with monkeypatch.context() as patch:
        patch.setattr(commit_module, "_project_shared_index_atomically", lambda **kwargs: "shared_index_lock_busy")
        first = run_workspace_content_commit(options=first_options)
    assert first.exit_code == 0
    next_options = _projection_options(repo, issue, owner, key="next", content="second\n")
    next_commit = run_workspace_content_commit(options=next_options)
    assert next_commit.report.shared_index_projection == "applied"
    debt, = (repo / ".git/aware-transactions").glob("index-projection-*.json")
    assert json.loads(debt.read_text())["paths"] == [path]
    recovered = run_workspace_content_commit(options=first_options)
    assert recovered.report.shared_index_projection == "applied"
    # Recovery projects current HEAD, not the historical replay's older file.
    assert _git(repo, "show", ":owned/file.py").stdout == "second\n"
    assert _git(repo, "show", ":" + path).stdout == "new\n"
    assert not tuple((repo / ".git/aware-transactions").glob("index-projection-*.json"))


def test_content_supplied_replay_must_be_reachable_from_target_ref(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _git(repo_root, "add", issue_relpath)
    _git(repo_root, "commit", "-m", "admit issue")
    expected_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    expected_blob = _git(
        repo_root, "rev-parse", f"{expected_head}:owned/file.py"
    ).stdout.strip()
    options = WorkspaceContentCommitOptions(
        repo_root=repo_root,
        issue_path=issue_relpath,
        path_contents=(
            WorkspaceSuppliedPathContent(
                path="owned/file.py",
                expected_head_blob_oid=expected_blob,
                content_text="published postimage\n",
            ),
        ),
        message="publish reachable operation",
        owner_id=owner,
        expected_head=expected_head,
        expected_repository_ref="refs/heads/main",
        semantic_intent_digest="sha256:" + "e" * 64,
        idempotency_ref="goal-mutation:test-reachability",
    )
    published = run_workspace_content_commit(options=options)
    assert published.exit_code == 0
    assert published.report.commit_hash is not None
    _git(repo_root, "branch", "archive", published.report.commit_hash)
    _git(repo_root, "reset", "--hard", expected_head)

    replay = run_workspace_content_commit(options=options)

    assert replay.exit_code == 2
    assert "idempotent_commit_not_reachable" in str(replay.report.error)
    assert _git(repo_root, "rev-parse", "HEAD").stdout.strip() == expected_head


def test_content_supplied_commit_rejects_stale_head_blob_without_mutation(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _git(repo_root, "add", issue_relpath)
    _git(repo_root, "commit", "-m", "admit issue")
    expected_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    initial_index = (repo_root / ".git/index").read_bytes()

    outcome = run_workspace_content_commit(
        options=WorkspaceContentCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            path_contents=(
                WorkspaceSuppliedPathContent(
                    path="owned/file.py",
                    expected_head_blob_oid="0" * 40,
                    content_text="must not land\n",
                ),
            ),
            message="reject stale preimage",
            owner_id=owner,
            expected_head=expected_head,
            expected_repository_ref="refs/heads/main",
            semantic_intent_digest="sha256:" + "b" * 64,
            idempotency_ref="goal-mutation:test-stale",
        )
    )

    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert "repository_head_path_stale" in str(outcome.report.error)
    assert _git(repo_root, "rev-parse", "HEAD").stdout.strip() == expected_head
    assert (repo_root / ".git/index").read_bytes() == initial_index


def test_content_supplied_commit_rejects_advanced_issue_revision(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _git(repo_root, "add", issue_relpath)
    _git(repo_root, "commit", "-m", "admit issue")
    before_issue_blob = _git(
        repo_root, "rev-parse", f"HEAD:{issue_relpath}"
    ).stdout.strip()
    issue_path = repo_root / issue_relpath
    issue_path.write_text(
        issue_path.read_text(encoding="utf-8") + "- Concurrent authority update.\n",
        encoding="utf-8",
    )
    _git(repo_root, "add", issue_relpath)
    _git(repo_root, "commit", "-m", "advance issue authority")
    expected_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    expected_blob = _git(
        repo_root, "rev-parse", f"{expected_head}:owned/file.py"
    ).stdout.strip()

    outcome = run_workspace_content_commit(
        options=WorkspaceContentCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            path_contents=(
                WorkspaceSuppliedPathContent(
                    path="owned/file.py",
                    expected_head_blob_oid=expected_blob,
                    content_text="must not land\n",
                ),
            ),
            message="reject advanced Issue",
            owner_id=owner,
            expected_head=expected_head,
            expected_repository_ref="refs/heads/main",
            expected_issue_blob_oid=before_issue_blob,
            semantic_intent_digest="sha256:" + "c" * 64,
            idempotency_ref="goal-mutation:test-issue-stale",
        )
    )

    assert outcome.exit_code == 2
    assert "committed_issue_revision_stale" in str(outcome.report.error)
    assert _git(repo_root, "rev-parse", "HEAD").stdout.strip() == expected_head


def test_real_commit_failed_ref_cas_leaves_shared_index_and_head_unchanged(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")
    _reject_reference_update(repo_root, exit_code=41)
    initial_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    initial_index = (repo_root / ".git/index").read_bytes()

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="attempt guarded commit",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.repository_write_preflight == "passed"
    assert outcome.report.staged_paths == ["owned/file.py"]
    assert outcome.report.index_restored is True
    assert outcome.report.transaction_mode == "isolated_index_atomic_ref_v1"
    assert outcome.report.reference_update == "cas_failed"
    assert outcome.report.shared_index_unchanged is True
    assert outcome.report.shared_index_projection == "not_run"
    assert (repo_root / ".git/index").read_bytes() == initial_index
    assert _git(repo_root, "rev-parse", "HEAD").stdout.strip() == initial_head
    assert _git(repo_root, "diff", "--cached", "--name-only").stdout == ""
    assert _git(repo_root, "diff", "--name-only").stdout == "owned/file.py\n"


def test_real_commit_permission_preflight_fails_before_staging(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")
    head_log = repo_root / ".git/logs/HEAD"
    head_log.chmod(0o444)
    initial_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    initial_index = (repo_root / ".git/index").read_bytes()

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="permission preflight",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.repository_write_preflight == "failed"
    assert outcome.report.staged_paths == []
    assert outcome.report.index_restored is None
    assert outcome.report.reference_update == "not_run"
    assert outcome.report.error
    assert "repository_metadata_not_writable" in outcome.report.error
    assert ".git/logs/HEAD" in outcome.report.error
    assert (repo_root / ".git/index").read_bytes() == initial_index
    assert _git(repo_root, "rev-parse", "HEAD").stdout.strip() == initial_head
    assert _git(repo_root, "diff", "--cached", "--name-only").stdout == ""


def test_real_commit_success_records_preflight_without_cleanup(tmp_path: Path) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="successful guarded commit",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.repository_write_preflight == "passed"
    assert outcome.report.index_restored is None
    assert outcome.report.reference_update == "cas_applied"
    assert outcome.report.shared_index_projection == "applied"
    assert outcome.report.staged_paths == ["owned/file.py"]
    assert _git(repo_root, "status", "--short", "--", "owned/file.py").stdout == ""


def test_real_commit_rejects_stale_issue_source_digest_before_staging(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")
    initial_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    initial_index = (repo_root / ".git/index").read_bytes()

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="reject stale issue authority",
            owner_id=owner,
            expected_issue_source_sha256="sha256:" + "0" * 64,
        )
    )

    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.error is not None
    assert outcome.report.error.startswith("issue_source_digest_stale:")
    assert outcome.report.staged_paths == []
    assert (repo_root / ".git/index").read_bytes() == initial_index
    assert _git(repo_root, "rev-parse", "HEAD").stdout.strip() == initial_head


def test_real_authorized_commit_failed_ref_cas_uses_isolated_index(
    tmp_path: Path,
) -> None:
    repo_root, _issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")
    _reject_reference_update(repo_root, exit_code=42)
    initial_index = (repo_root / ".git/index").read_bytes()

    outcome = run_workspace_authorized_commit(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=("owned/file.py",),
            message="attempt authorized guarded commit",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 2
    assert outcome.report.repository_write_preflight == "passed"
    assert outcome.report.staged_paths == ["owned/file.py"]
    assert outcome.report.index_restored is True
    assert outcome.report.reference_update == "cas_failed"
    assert outcome.report.shared_index_unchanged is True
    assert (repo_root / ".git/index").read_bytes() == initial_index
    assert _git(repo_root, "diff", "--cached", "--name-only").stdout == ""


def _resident_evidence() -> ResidentCommitAdmissionEvidence:
    return ResidentCommitAdmissionEvidence(
        generation_owner_ref="development-generation:1",
        repository_operation_ref="repository-operation:one",
        actor_ref="actor:agent-one",
        agent_ref="agent:one",
        human_sponsor_ref="identity:luis",
        dev_session_ref="dev-session:one",
        work_context_ref="work-context:one",
        issue_revision_ref="issue:one:revision:2",
        workspace_session_ref="workspace-session:one",
        source_effect_policy="provider_native_compatibility",
        provider_source_admission_digests=("sha256:" + "a" * 64,),
    )


def test_resident_commit_atomically_publishes_exact_admission_ref(
    tmp_path: Path,
) -> None:
    repo_root, _issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")
    provider = _ResidentRepositoryCommitProvider(
        _RESIDENT_PROVIDER_TOKEN,
        "development-generation:1",
        (tmp_path / "resident-journals").resolve(),
    )

    outcome = provider(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=("owned/file.py",),
            message="resident admitted commit",
            owner_id=owner,
            idempotency_ref="repository-commit:resident-one",
            resident_admission_evidence=_resident_evidence(),
        )
    )

    assert outcome.exit_code == 0, outcome.report.error
    admission_ref = outcome.report.repository_admission_ref
    evidence_digest = outcome.report.repository_admission_evidence_digest
    commit_hash = outcome.report.commit_hash
    assert admission_ref is not None
    assert evidence_digest is not None
    assert commit_hash is not None
    assert admission_ref.startswith(
        "refs/aware/repository-admissions/v1/" + commit_hash
    )
    object_id = _git(repo_root, "rev-parse", admission_ref).stdout.strip()
    evidence = _git(repo_root, "cat-file", "blob", object_id).stdout
    assert hashlib.sha256(evidence.encode()).hexdigest() == evidence_digest[7:]
    assert len(tuple((tmp_path / "resident-journals").glob("*.json"))) == 1
    assert len(tuple((tmp_path / "resident-journals").glob("*.complete"))) == 1
    provider.close()


def test_compatibility_commit_cannot_create_resident_admission(
    tmp_path: Path,
) -> None:
    repo_root, _issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")

    outcome = run_workspace_authorized_commit(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=("owned/file.py",),
            message="compatibility commit remains held",
            owner_id=owner,
            idempotency_ref="repository-commit:compatibility-one",
            resident_admission_evidence=_resident_evidence(),
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.repository_admission_ref is None
    assert (
        _git(
            repo_root,
            "for-each-ref",
            "--format=%(refname)",
            "refs/aware/repository-admissions/v1",
        ).stdout
        == ""
    )


def test_resident_issuer_and_grant_are_not_caller_constructible(
    tmp_path: Path,
) -> None:
    provider = _ResidentRepositoryCommitProvider(
        _RESIDENT_PROVIDER_TOKEN,
        "development-generation:1",
        (tmp_path / "resident-journals").resolve(),
    )

    with pytest.raises(TypeError, match="constructor_private"):
        _ResidentCommitAdmissionGrant()
    with pytest.raises(RuntimeError, match="issuer_unavailable"):
        provider._issue({"schema": "forged"})
    provider.close()


def test_real_detached_head_commit_has_complete_write_preflight(tmp_path: Path) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _git(repo_root, "checkout", "--detach")
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="detached guarded commit",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.repository_write_preflight == "passed"
    assert outcome.report.staged_paths == ["owned/file.py"]


def test_real_commit_preserves_foreign_shared_index_entries(tmp_path: Path) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="foreign/file.py", content="before\n")
    _git(repo_root, "add", "foreign/file.py")
    _git(repo_root, "commit", "-m", "seed foreign")
    _write_repo_file(repo_root=repo_root, relpath="foreign/file.py", content="staged\n")
    _git(repo_root, "add", "foreign/file.py")
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="publish without absorbing foreign stage",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.reference_update == "cas_applied"
    assert _git(repo_root, "diff", "--cached", "--name-only").stdout == (
        "foreign/file.py\n"
    )
    assert _git(repo_root, "show", "--format=", "--name-only", "HEAD").stdout == (
        "owned/file.py\n"
    )


def test_real_commit_dry_run_ignores_and_preserves_foreign_shared_index(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="foreign/file.py", content="before\n")
    _git(repo_root, "add", "foreign/file.py")
    _git(repo_root, "commit", "-m", "seed foreign")
    _write_repo_file(repo_root=repo_root, relpath="foreign/file.py", content="staged\n")
    _git(repo_root, "add", "foreign/file.py")
    staged_blob = _git(repo_root, "rev-parse", ":foreign/file.py").stdout.strip()
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="plan without reading foreign stage as authority",
            owner_id=owner,
            dry_run=True,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.status == "planned"
    assert outcome.report.staged_paths == ["owned/file.py"]
    assert (
        _git(repo_root, "rev-parse", ":foreign/file.py").stdout.strip() == staged_blob
    )


@pytest.mark.parametrize("initial_index", ["absent", "empty", "foreign", "owned"])
def test_real_commit_supports_unborn_branch_atomic_creation(tmp_path: Path, initial_index: str) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init", "-b", "main")
    _git(repo_root, "config", "user.name", "Aware Test")
    _git(repo_root, "config", "user.email", "aware-test@example.invalid")
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="first\n")
    if initial_index == "empty":
        _git(repo_root, "read-tree", "--empty")
    elif initial_index == "foreign":
        _write_repo_file(repo_root=repo_root, relpath="foreign.txt", content="staged\n")
        _git(repo_root, "add", "foreign.txt")
    elif initial_index == "owned":
        _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="foreign staged\n")
        _git(repo_root, "add", "owned/file.py")
        _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="first\n")

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="first atomic commit",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.expected_head is None
    assert outcome.report.updated_reference == "refs/heads/main"
    assert outcome.report.reference_update == "cas_applied"
    assert _git(repo_root, "show", "--format=", "--name-only", "HEAD").stdout == (
        "owned/file.py\n"
    )
    if initial_index == "owned":
        assert outcome.report.shared_index_projection_error == "foreign_staged_content_preserved"
        assert outcome.report.index_reconciliation_pending is True
        assert _git(repo_root, "show", ":owned/file.py").stdout == "foreign staged\n"
    else:
        assert outcome.report.shared_index_projection == "applied"
        assert outcome.report.index_reconciliation_pending is False
        assert _git(repo_root, "show", ":owned/file.py").stdout == "first\n"
        assert _git(repo_root, "status", "--porcelain", "--", "owned/file.py").stdout == ""
    if initial_index == "foreign":
        assert _git(repo_root, "show", ":foreign.txt").stdout == "staged\n"
    if initial_index in {"absent", "empty", "foreign"}:
        _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="second\n")
        second = run_workspace_commit(options=WorkspaceCommitOptions(
            repo_root=repo_root, issue_path=issue_relpath,
            target_paths=("owned/file.py",), message="follow-up publication", owner_id=owner,
        ))
        assert second.exit_code == 0
        assert second.report.index_reconciliation_pending is False
        assert _git(repo_root, "status", "--porcelain", "--", "owned/file.py").stdout == ""
        if initial_index == "foreign":
            assert _git(repo_root, "show", ":foreign.txt").stdout == "staged\n"


def test_real_commit_supports_linked_worktree_and_common_lock(tmp_path: Path) -> None:
    repo_root, _issue_relpath, owner = _real_repository(tmp_path)
    linked_root = tmp_path / "linked"
    _git(repo_root, "worktree", "add", "-b", "linked-branch", linked_root.as_posix())
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-linked.md"
    _write_issue(repo_root=linked_root, issue_relpath=issue_relpath, owner=owner)
    _write_repo_file(repo_root=linked_root, relpath="owned/file.py", content="linked\n")

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=linked_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="linked worktree atomic commit",
            owner_id=owner,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.updated_reference == "refs/heads/linked-branch"
    assert outcome.report.reference_update == "cas_applied"
    assert (repo_root / ".git/aware/locks/repository-publication.lock").is_file()


def test_interrupted_publisher_leaves_no_ref_or_shared_index_effect_and_recovers(
    tmp_path: Path,
) -> None:
    repo_root, issue_relpath, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py", content="after\n")
    marker = tmp_path / "reference-prepared"
    hook = repo_root / ".git/hooks/reference-transaction"
    hook.write_text(
        (
            "#!/bin/sh\n"
            'if [ "$1" = "prepared" ]; then\n'
            f"  touch {marker.as_posix()}\n"
            "  sleep 30\n"
            "fi\n"
        ),
        encoding="utf-8",
    )
    hook.chmod(0o755)
    initial_head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    initial_index = (repo_root / ".git/index").read_bytes()
    script = (
        "from pathlib import Path\n"
        "from aware_workspace_operator.commit import run_workspace_commit\n"
        "from aware_workspace_operator.models import WorkspaceCommitOptions\n"
        f"outcome = run_workspace_commit(options=WorkspaceCommitOptions(repo_root=Path({repo_root.as_posix()!r}), issue_path={issue_relpath!r}, target_paths=('owned/file.py',), message='interrupted atomic commit', owner_id={owner!r}))\n"
        "raise SystemExit(outcome.exit_code)\n"
    )
    process = subprocess.Popen(
        (sys.executable, "-c", script),
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 10
    while (
        not marker.exists() and process.poll() is None and time.monotonic() < deadline
    ):
        time.sleep(0.02)
    assert marker.exists()
    os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=5)

    assert _git(repo_root, "rev-parse", "HEAD").stdout.strip() == initial_head
    assert (repo_root / ".git/index").read_bytes() == initial_index
    transaction_root = repo_root / ".git/aware-transactions"
    assert tuple(transaction_root.glob("repository-index-*.tmp"))

    hook.unlink()
    recovered = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="recovered atomic commit",
            owner_id=owner,
        )
    )

    assert recovered.exit_code == 0, recovered.report.error
    assert recovered.report.reference_update == "cas_applied"
    assert not tuple(transaction_root.glob("repository-index-*.tmp"))


def test_workspace_commit_dry_run_success(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)

    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "status", "--porcelain", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout=" M owned/file.py\n", stderr=""
                ),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=True,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "planned"
    assert outcome.report.commit_hash is None
    assert outcome.report.staged_paths == ["owned/file.py"]
    assert outcome.report.commit_message == _expected_message(
        issue_relpath=issue_relpath,
        owner=owner,
    )


def test_workspace_commit_defaults_owner_from_provider_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "claude_code-session-42"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)
    monkeypatch.setenv("AWARE_INTERFACE_PROVIDER", "claude_code")
    monkeypatch.setenv("AWARE_INTERFACE_PROVIDER_SESSION_ID", "session-42")

    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "status", "--porcelain", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout=" M owned/file.py\n", stderr=""
                ),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            dry_run=True,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "planned"
    assert outcome.report.owner_id == owner
    assert outcome.report.issue_owner == owner


def test_workspace_commit_dry_run_detects_deletion(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)

    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "status", "--porcelain", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout=" D owned/file.py\n", stderr=""
                ),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=True,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "planned"
    assert outcome.report.staged_paths == ["owned/file.py"]


def test_workspace_commit_fails_on_foreign_pre_staged_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)

    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="foreign/path.txt\n", stderr=""
                ),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=False,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.error
    assert "pre-staged path is outside issue ownership scope" in outcome.report.error


def test_workspace_commit_successful_local_commit(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py")

    commit_message = _expected_message(issue_relpath=issue_relpath, owner=owner)
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "add", "-A", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="owned/file.py\n", stderr=""
                ),
            ),
            _GitExpectation(
                args=("git", "commit", "-m", commit_message),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0,
                    stdout="[main f00dbabe] ship scoped change\n",
                    stderr="",
                ),
            ),
            _GitExpectation(
                args=("git", "rev-parse", "HEAD"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="f00dbabe\n", stderr=""),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=False,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.staged_paths == ["owned/file.py"]
    assert outcome.report.commit_hash == "f00dbabe"
    assert outcome.report.commit_message == commit_message


def test_workspace_commit_reports_full_git_failure_details(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)
    _write_repo_file(repo_root=repo_root, relpath="owned/missing.py")

    important_stderr = "fatal: pathspec 'owned/missing.py' did not match any files"
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "add", "-A", "--", "owned/missing.py"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=128,
                    stdout="",
                    stderr=f"{'x' * 600}\n{important_stderr}\n",
                ),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/missing.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=False,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.error
    assert "Git command failed with exit code 128" in outcome.report.error
    assert important_stderr in outcome.report.error
    assert "[truncated" not in outcome.report.error
    assert "command:\ngit add -A -- owned/missing.py" in outcome.report.error
    assert outcome.report.command_log == [
        ["git", "rev-parse", "--is-inside-work-tree"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "add", "-A", "--", "owned/missing.py"],
    ]


def test_authorized_commit_waits_for_git_mutation_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py")
    ready = multiprocessing.Event()
    release = multiprocessing.Event()
    process = multiprocessing.Process(
        target=_hold_git_mutation_lock_until_released,
        args=(repo_root.as_posix(), ready, release),
    )
    process.start()
    try:
        assert ready.wait(timeout=5)
        monkeypatch.setenv("AWARE_GIT_MUTATION_LOCK_TIMEOUT_SECONDS", "2")
        monkeypatch.setenv("AWARE_GIT_MUTATION_LOCK_POLL_SECONDS", "0.01")

        commit_message = "workspace source revision"
        runner = _FakeGitRunner(
            expectations=[
                _GitExpectation(
                    args=("git", "rev-parse", "--is-inside-work-tree"),
                    cwd=repo_root,
                    result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
                ),
                _GitExpectation(
                    args=("git", "diff", "--cached", "--name-only"),
                    cwd=repo_root,
                    result=_GitCommandResult(returncode=0, stdout="", stderr=""),
                ),
                _GitExpectation(
                    args=("git", "add", "-A", "--", "owned/file.py"),
                    cwd=repo_root,
                    result=_GitCommandResult(returncode=0, stdout="", stderr=""),
                ),
                _GitExpectation(
                    args=("git", "diff", "--cached", "--name-only"),
                    cwd=repo_root,
                    result=_GitCommandResult(
                        returncode=0, stdout="owned/file.py\n", stderr=""
                    ),
                ),
                _GitExpectation(
                    args=("git", "commit", "-m", commit_message),
                    cwd=repo_root,
                    result=_GitCommandResult(
                        returncode=0,
                        stdout="[main f00dbabe] workspace source revision\n",
                        stderr="",
                    ),
                ),
                _GitExpectation(
                    args=("git", "rev-parse", "HEAD"),
                    cwd=repo_root,
                    result=_GitCommandResult(
                        returncode=0, stdout="f00dbabe\n", stderr=""
                    ),
                ),
            ]
        )
        timer = threading.Timer(0.15, release.set)
        started_at = time.monotonic()
        timer.start()
        outcome = run_workspace_authorized_commit(
            options=WorkspaceAuthorizedCommitOptions(
                repo_root=repo_root,
                target_paths=("owned/file.py",),
                message=commit_message,
                owner_id=owner,
                dry_run=False,
            ),
            git_runner=runner,
        )
        elapsed = time.monotonic() - started_at
        timer.cancel()

        runner.assert_complete()
        assert elapsed >= 0.12
        assert outcome.exit_code == 0
        assert outcome.report.status == "ok"
        assert outcome.report.commit_hash == "f00dbabe"
    finally:
        release.set()
        process.join(timeout=5)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)


def test_authorized_commit_reports_git_mutation_lock_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    ready = multiprocessing.Event()
    release = multiprocessing.Event()
    process = multiprocessing.Process(
        target=_hold_git_mutation_lock_until_released,
        args=(repo_root.as_posix(), ready, release),
    )
    process.start()
    try:
        assert ready.wait(timeout=5)
        monkeypatch.setenv("AWARE_GIT_MUTATION_LOCK_TIMEOUT_SECONDS", "0.05")
        monkeypatch.setenv("AWARE_GIT_MUTATION_LOCK_POLL_SECONDS", "0.01")
        runner = _FakeGitRunner(expectations=[])

        outcome = run_workspace_authorized_commit(
            options=WorkspaceAuthorizedCommitOptions(
                repo_root=repo_root,
                target_paths=("owned/file.py",),
                message="workspace source revision",
                owner_id=owner,
                dry_run=False,
            ),
            git_runner=runner,
        )

        assert outcome.exit_code == 2
        assert outcome.report.status == "failed"
        assert outcome.report.error
        assert "Timed out" in outcome.report.error
        assert "Aware Git mutation lock" in outcome.report.error
        assert "codex-lock-holder" in outcome.report.error
        assert "fb/2026-02-13/holder" in outcome.report.error
        assert "test lock holder" in outcome.report.error
        assert "git-mutation.lock" in outcome.report.error
        assert runner.calls == []
    finally:
        release.set()
        process.join(timeout=5)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)


def test_workspace_commit_accepts_already_staged_deleted_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)

    commit_message = (
        "ship scoped change\n\n"
        "Issue-Tag: fb/2026-02-13/test\n"
        f"Issue-Path: {issue_relpath}\n"
        f"Owner: {owner}\n"
        "Owned-Paths: owned/deleted.py"
    )
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="owned/deleted.py\n", stderr=""
                ),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="owned/deleted.py\n", stderr=""
                ),
            ),
            _GitExpectation(
                args=("git", "commit", "-m", commit_message),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0,
                    stdout="[main f00dbabe] ship scoped change\n",
                    stderr="",
                ),
            ),
            _GitExpectation(
                args=("git", "rev-parse", "HEAD"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="f00dbabe\n", stderr=""),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/deleted.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=False,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.staged_paths == ["owned/deleted.py"]
    assert outcome.report.commit_hash == "f00dbabe"


def test_workspace_commit_stages_missing_tracked_deletion(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)

    commit_message = (
        "ship scoped change\n\n"
        "Issue-Tag: fb/2026-02-13/test\n"
        f"Issue-Path: {issue_relpath}\n"
        f"Owner: {owner}\n"
        "Owned-Paths: owned/deleted.py"
    )
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "ls-files", "--", "owned/deleted.py"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="owned/deleted.py\n", stderr=""
                ),
            ),
            _GitExpectation(
                args=("git", "add", "-A", "--", "owned/deleted.py"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="owned/deleted.py\n", stderr=""
                ),
            ),
            _GitExpectation(
                args=("git", "commit", "-m", commit_message),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0,
                    stdout="[main f00dbabe] ship scoped change\n",
                    stderr="",
                ),
            ),
            _GitExpectation(
                args=("git", "rev-parse", "HEAD"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="f00dbabe\n", stderr=""),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/deleted.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=False,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.staged_paths == ["owned/deleted.py"]
    assert outcome.report.commit_hash == "f00dbabe"


def test_workspace_commit_skips_untracked_vanished_pathspec(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py")

    commit_message = (
        "ship scoped change\n\n"
        "Issue-Tag: fb/2026-02-13/test\n"
        f"Issue-Path: {issue_relpath}\n"
        f"Owner: {owner}\n"
        "Owned-Paths: owned/file.py,owned/stale-old-path.py"
    )
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "ls-files", "--", "owned/stale-old-path.py"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "add", "-A", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="owned/file.py\n", stderr=""
                ),
            ),
            _GitExpectation(
                args=("git", "commit", "-m", commit_message),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0,
                    stdout="[main f00dbabe] ship scoped change\n",
                    stderr="",
                ),
            ),
            _GitExpectation(
                args=("git", "rev-parse", "HEAD"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="f00dbabe\n", stderr=""),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py", "owned/stale-old-path.py"),
            message="ship scoped change",
            owner_id=owner,
            dry_run=False,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.staged_paths == ["owned/file.py"]
    assert outcome.report.commit_hash == "f00dbabe"


def test_workspace_commit_allow_empty_forwards_git_flag(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py")

    commit_message = _expected_message(issue_relpath=issue_relpath, owner=owner)
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "add", "-A", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "commit", "--allow-empty", "-m", commit_message),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0,
                    stdout="[main f00dbabe] ship scoped change\n",
                    stderr="",
                ),
            ),
            _GitExpectation(
                args=("git", "rev-parse", "HEAD"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="f00dbabe\n", stderr=""),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=False,
            allow_empty=True,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.staged_paths == []
    assert outcome.report.commit_hash == "f00dbabe"


def test_authorized_commit_allow_empty_forwards_git_flag(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    commit_message = "workspace source revision"
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py")
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "add", "-A", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "commit", "--allow-empty", "-m", commit_message),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0,
                    stdout="[main f00dbabe] workspace source revision\n",
                    stderr="",
                ),
            ),
            _GitExpectation(
                args=("git", "rev-parse", "HEAD"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="f00dbabe\n", stderr=""),
            ),
        ]
    )

    outcome = run_workspace_authorized_commit(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=("owned/file.py",),
            message=commit_message,
            owner_id=owner,
            dry_run=False,
            allow_empty=True,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.staged_paths == []
    assert outcome.report.commit_hash == "f00dbabe"


def test_authorized_commit_idempotency_ref_is_durable_and_replayable(
    tmp_path: Path,
) -> None:
    repo_root = (tmp_path / "repo").resolve()
    repo_root.mkdir(parents=True, exist_ok=True)
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    requested_paths = ("owned/file.py",)
    message = "workspace source revision"
    idempotency_ref = "repository-commit:receipt-123"
    _write_repo_file(repo_root=repo_root, relpath=requested_paths[0])
    fingerprint = _authorized_commit_request_fingerprint(
        repo_root=repo_root,
        owner_id=owner,
        requested_paths=requested_paths,
        message=message,
        allow_empty=False,
    )
    commit_message = (
        f"{message}\n\n"
        f"Aware-Idempotency-Ref: {idempotency_ref}\n"
        f"Aware-Request-Fingerprint: {fingerprint}"
    )
    initial_runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=(
                    "git",
                    "log",
                    "--all",
                    "--basic-regexp",
                    f"--grep=^Aware-Idempotency-Ref: {idempotency_ref}$",
                    "--max-count=2",
                    "--format=%H%x00%B%x00",
                ),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "add", "-A", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="owned/file.py\n", stderr=""
                ),
            ),
            _GitExpectation(
                args=("git", "commit", "-m", commit_message),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "rev-parse", "HEAD"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="f00dbabe\n", stderr=""),
            ),
        ]
    )

    initial = run_workspace_authorized_commit(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=requested_paths,
            message=message,
            owner_id=owner,
            idempotency_ref=idempotency_ref,
        ),
        git_runner=initial_runner,
    )

    initial_runner.assert_complete()
    assert initial.exit_code == 0
    assert initial.report.status == "ok"
    assert initial.report.commit_hash == "f00dbabe"
    assert initial.report.idempotency_ref == idempotency_ref
    assert initial.report.request_fingerprint == fingerprint
    assert initial.report.idempotent_replay is False
    assert initial.report.commit_message == commit_message

    replay_runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=(
                    "git",
                    "log",
                    "--all",
                    "--basic-regexp",
                    f"--grep=^Aware-Idempotency-Ref: {idempotency_ref}$",
                    "--max-count=2",
                    "--format=%H%x00%B%x00",
                ),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0,
                    stdout=f"f00dbabe\x00{commit_message}\n\x00\n",
                    stderr="",
                ),
            ),
            _GitExpectation(
                args=(
                    "git",
                    "diff-tree",
                    "--root",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "f00dbabe",
                ),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout="owned/file.py\n", stderr=""
                ),
            ),
        ]
    )

    replay = run_workspace_authorized_commit(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=requested_paths,
            message=message,
            owner_id=owner,
            idempotency_ref=idempotency_ref,
        ),
        git_runner=replay_runner,
    )

    replay_runner.assert_complete()
    assert replay.exit_code == 0
    assert replay.report.status == "ok"
    assert replay.report.commit_hash == "f00dbabe"
    assert replay.report.staged_paths == ["owned/file.py"]
    assert replay.report.idempotent_replay is True


def test_authorized_path_state_revalidates_exact_bytes_before_stage(
    tmp_path: Path,
) -> None:
    repo_root = (tmp_path / "repo").resolve()
    governed = repo_root / "owned" / "file.py"
    governed.parent.mkdir(parents=True)
    governed.write_text("authorized\n", encoding="utf-8")
    state = WorkspaceAuthorizedPathState(
        path="owned/file.py",
        expected_exists=True,
        expected_content_digest=(
            "sha256:" + hashlib.sha256(b"authorized\n").hexdigest()
        ),
    )

    _validate_authorized_path_states(
        repo_root=repo_root,
        requested_paths=("owned/file.py",),
        authorized_path_states=(state,),
    )

    governed.write_text("out of band\n", encoding="utf-8")
    with pytest.raises(ValueError, match="state is stale"):
        _validate_authorized_path_states(
            repo_root=repo_root,
            requested_paths=("owned/file.py",),
            authorized_path_states=(state,),
        )


def test_authorized_path_state_requires_exact_requested_path_set(
    tmp_path: Path,
) -> None:
    repo_root = (tmp_path / "repo").resolve()
    repo_root.mkdir(parents=True)

    with pytest.raises(ValueError, match="exactly match"):
        _validate_authorized_path_states(
            repo_root=repo_root,
            requested_paths=("owned/file.py",),
            authorized_path_states=(
                WorkspaceAuthorizedPathState(
                    path="owned/other.py",
                    expected_exists=False,
                ),
            ),
        )


def test_authorized_commit_rejects_changed_request_for_existing_idempotency_ref(
    tmp_path: Path,
) -> None:
    repo_root = (tmp_path / "repo").resolve()
    repo_root.mkdir(parents=True, exist_ok=True)
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    idempotency_ref = "repository-commit:receipt-123"
    original_fingerprint = _authorized_commit_request_fingerprint(
        repo_root=repo_root,
        owner_id=owner,
        requested_paths=("owned/file.py",),
        message="original request",
        allow_empty=False,
    )
    historical_message = (
        "original request\n\n"
        f"Aware-Idempotency-Ref: {idempotency_ref}\n"
        f"Aware-Request-Fingerprint: {original_fingerprint}"
    )
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=(
                    "git",
                    "log",
                    "--all",
                    "--basic-regexp",
                    f"--grep=^Aware-Idempotency-Ref: {idempotency_ref}$",
                    "--max-count=2",
                    "--format=%H%x00%B%x00",
                ),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0,
                    stdout=f"f00dbabe\x00{historical_message}\n\x00\n",
                    stderr="",
                ),
            ),
        ]
    )

    outcome = run_workspace_authorized_commit(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=("owned/file.py",),
            message="changed request",
            owner_id=owner,
            idempotency_ref=idempotency_ref,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.error
    assert "already bound to a different" in outcome.report.error
    assert outcome.report.command_log == [
        ["git", "rev-parse", "--is-inside-work-tree"],
        [
            "git",
            "log",
            "--all",
            "--basic-regexp",
            f"--grep=^Aware-Idempotency-Ref: {idempotency_ref}$",
            "--max-count=2",
            "--format=%H%x00%B%x00",
        ],
    ]


def test_authorized_commit_dry_run_does_not_resolve_or_claim_idempotency(
    tmp_path: Path,
) -> None:
    repo_root = (tmp_path / "repo").resolve()
    repo_root.mkdir(parents=True, exist_ok=True)
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_repo_file(repo_root=repo_root, relpath="owned/file.py")
    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "status", "--porcelain", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout=" M owned/file.py\n", stderr=""
                ),
            ),
        ]
    )

    outcome = run_workspace_authorized_commit(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=("owned/file.py",),
            message="planned request",
            owner_id=owner,
            dry_run=True,
            idempotency_ref="repository-commit:receipt-123",
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "planned"
    assert outcome.report.commit_hash is None
    assert outcome.report.idempotent_replay is False


@pytest.mark.parametrize(
    "idempotency_ref",
    ("contains whitespace", "x" * 513),
)
def test_authorized_commit_rejects_unbounded_or_unsafe_idempotency_ref(
    tmp_path: Path,
    idempotency_ref: str,
) -> None:
    repo_root = (tmp_path / "repo").resolve()
    repo_root.mkdir(parents=True, exist_ok=True)
    runner = _FakeGitRunner(expectations=[])

    outcome = run_workspace_authorized_commit(
        options=WorkspaceAuthorizedCommitOptions(
            repo_root=repo_root,
            target_paths=("owned/file.py",),
            message="request",
            owner_id="codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            idempotency_ref=idempotency_ref,
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.error


def test_workspace_commit_requires_owner_match(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    _write_issue(
        repo_root=repo_root,
        issue_relpath=issue_relpath,
        owner="codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id="codex-11111111-2222-3333-4444-555555555555",
            dry_run=True,
        )
    )

    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.error
    assert "Issue owner mismatch" in outcome.report.error


def test_workspace_commit_requires_in_progress_issue_status(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(
        repo_root=repo_root, issue_relpath=issue_relpath, owner=owner, status="Closed"
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=True,
            issue_metadata=WorkspaceCommitIssueMetadata(
                issue_tag="fb/2026-02-13/test",
                issue_owner=owner,
                issue_status="closed",
                ownership_scope=("owned",),
            ),
        )
    )

    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.error
    assert "Issue status must be In Progress for commit rail" in outcome.report.error


def test_workspace_commit_uses_canonical_issue_metadata_override(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    # Local markdown headers are stale on purpose; canonical metadata override is authoritative.
    _write_issue(
        repo_root=repo_root,
        issue_relpath=issue_relpath,
        owner="codex-stale-owner",
        status="Open",
        ownership_scope="`stale`",
    )

    runner = _FakeGitRunner(
        expectations=[
            _GitExpectation(
                args=("git", "rev-parse", "--is-inside-work-tree"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="true\n", stderr=""),
            ),
            _GitExpectation(
                args=("git", "diff", "--cached", "--name-only"),
                cwd=repo_root,
                result=_GitCommandResult(returncode=0, stdout="", stderr=""),
            ),
            _GitExpectation(
                args=("git", "status", "--porcelain", "--", "owned/file.py"),
                cwd=repo_root,
                result=_GitCommandResult(
                    returncode=0, stdout=" M owned/file.py\n", stderr=""
                ),
            ),
        ]
    )

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=True,
            issue_metadata=WorkspaceCommitIssueMetadata(
                issue_tag="fb/2026-02-13/test",
                issue_owner=owner,
                issue_status="in_progress",
                ownership_scope=("owned",),
            ),
        ),
        git_runner=runner,
    )

    runner.assert_complete()
    assert outcome.exit_code == 0
    assert outcome.report.status == "planned"
    assert outcome.report.issue_owner == owner
    assert outcome.report.issue_status == "in_progress"


def test_workspace_commit_fails_when_canonical_metadata_missing_scope(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    issue_relpath = "docs/issues/2026/02/13/fb-2026-02-13-test.md"
    owner = "codex-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_issue(repo_root=repo_root, issue_relpath=issue_relpath, owner=owner)

    outcome = run_workspace_commit(
        options=WorkspaceCommitOptions(
            repo_root=repo_root,
            issue_path=issue_relpath,
            target_paths=("owned/file.py",),
            message="ship scoped change",
            owner_id=owner,
            dry_run=True,
            issue_metadata=WorkspaceCommitIssueMetadata(
                issue_tag="fb/2026-02-13/test",
                issue_owner=owner,
                issue_status="in_progress",
                ownership_scope=(),
            ),
        )
    )

    assert outcome.exit_code == 2
    assert outcome.report.status == "failed"
    assert outcome.report.error
    assert "Canonical issue metadata missing ownership_scope" in outcome.report.error


def _deferred_compat_publication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, issue, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo, relpath="owned/file.py", content="published\n")
    options = WorkspaceCommitOptions(
        repo_root=repo, issue_path=issue, owner_id=owner,
        target_paths=("owned/file.py",), message="publish once",
    )
    with monkeypatch.context() as patch:
        patch.setattr(commit_module, "_project_shared_index_atomically", lambda **kwargs: "shared_index_lock_busy")
        outcome = run_workspace_commit(options=options)
    assert outcome.exit_code == 0  # library preserves the durable publication receipt
    assert outcome.report.index_reconciliation_pending is True
    assert outcome.report.shared_index_projection_error == "shared_index_lock_busy"
    assert _git(repo, "show", "HEAD:owned/file.py").stdout == "published\n"
    assert _git(repo, "show", ":owned/file.py").stdout == "before\n"
    return repo, options, outcome.report.commit_hash


def test_compat_projection_retries_transient_native_index_lock(tmp_path, monkeypatch):
    repo, issue, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo, relpath="owned/file.py", content="published\n")
    original = commit_module._project_shared_index_atomically
    attempts = []

    def transient(**kwargs):
        attempts.append(1)
        return "shared_index_lock_busy" if len(attempts) == 1 else original(**kwargs)

    monkeypatch.setattr(commit_module, "_project_shared_index_atomically", transient)
    outcome = run_workspace_commit(options=WorkspaceCommitOptions(
        repo_root=repo, issue_path=issue, owner_id=owner,
        target_paths=("owned/file.py",), message="publish once",
    ))
    assert len(attempts) == 2
    assert outcome.exit_code == 0
    assert outcome.report.index_reconciliation_pending is False
    assert _git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_compat_reconciliation_is_readonly_planned_and_no_commit_applied(tmp_path, monkeypatch):
    repo, options, publication = _deferred_compat_publication(tmp_path, monkeypatch)
    _write_repo_file(repo_root=repo, relpath="owned/file.py", content="new uncommitted work\n")
    _write_repo_file(repo_root=repo, relpath="foreign.txt", content="foreign staged\n")
    _git(repo, "add", "foreign.txt")
    index = (repo / ".git/index").read_bytes()
    recovery = options.model_copy(update={"reconcile_commit": publication})
    plan = run_workspace_commit(options=recovery.model_copy(update={"dry_run": True}))
    assert plan.exit_code == 0 and plan.report.status == "planned"
    assert (repo / ".git/index").read_bytes() == index
    applied = run_workspace_commit(options=recovery)
    assert applied.exit_code == 0
    assert applied.report.commit_hash == publication
    assert applied.report.reference_update == "not_run"
    assert applied.report.shared_index_projection == "applied"
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == publication
    assert _git(repo, "show", ":owned/file.py").stdout == "published\n"
    assert _git(repo, "show", ":foreign.txt").stdout == "foreign staged\n"
    assert (repo / "owned/file.py").read_text() == "new uncommitted work\n"
    replay = run_workspace_commit(options=recovery)
    assert replay.exit_code == 0 and replay.report.commit_hash == publication


@pytest.mark.parametrize("dry_run", [True, False])
def test_compat_reconciliation_preserves_foreign_staged_target(tmp_path, monkeypatch, dry_run):
    repo, options, publication = _deferred_compat_publication(tmp_path, monkeypatch)
    _write_repo_file(repo_root=repo, relpath="owned/file.py", content="foreign staged\n")
    _git(repo, "add", "owned/file.py")
    index = (repo / ".git/index").read_bytes()
    outcome = run_workspace_commit(options=options.model_copy(update={
        "reconcile_commit": publication, "dry_run": dry_run,
    }))
    assert outcome.exit_code == 2
    assert "index_reconciliation_foreign_staging" in outcome.report.error
    assert (repo / ".git/index").read_bytes() == index


def test_compat_reconciliation_refuses_advanced_published_path(tmp_path, monkeypatch):
    repo, options, publication = _deferred_compat_publication(tmp_path, monkeypatch)
    _write_repo_file(repo_root=repo, relpath="owned/file.py", content="later commit\n")
    _git(repo, "add", "owned/file.py")
    _git(repo, "commit", "-m", "another owner")
    index = (repo / ".git/index").read_bytes()
    outcome = run_workspace_commit(options=options.model_copy(update={"reconcile_commit": publication}))
    assert outcome.exit_code == 2
    assert "published_path_advanced" in outcome.report.error
    assert (repo / ".git/index").read_bytes() == index


def test_compat_reconciliation_allows_unrelated_head_advance(tmp_path, monkeypatch):
    repo, options, publication = _deferred_compat_publication(tmp_path, monkeypatch)
    _write_repo_file(repo_root=repo, relpath="foreign.txt", content="other publication\n")
    _git(repo, "add", "foreign.txt")
    _git(repo, "commit", "--only", "foreign.txt", "-m", "unrelated publication")
    head = _git(repo, "rev-parse", "HEAD").stdout
    outcome = run_workspace_commit(options=options.model_copy(update={"reconcile_commit": publication}))
    assert outcome.exit_code == 0
    assert _git(repo, "rev-parse", "HEAD").stdout == head
    assert _git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_compat_reconciliation_rejects_unadmitted_commit(tmp_path, monkeypatch):
    repo, options, publication = _deferred_compat_publication(tmp_path, monkeypatch)
    parent = _git(repo, "rev-parse", f"{publication}^").stdout.strip()
    outcome = run_workspace_commit(options=options.model_copy(update={"reconcile_commit": parent}))
    assert outcome.exit_code == 2
    assert "publication_issue_mismatch" in outcome.report.error


def test_compat_commit_receipt_does_not_follow_later_head(tmp_path, monkeypatch):
    repo, issue, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo, relpath="owned/file.py", content="published\n")
    original = commit_module._run_commit_flow

    def advance_after_publication(**kwargs):
        result = original(**kwargs)
        _write_repo_file(repo_root=repo, relpath="foreign.txt", content="other\n")
        _git(repo, "add", "foreign.txt")
        _git(repo, "commit", "-m", "later owner")
        return result

    monkeypatch.setattr(commit_module, "_run_commit_flow", advance_after_publication)
    outcome = run_workspace_commit(options=WorkspaceCommitOptions(
        repo_root=repo, issue_path=issue, owner_id=owner,
        target_paths=("owned/file.py",), message="publish once",
    ))
    assert outcome.exit_code == 0
    assert outcome.report.commit_hash == outcome.report.candidate_commit
    assert outcome.report.commit_hash != _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.mark.parametrize("path", ["foreign.txt", "owned/new-file.py"])
def test_compat_reconciliation_cannot_expand_publication_scope(tmp_path, monkeypatch, path):
    repo, options, publication = _deferred_compat_publication(tmp_path, monkeypatch)
    index = (repo / ".git/index").read_bytes()
    outcome = run_workspace_commit(options=options.model_copy(update={
        "reconcile_commit": publication, "target_paths": (path,), "dry_run": True,
    }))
    assert outcome.exit_code == 2
    assert "scope" in outcome.report.error
    assert (repo / ".git/index").read_bytes() == index


def test_compat_reconciliation_fences_head_movement_after_validation(tmp_path, monkeypatch):
    repo, options, publication = _deferred_compat_publication(tmp_path, monkeypatch)
    original = commit_module._recover_replayed_index_projection

    def advance_before_recovery(**kwargs):
        _write_repo_file(repo_root=repo, relpath="foreign.txt", content="concurrent\n")
        _git(repo, "add", "foreign.txt")
        _git(repo, "commit", "--only", "foreign.txt", "-m", "concurrent owner")
        return original(**kwargs)

    monkeypatch.setattr(commit_module, "_recover_replayed_index_projection", advance_before_recovery)
    outcome = run_workspace_commit(options=options.model_copy(update={"reconcile_commit": publication}))
    assert outcome.exit_code == 2
    assert "index_reconciliation_head_advanced" in outcome.report.error
    assert _git(repo, "show", ":owned/file.py").stdout == "before\n"
    assert _git(repo, "show", "HEAD:owned/file.py").stdout == "published\n"


def test_compat_projection_exception_retains_published_receipt(tmp_path, monkeypatch):
    repo, issue, owner = _real_repository(tmp_path)
    _write_repo_file(repo_root=repo, relpath="owned/file.py", content="published\n")

    def interrupted(**kwargs):
        raise OSError("simulated projection IO failure")

    monkeypatch.setattr(commit_module, "_project_shared_index_atomically", interrupted)
    outcome = run_workspace_commit(options=WorkspaceCommitOptions(
        repo_root=repo, issue_path=issue, owner_id=owner,
        target_paths=("owned/file.py",), message="publish once",
    ))
    assert outcome.exit_code == 2  # preserve the library's actual provider error
    assert outcome.report.commit_hash == _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert outcome.report.index_reconciliation_pending is True
    assert outcome.report.shared_index_projection_error == "post_publication_projection_interrupted"
    assert _git(repo, "show", ":owned/file.py").stdout == "before\n"
