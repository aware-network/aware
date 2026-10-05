"""An agent entrance to canonical filesystem Issue operations, not another engine."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from aware_issue_cli.main import main as issue_main
from aware_issue_cli.summary import summarize_result
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueBindScopePathsRequest,
    IssueEnsureSnapshotRequest,
    IssueMutationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueSdkOperationClient,
    IssueStartProgressRequest,
)

from .setup import (
    initialize as initialize_bootstrap,
)
from .setup import (
    observe_contract,
    prepare_repository,
)

MANIFEST = """aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = ".aware/agent-protocol.md"
[records.goal]
profile = "aware.goal.markdown.v1"
role = "unavailable"
[records.issue]
profile = "aware.issue.markdown.v1"
role = "authority"
root = "docs/issues"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification]
profile = "specification_fs_v1"
role = "unavailable"
[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
"""


def initialize(arguments: list[str]) -> int:
    return initialize_bootstrap(arguments, manifest=MANIFEST)


def open_issue(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="aware issue open")
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--protocol-source", default="aware.protocol.toml")
    parser.add_argument("--issue-ref", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--priority", default="P1")
    parser.add_argument("--scope-path", action="append", required=True)
    parser.add_argument("--client-intent-id", required=True)
    parser.add_argument("--actor-ref", required=True)
    parser.add_argument("--actor-evidence-ref", required=True)
    parser.add_argument("--goal-ref", default="TBD")
    parser.add_argument("--problem", action="append", required=True)
    parser.add_argument("--objective", action="append", required=True)
    parser.add_argument("--acceptance", action="append", required=True)
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    args = parser.parse_args(arguments)
    evidence = {
        "issue_ref": args.issue_ref,
        "actor_ref": args.actor_ref,
        "actor_evidence_ref": args.actor_evidence_ref,
    }
    request = IssueEnsureSnapshotRequest(
        **evidence,
        client_intent_id=args.client_intent_id + ":ensure",
        title=args.title,
        priority=args.priority,
        owner_ref=args.actor_ref,
        goal_ref=args.goal_ref,
        source_description="Customer-directed work through aware issue open",
        problem_items=tuple(args.problem),
        objective_items=tuple(args.objective),
        acceptance_items=tuple(args.acceptance),
    )

    def emit(payload):
        print(
            json.dumps(
                summarize_result(payload) if args.format == "summary" else payload,
                sort_keys=True,
            )
        )

    client = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(
            repository_root=args.repository_root,
            protocol_source_ref=args.protocol_source,
        )
    )
    before = client.resolve_read_projection(
        IssueReadProjectionResolveRequest(issue_ref=args.issue_ref)
    )
    if before.outcome is not IssueReadProjectionResolveOutcome.ABSENT:
        emit(
            {
                "outcome": "refused",
                "diagnostics": ["open_requires_absent_issue"],
                "observation": before.to_wire(),
            }
        )
        return 2
    receipts = []

    def retain(result):
        receipts.append(result.to_wire())
        return result.outcome in {
            IssueMutationOutcome.APPLIED,
            IssueMutationOutcome.IDEMPOTENT,
        }

    try:
        ensured = client.ensure_issue_snapshot(request)
        if retain(ensured) and ensured.projection is not None:
            scope = tuple(
                dict.fromkeys([*args.scope_path, ensured.projection.source_path])
            )
            bound = client.bind_issue_scope_paths(
                IssueBindScopePathsRequest(
                    **evidence,
                    client_intent_id=args.client_intent_id + ":scope",
                    expected_source_sha256=ensured.source_sha256_after,
                    scope_paths=scope,
                )
            )
            if retain(bound):
                started = client.start_issue_progress(
                    IssueStartProgressRequest(
                        **evidence,
                        client_intent_id=args.client_intent_id + ":start",
                        expected_source_sha256=bound.source_sha256_after,
                    )
                )
                success = retain(started)
                emit(
                    {
                        "outcome": "opened" if success else "incomplete",
                        "receipts": receipts,
                        "atomic": False,
                    }
                )
                return 0 if success else 2
    except (ValueError, TypeError, OSError, subprocess.CalledProcessError) as error:
        emit(
            {
                "outcome": "incomplete",
                "receipts": receipts,
                "atomic": False,
                "diagnostics": [
                    f"composition_failed:{type(error).__name__}",
                    str(error),
                ],
            }
        )
        return 2
    emit({"outcome": "incomplete", "receipts": receipts, "atomic": False})
    return 2


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args and args[0] == "init":
            return initialize(args[1:])
        if args and args[0] == "contract":
            return observe_contract(args[1:])
        if args[:2] == ["issue", "open"]:
            return open_issue(args[2:])
        if args and args[0] == "issue":
            return issue_main(args[1:])
        if args[:2] == ["repository", "commit"]:
            return issue_main(["commit-workspace", *args[2:]])
        if args[:2] == ["repository", "create"]:
            return prepare_repository(args[2:])
        parser = argparse.ArgumentParser(
            prog="aware", description="Agent-first, filesystem-only Issue workflow."
        )
        parser.add_argument(
            "--version", action="version", version="aware-agent-cli 0.1.0a5"
        )
        parser.epilog = "Commands: init [--create-repository]; contract; issue open; issue <canonical Issue CLI command>; repository create; repository commit"
        parser.parse_args(args)
        parser.print_help()
        return 0
    except (ValueError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(
            json.dumps(
                {"outcome": "error", "diagnostics": [str(error)]}, sort_keys=True
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
