"""Thin CLI projection for canonical Issue SDK operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from collections.abc import Sequence
from functools import partial

from aware_command_runtime import (
    AwareCommandInvocation,
    AwareCommandRegistry,
    CommandRegistrationError,
    build_parser,
    dispatch_command,
)
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
from aware_issue_sdk.repository_publication import IssueRepositoryPublicationRefusal

from .composition import create_repository_client
from .summary import summarize_result, validate_presentation_input

_ISSUE_OPERATION_REFS = {
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
}


def register_issue_commands(registry: AwareCommandRegistry) -> None:
    """Mount existing SDK handlers, without admission, IO or operation execution."""
    names = ("present-receipt", "publish-close", *_ISSUE_OPERATION_REFS)
    # Refuse a family collision before adding any part of this family.
    for name in names:
        if registry.get(name) is not None:
            raise CommandRegistrationError(f"Command {name!r} is already registered")
    for name in names:
        registry.register_command(
            name=name,
            help=(
                "Present a saved full JSON result without replaying its operation"
                if name == "present-receipt"
                else "Publish implementation then separately close through the same original owners; not atomic."
                if name == "publish-close"
                else f"Invoke {_ISSUE_OPERATION_REFS[name]} through the selected FS provider."
            ),
            configure_parser=partial(_configure_issue_command, command=name),
            handle=_handle_issue,
            source="aware_issue_cli",
            operation_ref=_ISSUE_OPERATION_REFS.get(name),
            projection_ref=f"aware_issue_cli.{name.replace('-', '_')}"
            if name in {"present-receipt", "publish-close"}
            else None,
        )


def _parser(registry: AwareCommandRegistry) -> argparse.ArgumentParser:
    return build_parser(registry, prog="aware-issue-cli")


def _configure_issue_command(parser: argparse.ArgumentParser, *, command: str) -> None:
    if command == "present-receipt":
        _configure_present(parser)
    elif command == "resolve-read-projection":
        _target_arguments(parser)
    elif command == "ensure-snapshot":
        _configure_ensure(parser)
    elif command in {"commit-workspace", "publish-close"}:
        _configure_commit(parser)
        if command == "publish-close":
            parser.add_argument("--resolution", required=True)
            parser.add_argument("--verified-by", action="append", required=True)
            parser.add_argument("--client-intent-id", required=True)
    else:
        _mutation_arguments(parser)
        if command == "set-owner":
            parser.add_argument("--new-owner-ref", required=True)
        elif command == "bind-scope":
            parser.add_argument("--scope-path", action="append", default=[])
        elif command == "append-update":
            parser.add_argument("--message", required=True)
            parser.add_argument("--outcome", default="info")
        elif command == "append-evidence":
            parser.add_argument("--path", required=True)
            parser.add_argument("--description")
        elif command == "close":
            parser.add_argument("--resolution", required=True)
            parser.add_argument("--verified-by", action="append", required=True)
            parser.add_argument("--publication-receipt-ref", required=True)
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary" if command == "present-receipt" else "json",
        help="json retains the full result; summary omits only historical recorded evidence with visible digest/access metadata",
    )


def _configure_present(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--receipt-path",
        required=True,
        help="Saved full JSON file; relative to process working directory",
    )
    parser.add_argument(
        "--expected-receipt-sha256",
        help="Optional sha256:<hex> of exact saved file bytes, not Issue or manifest bytes",
    )


def _configure_ensure(ensure: argparse.ArgumentParser) -> None:
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


def _configure_commit(commit_workspace: argparse.ArgumentParser) -> None:
    _target_arguments(commit_workspace)
    commit_workspace.add_argument("--expected-issue-source-sha256", required=True)
    commit_workspace.add_argument("--path", action="append", required=True)
    commit_workspace.add_argument("--message", required=True)
    commit_workspace.add_argument("--dry-run", action="store_true")
    commit_workspace.add_argument("--actor-ref", required=True)
    commit_workspace.add_argument("--actor-evidence-ref", required=True)


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
    registry = AwareCommandRegistry()
    register_issue_commands(registry)
    parser = _parser(registry)
    args = parser.parse_args(argv)
    return dispatch_command(
        registry,
        args=args,
        parser=parser,
        argv=sys.argv[1:] if argv is None else argv,
    )


def _handle_issue(invocation: AwareCommandInvocation) -> int:
    args = invocation.args
    command = invocation.command.name
    if command == "present-receipt":
        return _present_receipt(args)
    try:
        provider = FilesystemIssueOperationProvider(
            repository_root=args.repository_root,
            protocol_source_ref=args.protocol_source,
        )
        repository_client = (
            create_repository_client(
                provider=provider, repository_root=args.repository_root
            )
            if command in {"commit-workspace", "close", "publish-close"}
            else None
        )
        client = IssueSdkOperationClient(
            provider=provider, repository_client=repository_client
        )
        if command == "publish-close":
            return _publish_close(args, client)
        if command == "resolve-read-projection":
            result = client.resolve_read_projection(
                IssueReadProjectionResolveRequest(issue_ref=args.issue_ref)
            )
        elif command == "ensure-snapshot":
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
        elif command == "start-progress":
            result = client.start_issue_progress(
                IssueStartProgressRequest(**_mutation_payload(args))
            )
        elif command == "block":
            result = client.block_issue(IssueBlockRequest(**_mutation_payload(args)))
        elif command == "resume":
            result = client.resume_issue(IssueResumeRequest(**_mutation_payload(args)))
        elif command == "set-owner":
            result = client.set_issue_owner(
                IssueSetOwnerRequest(
                    **_mutation_payload(args),
                    new_owner_ref=args.new_owner_ref,
                )
            )
        elif command == "bind-scope":
            result = client.bind_issue_scope_paths(
                IssueBindScopePathsRequest(
                    **_mutation_payload(args),
                    scope_paths=tuple(args.scope_path),
                )
            )
        elif command == "append-update":
            result = client.append_issue_update(
                IssueAppendUpdateRequest(
                    **_mutation_payload(args),
                    message=args.message,
                    outcome=args.outcome,
                )
            )
        elif command == "append-evidence":
            result = client.append_issue_evidence(
                IssueAppendEvidenceRequest(
                    **_mutation_payload(args),
                    path=args.path,
                    description=args.description,
                )
            )
        elif command == "close":
            result = client.close_issue(
                IssueCloseRequest(
                    **_mutation_payload(args),
                    resolution=args.resolution,
                    verified_by=tuple(args.verified_by),
                    publication_receipt_ref=args.publication_receipt_ref,
                )
            )
        elif command == "commit-workspace":
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
            raise AssertionError(f"unsupported command: {command}")
    except IssueRepositoryPublicationRefusal as error:
        payload = _repository_refusal_payload(
            error, args.issue_ref, _ISSUE_OPERATION_REFS.get(command)
        )
        print(
            json.dumps(
                summarize_result(payload) if args.format == "summary" else payload,
                sort_keys=True,
            )
        )
        return 2
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
    except (TypeError, ValueError, OSError) as error:
        operation_ref = _ISSUE_OPERATION_REFS.get(command)
        payload: dict[str, object] = {
            "operation_ref": operation_ref,
            "outcome": "malformed",
            "diagnostics": [f"request_invalid:{type(error).__name__}"],
            "authorizes_retry": False,
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
        "planned",
        "completed",
        IssueReadProjectionResolveOutcome.FOUND,
        IssueMutationOutcome.APPLIED,
        IssueMutationOutcome.IDEMPOTENT,
        IssuePublicationOutcome.PLANNED,
        IssuePublicationOutcome.APPLIED,
    }
    return 0 if successful else 2


def _publish_close(args, client):
    """Explicit two-effect composition; never recover authority from a receipt.

    Preconstruct both intents before the first effect. Close uses the caller's
    original Issue CAS guard; it is never silently refreshed after publication.
    """
    from dataclasses import replace

    publication_request = IssueCommitWorkspaceRequest(
        issue_ref=args.issue_ref,
        expected_issue_source_sha256=args.expected_issue_source_sha256,
        target_paths=tuple(args.path),
        message=args.message,
        actor_ref=args.actor_ref,
        actor_evidence_ref=args.actor_evidence_ref,
        dry_run=args.dry_run,
    )
    # A placeholder is validated as intent data only, not used as authority.
    close_request = IssueCloseRequest(
        issue_ref=args.issue_ref,
        expected_source_sha256=args.expected_issue_source_sha256,
        client_intent_id=args.client_intent_id,
        actor_ref=args.actor_ref,
        actor_evidence_ref=args.actor_evidence_ref,
        resolution=args.resolution,
        verified_by=tuple(args.verified_by),
        publication_receipt_ref="git:" + "0" * 40,
    )
    publication = client.commit_workspace(publication_request)
    records = [publication.to_wire()]
    # This is consumer sequencing over explicit owner disposition, not an
    # authorization port. Genuine closeout independently verifies the parent.
    if publication.outcome == "completed" and not args.dry_run:
        receipt = "git:" + records[0]["workspace_result"]["commit_hash"]
        try:
            closed = client.close_issue(
                replace(close_request, publication_receipt_ref=receipt)
            )
            records.append(closed.to_wire())
        except IssueRepositoryPublicationRefusal as error:
            records.append(
                _repository_refusal_payload(
                    error, args.issue_ref, close_request.operation_ref
                )
            )
    payload = {
        "contract": "aware.issue.publish-close-presentation.v1",
        "projection_ref": "aware_issue_cli.publish_close",
        "issue_ref": args.issue_ref,
        "outcome": records[-1]["outcome"],
        "receipts": records,
        "atomic": False,
        "authorizes_retry": False,
        "authority_restored": False,
    }
    print(
        json.dumps(
            summarize_result(payload) if args.format == "summary" else payload,
            sort_keys=True,
        )
    )
    return (
        0
        if (args.dry_run and publication.outcome == "planned")
        or (len(records) == 2 and records[-1]["outcome"] == "completed")
        else 2
    )


def _repository_refusal_payload(error, issue_ref, operation_ref):
    return {
        "contract": "aware.issue.repository-consumer-refusal.v1",
        "operation_ref": operation_ref,
        "issue_ref": issue_ref,
        "outcome": "refused",
        "code": error.code,
        "phase": "consumer_return",
        "effect": "unknown",
        "authorizes_retry": False,
        "authority_restored": False,
        "result_validation_complete": error.result_validation_complete,
        "consumer_result_validation": error.consumer_result_validation,
        "consumer_result": None
        if error.consumer_result is None
        else error.consumer_result.to_wire(),
        "diagnostics": list(error.diagnostics),
    }


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
            or not (
                isinstance(payload.get("operation_ref"), str)
                or (
                    payload.get("projection_ref") == "aware_issue_cli.publish_close"
                    and payload.get("contract")
                    == "aware.issue.publish-close-presentation.v1"
                )
            )
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
