from __future__ import annotations

import argparse
import json

import pytest
from aware_workspace_operator.cli import commit_command
from aware_workspace_operator.models import (
    WorkspaceCommitIssueMetadata,
    WorkspaceCommitOutcome,
    WorkspaceCommitReport,
)


@pytest.mark.parametrize("json_output", [True, False])
@pytest.mark.parametrize("status", ["ok", "failed"])
def test_cli_reports_publication_pending_not_plain_success(
    tmp_path, monkeypatch, capsys, json_output, status
):
    parser = argparse.ArgumentParser()
    commit_command.register_commit_parser(parser.add_subparsers())
    args = parser.parse_args(
        [
            "commit",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.md",
            "--issue-tag",
            "fb/test",
            "--path",
            "owned.py",
            "--message",
            "publish",
            *(["--json"] if json_output else []),
        ]
    )
    monkeypatch.setattr(
        commit_command,
        "_load_issue_metadata_for_commit",
        lambda **kwargs: WorkspaceCommitIssueMetadata(
            issue_tag="fb/test",
            issue_owner="codex-test",
            issue_status="in_progress",
            ownership_scope=("owned.py",),
        ),
    )
    monkeypatch.setattr(
        commit_command, "sync_issue_state_from_doc", lambda **kwargs: None
    )
    monkeypatch.setattr(
        commit_command,
        "run_workspace_commit",
        lambda **kwargs: WorkspaceCommitOutcome(
            report=WorkspaceCommitReport(
                repo_root=str(tmp_path),
                status=status,
                commit_hash="a" * 40,
                shared_index_projection="failed",
                shared_index_projection_error="shared_index_lock_busy",
                index_reconciliation_pending=True,
            ),
            exit_code=0,
        ),
    )
    assert commit_command.handle_commit_command(args, None) == 3
    output = capsys.readouterr()
    assert "Publication succeeded" in output.err
    assert "--reconcile-index " + "a" * 40 in output.err
    if json_output:
        body = json.loads(output.out)
        assert body["commit_hash"] == "a" * 40
        assert body["index_reconciliation_pending"] is True


def test_cli_reconciliation_option_is_forwarded(tmp_path, monkeypatch):
    parser = argparse.ArgumentParser()
    commit_command.register_commit_parser(parser.add_subparsers())
    args = parser.parse_args(
        [
            "commit",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.md",
            "--issue-tag",
            "fb/test",
            "--path",
            "owned.py",
            "--message",
            "publish",
            "--reconcile-index",
            "a" * 40,
            "--dry-run",
        ]
    )
    monkeypatch.setattr(
        commit_command,
        "_load_issue_metadata_for_commit",
        lambda **kwargs: WorkspaceCommitIssueMetadata(
            issue_tag="fb/test",
            issue_owner="codex-test",
            issue_status="in_progress",
            ownership_scope=("owned.py",),
        ),
    )

    def observe(*, options):
        assert options.reconcile_commit == "a" * 40
        assert options.dry_run is True
        return WorkspaceCommitOutcome(
            report=WorkspaceCommitReport(repo_root=str(tmp_path), status="planned"),
            exit_code=0,
        )

    monkeypatch.setattr(commit_command, "run_workspace_commit", observe)
    assert commit_command.handle_commit_command(args, None) == 0
