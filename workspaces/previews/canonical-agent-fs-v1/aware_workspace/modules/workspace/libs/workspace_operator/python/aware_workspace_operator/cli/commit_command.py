"""Canonical local git commit rail (issue + ownership enforced)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aware_workflow.cli.workflow_issue_state import (
    load_workspace_commit_issue_metadata_from_state,
    resolve_repo_relative_path,
    resolve_workflow_issue_state_path,
    sync_issue_state_from_doc,
)

from aware_workspace_operator import (
    WorkspaceCommitIssueMetadata,
    WorkspaceCommitOptions,
    print_workspace_commit_result,
    resolve_repo_root,
    run_workspace_commit,
)


def _load_issue_metadata_from_state(
    *,
    issue_path: str,
    issue_tag: str,
    state_path: Path,
) -> WorkspaceCommitIssueMetadata:
    return load_workspace_commit_issue_metadata_from_state(
        issue_path=issue_path,
        issue_tag=issue_tag,
        state_path=state_path,
    )


def _load_issue_metadata_for_commit(
    *,
    repo_root: Path,
    issue_path: str,
    issue_tag: str,
    state_path: Path,
) -> WorkspaceCommitIssueMetadata:
    issue_doc_path = resolve_repo_relative_path(
        repo_root=repo_root,
        raw_path=issue_path,
    )
    if issue_doc_path.exists():
        sync_issue_state_from_doc(
            repo_root=repo_root,
            issue_doc_path=issue_doc_path,
            state_path=state_path,
            issue_tag=issue_tag,
        )
    return _load_issue_metadata_from_state(
        issue_path=issue_path,
        issue_tag=issue_tag,
        state_path=state_path,
    )


def handle_commit_command(args: argparse.Namespace, ctx: Any) -> int:
    _ = ctx
    try:
        repo_root = resolve_repo_root(
            raw_repo_root=getattr(args, "repo_root", None),
            create_if_missing=False,
        )
        state_path = resolve_workflow_issue_state_path(
            repo_root=repo_root,
            raw_state_path=getattr(args, "issue_state_path", None),
        )
    except Exception as exc:  # noqa: BLE001 - CLI boundary reports typed setup failures
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    issue_tag = str(getattr(args, "issue_tag", "")).strip()
    try:
        issue_metadata = _load_issue_metadata_for_commit(
            repo_root=repo_root,
            issue_path=str(args.issue),
            issue_tag=issue_tag,
            state_path=state_path,
        )
    except Exception as exc:  # noqa: BLE001 - Issue authority must fail closed
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    options = WorkspaceCommitOptions(
        repo_root=repo_root,
        issue_path=str(args.issue),
        target_paths=tuple(getattr(args, "path", []) or ()),
        message=str(args.message),
        owner_id=(str(args.owner_id) if getattr(args, "owner_id", None) else None),
        dry_run=bool(getattr(args, "dry_run", False)),
        allow_empty=bool(getattr(args, "allow_empty", False)),
        issue_metadata=issue_metadata,
        reconcile_commit=getattr(args, "reconcile_index", None),
    )

    try:
        outcome = run_workspace_commit(options=options)
    except Exception as exc:  # noqa: BLE001 - CLI boundary preserves provider errors
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if outcome.exit_code == 0 and not options.dry_run:
        try:
            sync_issue_state_from_doc(
                repo_root=repo_root,
                issue_doc_path=resolve_repo_relative_path(
                    repo_root=repo_root,
                    raw_path=options.issue_path,
                ),
                state_path=state_path,
                issue_tag=issue_tag,
            )
        except Exception as exc:  # noqa: BLE001 - publication must survive cache sync failure
            print(
                f"Warning: local workflow issue state sync failed after commit: {exc}",
                file=sys.stderr,
            )

    if bool(getattr(args, "json", False)):
        print(json.dumps(outcome.payload, indent=2, sort_keys=True))
    else:
        print_workspace_commit_result(payload=outcome.payload)
    if (
        outcome.report.commit_hash is not None
        and outcome.report.shared_index_projection == "failed"
    ):
        print(
            "Publication succeeded, but shared-index reconciliation is pending: "
            f"{outcome.report.shared_index_projection_error}. "
            "Do not create another commit or reset the shared index. "
            "Repeat this scoped request with --reconcile-index "
            f"{outcome.report.commit_hash} --dry-run, then without --dry-run.",
            file=sys.stderr,
        )
        return 3
    return int(outcome.exit_code)


def register_commit_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "commit",
        help=(
            "Canonical local git commit rail with strict issue ownership checks "
            "(only explicit scoped paths are allowed)."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Optional repository root. When omitted, resolves from explicit "
            "workspace repo-root environment variables only."
        ),
    )
    parser.add_argument(
        "--issue",
        required=True,
        help="Issue path used for ownership/tag enforcement (repo-relative or absolute).",
    )
    parser.add_argument(
        "--issue-tag",
        required=True,
        help=(
            "Canonical issue tag used to refresh issue authority and load "
            "ownership/status/scope (example: fb/2026-02-13/my-issue)."
        ),
    )
    parser.add_argument(
        "--issue-state-path",
        default=None,
        help=(
            "Optional workflow issue state file path. Defaults to "
            "`$AWARE_WORKFLOW_ISSUE_STATE_PATH` or `<repo>/.aware/workflow_issue/state.json`."
        ),
    )
    parser.add_argument(
        "--path",
        action="append",
        required=True,
        default=[],
        help="Repeatable explicit path to stage+commit. Must be within issue ownership scope.",
    )
    parser.add_argument(
        "--message",
        required=True,
        help="Commit subject line. Canonical metadata footers are added automatically.",
    )
    parser.add_argument(
        "--owner-id",
        default=None,
        help=(
            "Optional owner execution-id override (`<provider>-<provider_session_id>`). "
            "When omitted, the commit rail resolves from the current provider context."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and validate ownership/scoped staging without mutating git state.",
    )
    parser.add_argument(
        "--reconcile-index",
        metavar="PUBLISHED_COMMIT",
        default=None,
        help=(
            "Reconcile only these Issue-owned index paths to an already published "
            "commit; verifies unchanged HEAD postimages and preserves foreign staging. "
            "Never creates a commit or modifies worktree files."
        ),
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow commit rail to proceed even when no scoped changes are detected.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable report JSON.",
    )
    return parser


__all__ = ["handle_commit_command", "register_commit_parser"]
