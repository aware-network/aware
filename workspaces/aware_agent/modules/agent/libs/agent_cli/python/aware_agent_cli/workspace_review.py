"""Thin explicit actions over Workspace's durable review SDK, never a writer."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry

from .initialization import _execution


def register_workspace_review_command(registry: AwareCommandRegistry) -> None:
    registry.register_command(
        name="review",
        help="Prepare, inspect and explicitly invoke SDK-carried repository setup.",
        description=(
            "Repository-manifest A1 only. Prepare, review physical scope, explicitly "
            "bind it, review the second preview, then explicitly apply final files. "
            "No guard copying, automatic refresh, retry, service or record writer."
        ),
        configure_parser=_configure,
        handle=_handle,
        source="aware_agent_cli",
        projection_ref="aware.agent.workspace-review.v1",
    )


def _configure(parser: argparse.ArgumentParser) -> None:
    actions = parser.add_subparsers(dest="review_action", required=True)
    for name in ("prepare", "show", "scope", "apply", "evidence"):
        action = actions.add_parser(name)
        action.add_argument("--repository-root", required=True, type=Path)
        action.add_argument("--evidence-root", required=True, type=Path)
        action.add_argument("--json", action="store_true")
        if name == "prepare":
            action.add_argument("--issue-ref", required=True)
            action.add_argument("--issue-path", required=True)
            action.add_argument(
                "--authority-manifest-locator", default="aware.protocol.toml"
            )
            action.add_argument("--name", required=True)
            action.add_argument("--license-expression", required=True)
            action.add_argument("--actor-ref", required=True)
            action.add_argument("--actor-evidence-ref", required=True)
            action.add_argument("--include-issue-lifecycle", action="store_true")
        else:
            action.add_argument(
                "--reference",
                required=True,
                help="Exact SDK-issued SetupEvidenceRef JSON; not a file or handwritten record.",
            )
        if name in ("prepare", "scope", "apply"):
            action.add_argument("--client-intent-id", required=True)
        if name == "scope":
            action.add_argument(
                "--accept-reviewed-effect-scope", action="store_true", required=True
            )
        if name == "apply":
            action.add_argument(
                "--accept-reviewed-final-files", action="store_true", required=True
            )


def _outcome_payload(value: Any) -> dict[str, Any]:
    from aware_workspace_sdk.architecture_setup_command_values import (
        command_value_to_payload,
    )
    from aware_workspace_sdk.architecture_setup_review_codec import (
        review_value_to_payload,
    )

    return {
        "product_status": value.product_status,
        "reference": None
        if value.reference is None
        else review_value_to_payload(value.reference),
        "retention": review_value_to_payload(value.retention),
        "diagnostics": list(value.diagnostics),
        "authorizes_retry": value.authorizes_retry,
        # Incomplete retention must not hide already known publication evidence.
        "original_evidence": None
        if value.original_evidence is None
        else command_value_to_payload(value.original_evidence),
    }


def _scope_payload(value: Any) -> dict[str, Any]:
    from aware_issue_sdk.operation import IssueMutationError, IssueMutationResult
    from aware_issue_sdk.operation_codec import encode_issue_result
    from aware_workspace_sdk.architecture_setup_review_codec import (
        review_value_to_payload,
    )

    original = value.original_outcome
    if type(original) is IssueMutationResult:
        original_wire = encode_issue_result(original)
    elif type(original) is IssueMutationError:
        original_wire = original.to_wire()
    else:
        original_wire = review_value_to_payload(original)
    return {
        "status": value.status,
        "reference": None
        if value.reference is None
        else review_value_to_payload(value.reference),
        "original_outcome": original_wire,
        "retention": review_value_to_payload(value.retention),
        "diagnostics": list(value.diagnostics),
    }


def _cleanup_payload(value: Any) -> dict[str, Any]:
    from aware_workspace_sdk.architecture_setup_review_codec import (
        review_value_to_payload,
    )

    return review_value_to_payload(value)


def _exception_metadata(error: BaseException) -> dict[str, Any]:
    result: dict[str, Any] = {
        "error_type": type(error).__name__,
        "interruption": not isinstance(error, Exception),
    }
    if error.__cause__ is not None:
        result["cause_type"] = type(error.__cause__).__name__
    return result


def _error_payload(error: BaseException) -> dict[str, Any]:
    value: dict[str, Any] = {
        "error_type": type(error).__name__,
        "authorizes_retry": False,
    }
    try:
        from aware_workspace_sdk.architecture_setup_review_codec import (
            SetupReviewValueError,
            review_value_to_payload,
        )
        from aware_workspace_sdk.architecture_setup_review_values import (
            SetupReviewError,
            SetupReviewFailure,
        )
    except ImportError:
        return value
    if type(error) is SetupReviewValueError:
        value["code"] = str(error)
    failure = (
        error.failure
        if type(error) is SetupReviewError
        else getattr(error, "setup_review_failure", None)
    )
    if type(failure) is SetupReviewFailure:
        value.update(
            code=failure.code,
            phase=failure.phase,
            interruption=failure.interruption,
            retention=review_value_to_payload(failure.retention),
            reference=None
            if failure.reference is None
            else review_value_to_payload(failure.reference),
            outcome=None
            if failure.outcome is None
            else _outcome_payload(failure.outcome),
            cleanup=None
            if failure.cleanup is None
            else review_value_to_payload(failure.cleanup),
        )
        # These additive owner fields may be absent in older SDK carriers.
        # Absence does not fabricate a refusal or imply that no reads occurred.
        reads = getattr(failure, "reads", None)
        if reads is not None:
            from aware_file_system.private_directory import (
                private_directory_value_to_payload,
            )

            value["reads"] = []
            for index, read in enumerate(reads):
                try:
                    value["reads"].append(private_directory_value_to_payload(read))
                except BaseException as projection_error:  # noqa: BLE001 -- retain primary evidence if a bounded owner codec cannot encode a read
                    value["reads"].append(None)
                    value.setdefault("presentation_errors", {})[f"reads[{index}]"] = (
                        _exception_metadata(projection_error)
                    )
        refusal = getattr(failure, "refusal", None)
        if refusal is not None:
            try:
                value["refusal"] = review_value_to_payload(refusal)
            except BaseException as projection_error:  # noqa: BLE001 -- no raw-record fallback for an unencodable owner value
                value.setdefault("presentation_errors", {})["refusal"] = (
                    _exception_metadata(projection_error)
                )
        retention_error = (
            getattr(error, "retention_error", None)
            if type(error) is SetupReviewError
            else getattr(error, "setup_review_retention_error", None)
        )
        if isinstance(retention_error, BaseException):
            # Capture interruption can be the primary interrupt object itself.
            # Preserve its identity relationship without recursively encoding it.
            value["retention_error"] = _exception_metadata(retention_error)
            value["retention_error"]["same_as_primary_exception"] = (
                retention_error is error
            )
    completion = getattr(error, "setup_scope_completion", None)
    if completion is not None:
        value["scope_completion"] = _scope_payload(completion)
        original = value["scope_completion"]["original_outcome"]
        if "code" in original:
            value["code"] = original["code"]
        if completion.reference is not None:
            value["reference"] = review_value_to_payload(completion.reference)
    retention_error = getattr(error, "setup_scope_retention_error", None)
    if retention_error is not None:
        value["scope_retention_error"] = _error_payload(retention_error)
    if error.__cause__ is not None:
        value["cause_type"] = type(error.__cause__).__name__
    return value


def _incomplete_owner_evidence(payload: dict[str, Any]) -> bool:
    """Project original retention outcomes, independently of later cleanup."""
    retention = payload.get("retention", {}).get("value", {})
    cleanup = payload.get("cleanup")
    if cleanup is not None and not cleanup["value"]["ledger_complete"]:
        return True
    if retention.get("status") in ("incomplete", "unknown") or (
        retention.get("status") in ("captured", "published")
        and not retention.get("ledger_complete")
    ):
        return True
    if (
        payload.get("status") == "incomplete"
        or payload.get("product_status") == "incomplete"
    ):
        return True
    if (
        payload.get("original_evidence") is not None
        and payload.get("reference") is None
    ):
        return True
    return any(
        _incomplete_owner_evidence(value)
        for key in ("outcome", "error", "scope_completion", "scope_retention_error")
        if (value := payload.get(key)) is not None
    )


def _scope(
    client: Any,
    first: Any,
    args: argparse.Namespace,
    execution: str,
    payload: dict[str, Any],
) -> Any:
    from aware_issue_fs_adapter.provider import FilesystemIssueOperationProvider
    from aware_issue_sdk.operation import (
        IssueMutationError,
        IssueProviderResultError,
        IssueSdkOperationClient,
    )
    from aware_workspace_sdk.architecture_setup_review_codec import (
        review_value_to_payload,
    )
    from aware_workspace_sdk.architecture_setup_review_values import (
        SetupScopeDecision,
        SetupUnknownScopeOutcome,
    )

    # Resolve the original provider before creating a dispatch intent. Never use
    # the parser/CLI, decode Markdown, or construct an admission ourselves.
    issuer = IssueSdkOperationClient(
        FilesystemIssueOperationProvider(
            repository_root=args.repository_root,
            protocol_source_ref=first.record.request.target.authority_manifest_locator,
        )
    )
    # Stable, domain-separated child intent, not a collision retry or new guard.
    # Validate it through the original codec before the first mutation.
    next_request = replace(
        first.record.request,
        client_intent_id=args.client_intent_id + ":second-preview",
    )
    review_value_to_payload(next_request)
    payload["stage"] = "scope_decision"
    inputs = client.record_review_decision(
        first.reference,
        decision=SetupScopeDecision(
            first.reference,
            "accept_reviewed_effect_scope",
            execution,
            args.client_intent_id,
        ),
    )
    payload["stage"] = "issue_scope"
    try:
        original = issuer.bind_issue_scope_paths(inputs.record.request)
    except (
        BaseException
    ) as error:  # retain cancellation and uncertain dispatch, never retry
        if (
            type(error) is IssueProviderResultError
            and type(error.failure) is IssueMutationError
        ):
            outcome = error.failure
        else:
            outcome = SetupUnknownScopeOutcome(
                "unknown",
                type(error).__name__,
                not isinstance(error, Exception),
                ("scope_dispatch_return_unavailable",),
            )
        try:
            completion = client.record_scope_outcome(inputs, outcome=outcome)
            BaseException.__setattr__(error, "setup_scope_completion", completion)
        except BaseException as retention_error:  # noqa: BLE001 -- do not replace the primary Issue failure
            BaseException.__setattr__(
                error, "setup_scope_retention_error", retention_error
            )
        raise
    payload["stage"] = "scope_retention"
    completion = client.record_scope_outcome(inputs, outcome=original)
    payload["scope_completion"] = _scope_payload(completion)
    if completion.reference is not None:
        payload["reference"] = review_value_to_payload(completion.reference)
    if completion.continuation is None:
        return None
    payload["stage"] = "second_preview"
    return client.preview_review(
        next_request,
        scope_continuation=completion.continuation,
    )


def review_payload(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], int, bytes | None]:
    """Presentation transport only; all retained values/decisions are SDK-owned."""
    payload: dict[str, Any] = {
        "contract": "aware.agent.workspace-review.v1",
        "action": args.review_action,
        "status": "refused",
        "stage": "preflight",
        "authorizes_retry": False,
    }
    client = None
    raw = None
    code = 2
    try:
        from aware_workspace_sdk.architecture_setup import ArchitectureSetupRequest
        from aware_workspace_sdk.architecture_setup_review import (
            WorkspaceSetupReviewClient,
            concise_result,
        )
        from aware_workspace_sdk.architecture_setup_review_codec import (
            review_value_from_json,
            review_value_to_payload,
        )
        from aware_workspace_sdk.architecture_setup_review_values import (
            ReviewedSetupApplyInputs,
            SetupApplyDecision,
            SetupEvidenceRef,
            SetupReviewRequest,
            SetupTarget,
        )

        execution = _execution()
        reference = (
            None
            if args.review_action == "prepare"
            else review_value_from_json(SetupEvidenceRef, args.reference)
        )
        target = (
            SetupTarget(
                str(args.repository_root),
                args.issue_ref,
                args.issue_path,
                args.authority_manifest_locator,
            )
            if reference is None
            else reference.target
        )
        payload["stage"] = "client_acquisition"
        client = WorkspaceSetupReviewClient.filesystem(
            repository_root=args.repository_root,
            evidence_root=args.evidence_root,
            execution_id=execution,
            authority_manifest_locator=target.authority_manifest_locator,
        )
        value: Any = None
        if args.review_action == "prepare":
            payload["stage"] = "first_preview"
            value = client.preview_review(
                SetupReviewRequest(
                    target,
                    ArchitectureSetupRequest(
                        "repository",
                        name=args.name,
                        license_expression=args.license_expression,
                    ),
                    execution,
                    args.client_intent_id,
                    args.actor_ref,
                    args.actor_evidence_ref,
                    args.include_issue_lifecycle,
                )
            )
        elif args.review_action == "evidence":
            assert reference is not None
            payload["stage"] = "evidence_read"
            read = client.read_evidence(reference, expected_target=target)
            raw = read.raw_bytes
            payload["reference"] = review_value_to_payload(read.reference)
        else:
            assert reference is not None
            payload["stage"] = "review_read"
            payload["purpose"] = (
                "history" if args.review_action == "show" else "current_use"
            )
            value = client.read_review(
                reference,
                expected_target=target,
                purpose="history" if args.review_action == "show" else "current_use",
            )
            if args.review_action == "scope":
                value = _scope(client, value, args, execution, payload)
            elif args.review_action == "apply":
                payload["stage"] = "apply_decision"
                inputs = client.record_review_decision(
                    value.reference,
                    decision=SetupApplyDecision(
                        value.reference,
                        "accept_reviewed_final_files",
                        execution,
                        args.client_intent_id,
                    ),
                )
                if type(inputs) is not ReviewedSetupApplyInputs:
                    raise TypeError("original_reviewed_apply_inputs_required")
                payload["stage"] = "apply"
                value = client.apply_reviewed(
                    inputs, client_intent_id=args.client_intent_id
                )
                # Keep original evidence if concise projection cannot be supplied.
                payload["outcome"] = _outcome_payload(value)
                if value.reference is not None:
                    payload["reference"] = review_value_to_payload(value.reference)
        if value is not None:
            payload["result"] = review_value_to_payload(concise_result(value))
            if args.review_action != "apply":
                payload["review"] = review_value_to_payload(value.record)
                payload["reference"] = review_value_to_payload(value.reference)
                payload["ready_for_decision"] = value.record.ready_for_decision
                code = 0 if value.record.ready_for_decision else 2
            else:
                code = 0 if value.product_status == "apply_completed" else 2
        elif raw is not None:
            code = 0
        payload["status"] = "completed" if code == 0 else "refused"
    except BaseException as error:  # noqa: BLE001 -- command boundary, no dispatch or evidence reconstruction
        payload["error"] = _error_payload(error)
        if "reference" not in payload and payload["error"].get("reference") is not None:
            payload["reference"] = payload["error"]["reference"]
        code = 130 if not isinstance(error, Exception) else 2
    finally:
        if client is not None:
            try:
                cleanup = client.release_client()
                payload["client_cleanup"] = _cleanup_payload(cleanup)
                if not cleanup.ledger_complete:
                    code = 3 if code != 130 else code
                    payload["status"] = "incomplete"
            except BaseException as error:  # noqa: BLE001 -- keep the original result/failure and independent cleanup
                payload["cleanup_error"] = _error_payload(error)
                code = 130 if not isinstance(error, Exception) or code == 130 else 3
                payload["status"] = "incomplete"
    if _incomplete_owner_evidence(payload):
        payload["status"] = "incomplete"
        code = 130 if code == 130 else 3
    presentation_errors = payload.get("error", {}).get("presentation_errors", {})
    if presentation_errors:
        payload["status"] = "incomplete"
        code = (
            130
            if code == 130
            or any(e["interruption"] for e in presentation_errors.values())
            else 3
        )
    return payload, code, raw


def _terminal_text(value: str) -> str:
    """Quoted ASCII display only; never alter the original SDK value."""
    return json.dumps(value, ensure_ascii=True)


def _summary(payload: dict[str, Any]) -> str:
    lines = [f"Workspace review {payload['action']}: {payload['status']}"]
    if payload.get("purpose") == "history":
        lines.append("Historical review only; this read grants no current admission.")
    if "result" in payload:
        result = payload["result"]["value"]
        lines.extend(
            (
                f"Outcome: {result['product_status']}",
                f"Decision required: {result['decision_required']}",
            )
        )
    if "scope_completion" in payload:
        completion = payload["scope_completion"]
        lines.append("Issue scope outcome: " + completion["status"])
    if "error" in payload:
        outcome = payload.get("outcome") or payload["error"].get("outcome")
        if outcome is not None:
            lines.append(
                "Original product outcome retained: " + outcome["product_status"]
            )
    outcome = payload.get("outcome") or payload.get("error", {}).get("outcome")
    original = None if outcome is None else outcome["original_evidence"]
    if original is not None and original["workspace_result"] is not None:
        workspace = original["workspace_result"]["value"]
        effects = sorted(
            {effect["value"]["effect_state"] for effect in workspace["effects"]}
        )
        lines.extend(
            (
                "Original Workspace release: " + _terminal_text(workspace["release"]),
                "Original physical effect states: "
                + ", ".join(map(_terminal_text, effects)),
                "Original Workspace durability: "
                + _terminal_text(workspace["durability"]),
                f"Original remaining effects: {len(workspace['remaining_effects'])}; scratch residue: {len(workspace['scratch_residue'])}",
                "Later client cleanup does not change these original qualifications; inspect full evidence for details.",
            )
        )
    if "review" in payload:
        record = payload["review"]["value"]
        request = record["request"]["value"]
        target = request["target"]["value"]
        architecture = request["architecture_request"]["value"]
        lines.extend(
            (
                f"Request: repository {_terminal_text(architecture['name'])}; license {_terminal_text(architecture['license_expression'])}",
                f"Issue: {_terminal_text(target['issue_tag'])} at {_terminal_text(target['issue_path'])}",
                f"Authority manifest: {_terminal_text(target['authority_manifest_locator'])}",
                "Reviewed guards remain owner-carried; --json exposes their exact original values.",
            )
        )
        for key, label in (
            ("physical_scope", "Issue physical scope"),
            ("final_files", "Apply final files"),
            ("existing_scope", "Preserved Issue scope"),
        ):
            paths = record[key]
            lines.append(
                f"{label} ({len(paths)}): " + ", ".join(map(_terminal_text, paths[:8]))
            )
            if len(paths) > 8:
                lines.append(
                    "Additional paths omitted; inspect --json before deciding."
                )
        if not payload.get("ready_for_decision"):
            lines.append(
                "Not ready for a decision; inspect the retained diagnostics. Do not retry automatically."
            )
    if "reference" in payload:
        lines.append(
            (
                "Owner reference (evidence only, not a review or admission): "
                if payload.get("error", {}).get("refusal") is not None
                else "Reference (exact SDK JSON, reuse unchanged): "
            )
            + json.dumps(payload["reference"], sort_keys=True, separators=(",", ":"))
        )
    if "error" in payload:
        failure = payload["error"]
        lines.append(
            "Primary failure: "
            + _terminal_text(failure.get("code", failure["error_type"]))
        )
        if "phase" in failure:
            lines.append("Owner phase: " + _terminal_text(failure["phase"]))
        if "retention" in failure:
            retention = failure["retention"]["value"]
            lines.append(
                "Evidence retention: "
                + _terminal_text(retention["status"])
                + "; ledger complete: "
                + str(retention["ledger_complete"]).lower()
            )
        if failure.get("refusal") is not None:
            refusal = failure["refusal"]["value"]
            lines.append(
                "Product dispatch for this refused action: "
                + _terminal_text(refusal["product_dispatch"])
                + ". This does not describe historical effects or evidence writes."
            )
        if failure.get("cleanup") is not None:
            lines.append(
                "Original owner cleanup complete: "
                + str(failure["cleanup"]["value"]["ledger_complete"]).lower()
            )
        if "retention_error" in failure:
            lines.append(
                "Independent retention error: "
                + _terminal_text(failure["retention_error"]["error_type"])
            )
    if "client_cleanup" in payload:
        lines.append(
            "Client cleanup complete: "
            + str(payload["client_cleanup"]["value"]["ledger_complete"]).lower()
        )
    lines.append(
        "No automatic retry or guard refresh. Full retained bytes: review evidence --reference <SDK JSON>."
    )
    return "\n".join(lines)


def _handle(invocation: AwareCommandInvocation) -> int:
    payload, code, raw = review_payload(invocation.args)
    try:
        if raw is not None:
            # Original UTF-8 capture, not parsed or reserialized JSON v1.
            sys.stdout.write(raw.decode("utf-8"))
            print(
                json.dumps(
                    {
                        "client_cleanup": payload.get("client_cleanup"),
                        "error": payload.get("error"),
                        "cleanup_error": payload.get("cleanup_error"),
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
        else:
            failure = payload.get("error", {})
            outcome = payload.get("outcome") or payload.get("error", {}).get("outcome")
            scope = payload.get("scope_completion") or payload.get("error", {}).get(
                "scope_completion"
            )
            unavailable_capture = (
                outcome is not None
                and (
                    outcome["reference"] is None
                    or outcome["retention"]["value"]["status"] != "published"
                    or not outcome["retention"]["value"]["ledger_complete"]
                )
            ) or (scope is not None and scope["status"] == "incomplete")
            failed_retention = failure.get("retention", {}).get("value", {})
            unavailable_capture = (
                unavailable_capture
                or bool(failure.get("presentation_errors"))
                or (
                    failed_retention.get("status") in ("incomplete", "unknown")
                    or failed_retention.get("status") in ("published", "captured")
                    and not failed_retention.get("ledger_complete")
                )
            )
            print(
                json.dumps(payload, sort_keys=True)
                if invocation.args.json or unavailable_capture
                else _summary(payload)
            )
    except (OSError, UnicodeError):
        # Output failure cannot erase interruption or cause redispatch/cleanup.
        return 130 if code == 130 else 3
    return code
