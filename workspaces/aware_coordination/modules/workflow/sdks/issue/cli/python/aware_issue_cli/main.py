"""Thin CLI projection for canonical Issue SDK operations."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueAppendEvidenceRequest,
    IssueAppendUpdateRequest,
    IssueBindScopePathsRequest,
    IssueBlockRequest,
    IssueCloseRequest,
    IssueCommitWorkspaceRequest,
    IssueEnsureSnapshotRequest,
    IssueMutationOutcome,
    IssuePublicationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueResumeRequest,
    IssueSdkOperationClient,
    IssueSetOwnerRequest,
    IssueStartProgressRequest,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aware-issue-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve = subparsers.add_parser("resolve-read-projection")
    resolve.add_argument("--repository-root", required=True)
    resolve.add_argument("--issue-ref", required=True)
    resolve.add_argument("--protocol-source", default="aware.protocol.toml")
    ensure = subparsers.add_parser("ensure-snapshot")
    _target_arguments(ensure)
    ensure.add_argument("--title", required=True)
    ensure.add_argument("--priority", required=True)
    ensure.add_argument("--owner-ref")
    ensure.add_argument("--goal-ref", default="TBD")
    ensure.add_argument(
        "--source-description",
        default="issue_sdk.ensure_issue_snapshot",
    )
    ensure.add_argument("--expected-source-sha256")
    _actor_arguments(ensure)

    for command in ("start-progress", "block", "resume"):
        mutation = subparsers.add_parser(command)
        _mutation_arguments(mutation)

    set_owner = subparsers.add_parser("set-owner")
    _mutation_arguments(set_owner)
    set_owner.add_argument("--new-owner-ref", required=True)

    bind_scope = subparsers.add_parser("bind-scope")
    _mutation_arguments(bind_scope)
    bind_scope.add_argument("--scope-path", action="append", default=[])

    append_update = subparsers.add_parser("append-update")
    _mutation_arguments(append_update)
    append_update.add_argument("--message", required=True)
    append_update.add_argument("--outcome", default="info")

    append_evidence = subparsers.add_parser("append-evidence")
    _mutation_arguments(append_evidence)
    append_evidence.add_argument("--path", required=True)
    append_evidence.add_argument("--description")

    close = subparsers.add_parser("close")
    _mutation_arguments(close)
    close.add_argument("--resolution", required=True)
    close.add_argument("--verified-by", action="append", required=True)
    close.add_argument("--publication-receipt-ref", required=True)

    commit_workspace = subparsers.add_parser("commit-workspace")
    _target_arguments(commit_workspace)
    commit_workspace.add_argument("--expected-issue-source-sha256", required=True)
    commit_workspace.add_argument("--path", action="append", required=True)
    commit_workspace.add_argument("--message", required=True)
    commit_workspace.add_argument("--dry-run", action="store_true")
    commit_workspace.add_argument("--actor-ref", required=True)
    commit_workspace.add_argument("--actor-evidence-ref", required=True)
    return parser


def _target_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--issue-ref", required=True)
    parser.add_argument("--protocol-source", default="aware.protocol.toml")


def _actor_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--client-intent-id", required=True)
    parser.add_argument("--actor-ref", required=True)
    parser.add_argument("--actor-evidence-ref", required=True)


def _mutation_arguments(parser: argparse.ArgumentParser) -> None:
    _target_arguments(parser)
    parser.add_argument("--expected-source-sha256", required=True)
    _actor_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        provider = FilesystemIssueOperationProvider(
            repository_root=args.repository_root,
            protocol_source_ref=args.protocol_source,
        )
        client = IssueSdkOperationClient(provider=provider)
        if args.command == "resolve-read-projection":
            result = client.resolve_read_projection(
                IssueReadProjectionResolveRequest(issue_ref=args.issue_ref)
            )
        elif args.command == "ensure-snapshot":
            result = client.ensure_issue_snapshot(
                IssueEnsureSnapshotRequest(
                    issue_ref=args.issue_ref,
                    title=args.title,
                    priority=args.priority,
                    owner_ref=args.owner_ref,
                    goal_ref=args.goal_ref,
                    source_description=args.source_description,
                    expected_source_sha256=args.expected_source_sha256,
                    client_intent_id=args.client_intent_id,
                    actor_ref=args.actor_ref,
                    actor_evidence_ref=args.actor_evidence_ref,
                )
            )
        elif args.command == "start-progress":
            result = client.start_issue_progress(
                IssueStartProgressRequest(**_mutation_payload(args))
            )
        elif args.command == "block":
            result = client.block_issue(IssueBlockRequest(**_mutation_payload(args)))
        elif args.command == "resume":
            result = client.resume_issue(IssueResumeRequest(**_mutation_payload(args)))
        elif args.command == "set-owner":
            result = client.set_issue_owner(
                IssueSetOwnerRequest(
                    **_mutation_payload(args),
                    new_owner_ref=args.new_owner_ref,
                )
            )
        elif args.command == "bind-scope":
            result = client.bind_issue_scope_paths(
                IssueBindScopePathsRequest(
                    **_mutation_payload(args),
                    scope_paths=tuple(args.scope_path),
                )
            )
        elif args.command == "append-update":
            result = client.append_issue_update(
                IssueAppendUpdateRequest(
                    **_mutation_payload(args),
                    message=args.message,
                    outcome=args.outcome,
                )
            )
        elif args.command == "append-evidence":
            result = client.append_issue_evidence(
                IssueAppendEvidenceRequest(
                    **_mutation_payload(args),
                    path=args.path,
                    description=args.description,
                )
            )
        elif args.command == "close":
            result = client.close_issue(
                IssueCloseRequest(
                    **_mutation_payload(args),
                    resolution=args.resolution,
                    verified_by=tuple(args.verified_by),
                    publication_receipt_ref=args.publication_receipt_ref,
                )
            )
        elif args.command == "commit-workspace":
            result = client.commit_workspace(
                IssueCommitWorkspaceRequest(
                    issue_ref=args.issue_ref,
                    expected_issue_source_sha256=(args.expected_issue_source_sha256),
                    target_paths=tuple(args.path),
                    message=args.message,
                    actor_ref=args.actor_ref,
                    actor_evidence_ref=args.actor_evidence_ref,
                    dry_run=args.dry_run,
                )
            )
        else:
            raise AssertionError(f"unsupported command: {args.command}")
    except (TypeError, ValueError) as error:
        operation_ref = {
            "resolve-read-projection": "issue_sdk.resolve_issue_read_projection",
            "ensure-snapshot": "issue_sdk.ensure_issue_snapshot",
            "start-progress": "issue_sdk.start_issue_progress",
            "block": "issue_sdk.block_issue",
            "resume": "issue_sdk.resume_issue",
            "set-owner": "issue_sdk.set_issue_owner",
            "bind-scope": "issue_sdk.bind_issue_scope_paths",
            "append-update": "issue_sdk.append_issue_update",
            "append-evidence": "issue_sdk.append_issue_evidence",
            "close": "issue_sdk.close_issue",
            "commit-workspace": "issue_sdk.commit_workspace",
        }[args.command]
        print(
            json.dumps(
                {
                    "operation_ref": operation_ref,
                    "outcome": "malformed",
                    "diagnostics": [f"request_invalid:{type(error).__name__}"],
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result.to_wire(), sort_keys=True))
    successful = result.outcome in {
        IssueReadProjectionResolveOutcome.FOUND,
        IssueMutationOutcome.APPLIED,
        IssueMutationOutcome.IDEMPOTENT,
        IssuePublicationOutcome.PLANNED,
        IssuePublicationOutcome.APPLIED,
    }
    return 0 if successful else 2


def _mutation_payload(args: argparse.Namespace) -> dict[str, str]:
    return {
        "issue_ref": args.issue_ref,
        "expected_source_sha256": args.expected_source_sha256,
        "client_intent_id": args.client_intent_id,
        "actor_ref": args.actor_ref,
        "actor_evidence_ref": args.actor_evidence_ref,
    }


if __name__ == "__main__":
    raise SystemExit(main())
