"""Thin CLI projection for canonical Issue SDK operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
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
    IssueProviderResultError,
    IssuePublicationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueResumeRequest,
    IssueSdkOperationClient,
    IssueSetOwnerRequest,
    IssueStartProgressRequest,
)

from .summary import summarize_result, validate_presentation_input


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aware-issue-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    present = subparsers.add_parser(
        "present-receipt",
        help="Present a saved full JSON result without replaying its operation",
    )
    present.add_argument(
        "--receipt-path",
        required=True,
        help="Saved full JSON file; relative to process working directory",
    )
    present.add_argument(
        "--expected-receipt-sha256",
        help="Optional sha256:<hex> of exact saved file bytes, not Issue or manifest bytes",
    )
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
    ensure.add_argument("--problem", action="append", default=[])
    ensure.add_argument("--objective", action="append", default=[])
    ensure.add_argument("--acceptance", action="append", default=[])
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
    for command_parser in subparsers.choices.values():
        command_parser.add_argument(
            "--format",
            choices=("json", "summary"),
            default="summary" if command_parser is present else "json",
            help="json retains the full result; summary omits only historical recorded evidence with visible digest/access metadata",
        )
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
    if args.command == "present-receipt":
        return _present_receipt(args)
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
                    problem_items=tuple(args.problem),
                    objective_items=tuple(args.objective),
                    acceptance_items=tuple(args.acceptance),
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
    except IssueProviderResultError as error:
        payload = error.to_wire()
        payload.update(
            outcome="malformed",
            diagnostics=[error.failure.code],
            authorizes_retry=False,
        )
        print(
            json.dumps(
                summarize_result(payload) if args.format == "summary" else payload,
                sort_keys=True,
            )
        )
        return 2
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
        payload: dict[str, object] = {
            "operation_ref": operation_ref,
            "outcome": "malformed",
            "diagnostics": [f"request_invalid:{type(error).__name__}"],
        }
        print(
            json.dumps(
                summarize_result(payload) if args.format == "summary" else payload,
                sort_keys=True,
            )
        )
        return 2
    payload = result.to_wire()
    print(
        json.dumps(
            summarize_result(payload) if args.format == "summary" else payload,
            sort_keys=True,
        )
    )
    successful = result.outcome in {
        IssueReadProjectionResolveOutcome.FOUND,
        IssueMutationOutcome.APPLIED,
        IssueMutationOutcome.IDEMPOTENT,
        IssuePublicationOutcome.PLANNED,
        IssuePublicationOutcome.APPLIED,
    }
    return 0 if successful else 2


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _present_receipt(args):
    """No provider call, capability reconstruction, source mutation or retry."""
    try:
        expected = args.expected_receipt_sha256
        if (
            expected is not None
            and re.fullmatch(r"sha256:[0-9a-f]{64}", expected) is None
        ):
            raise ValueError("invalid_saved_receipt_digest")
        descriptor = os.open(
            args.receipt_path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW
        )
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError("saved_receipt_not_regular")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                body = stream.read(16 * 1024 * 1024 + 1)
        finally:
            os.close(descriptor)
        if len(body) > 16 * 1024 * 1024:
            raise ValueError("saved_receipt_exceeds_16_mib")
        digest = "sha256:" + hashlib.sha256(body).hexdigest()
        if expected is not None and expected != digest:
            raise ValueError("saved_receipt_digest_mismatch")
        payload = json.loads(
            body.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError("nonfinite_json")
            ),
        )
        if (
            type(payload) is not dict
            or not isinstance(payload.get("operation_ref"), str)
            or not isinstance(payload.get("outcome"), str)
            or "view" in payload
        ):
            raise ValueError("full_operation_result_required")
        validate_presentation_input(payload)
        output = summarize_result(payload) if args.format == "summary" else payload
        # Wrap instead of overwriting any original domain field.
        print(
            json.dumps(
                {
                    "presentation": {
                        "mode": "saved_result_no_operation_replay",
                        "receipt_path": args.receipt_path,
                        "receipt_sha256": digest,
                        "operation_invoked": False,
                        "currentness": "not_revalidated",
                        "authority_restored": False,
                    },
                    "result": output,
                },
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 0  # Presentation succeeded; recorded domain outcome is unchanged.
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as error:
        print(
            json.dumps(
                {
                    "presentation": {
                        "outcome": "refused",
                        "operation_invoked": False,
                        "diagnostic": str(error)
                        if isinstance(error, ValueError)
                        else type(error).__name__,
                    }
                },
                sort_keys=True,
            )
        )
        return 2


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
