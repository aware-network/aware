"""Thin explicit actions over Workspace's durable review SDK, never a writer."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry

from ._review_input import ReferenceInputError, input_observation, read_result_reference
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
        descriptions = {
            "show": (
                "Read a historical SetupReviewRecord only; no current-use authority. "
                "For retained refusals, outcomes or other evidence kinds, use "
                "aware workspace review evidence with the same explicit roots and exact reference."
            ),
            "evidence": (
                "Read original retained evidence using its exact SDK reference, "
                "including refusals and outcomes. Returned bytes may be the original "
                "command capture, not the reference container's schema. Read-only; "
                "does not renew admission or a decision."
            ),
        }
        description = descriptions.get(name)
        action = actions.add_parser(name, help=description, description=description)
        action.add_argument("--repository-root", required=True, type=Path)
        action.add_argument("--evidence-root", required=True, type=Path)
        action.add_argument("--json", action="store_true")
        if name == "show":
            action.add_argument(
                "--focus",
                choices=("overview", "scope", "files", "guards"),
                help="Explicit historical human view; incompatible with --json. Omit for unchanged output.",
            )
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
            reference = action.add_mutually_exclusive_group(required=True)
            reference.add_argument(
                "--reference",
                help="Exact SDK-issued SetupEvidenceRef JSON; not a file or handwritten record.",
            )
            reference.add_argument(
                "--reference-from-stdin",
                action="store_true",
                help="Read one saved Agent --json result from binary stdin; selects only top-level /reference, not approval or continuation.",
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
    if type(error) is ReferenceInputError:
        value["code"] = str(error)
    elif (input_code := getattr(error, "reference_input_code", None)) is not None:
        value["code"] = input_code
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
    from_stdin = getattr(args, "reference_from_stdin", False)
    if from_stdin:
        payload["reference_input"] = input_observation()
    try:
        if getattr(args, "focus", None) is not None and args.json:
            raise ReferenceInputError("review_focus_json_incompatible")
        selected = None
        execution = None
        if from_stdin:
            payload["stage"] = "reference_input"
            execution = _execution()
            selected = read_result_reference(sys.stdin, payload["reference_input"])
        from aware_workspace_sdk.architecture_setup import ArchitectureSetupRequest
        from aware_workspace_sdk.architecture_setup_review import (
            WorkspaceSetupReviewClient,
            concise_result,
        )
        from aware_workspace_sdk.architecture_setup_review_codec import (
            review_value_from_json,
            review_value_from_payload,
            review_value_to_payload,
        )
        from aware_workspace_sdk.architecture_setup_review_values import (
            ReviewedSetupApplyInputs,
            SetupApplyDecision,
            SetupEvidenceRef,
            SetupReviewRequest,
            SetupTarget,
        )

        if execution is None:
            execution = _execution()
        reference = (
            None
            if args.review_action == "prepare"
            else review_value_from_payload(SetupEvidenceRef, selected)
            if from_stdin
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


def _completion_text(value: Any) -> str:
    return (
        "true"
        if value is True
        else "false"
        if value is False
        else "unknown/not returned"
    )


def _retention_summary(label: str, carrier: dict[str, Any]) -> str:
    retention = (carrier.get("retention") or {}).get("value") or {}
    return (
        label
        + ": "
        + _terminal_text(retention.get("status") or "unknown")
        + "; ledger complete: "
        + _completion_text(retention.get("ledger_complete"))
    )


def _resource_release_summary(payload: dict[str, Any]) -> tuple[str, str]:
    """Display original release rows without completing any owner ledger."""
    failure = payload.get("error") or {}
    retention = (failure.get("retention") or {}).get("value") or {}
    physical = (retention.get("physical_refusal") or {}).get("value") or {}
    physical_cleanup = (physical.get("cleanup") or {}).get("value") or {}
    sequence = (physical_cleanup.get("sequence") or {}).get("value") or {}
    client = (payload.get("client_cleanup") or {}).get("value") or {}
    directory = (client.get("directory") or {}).get("value") or {}
    observation = (directory.get("observation") or {}).get("value") or {}

    def release_text(row: dict[str, Any]) -> str:
        value = row.get("release")
        return (
            _terminal_text(value) if isinstance(value, str) else "unknown/not returned"
        )

    return (
        "Private evidence directory release: "
        + release_text(directory)
        + "; family ledger complete: "
        + _completion_text(observation.get("ledger_complete")),
        "Original failed-sequence release: "
        + release_text(sequence)
        + "; sequence ledger complete: "
        + _completion_text(sequence.get("ledger_complete")),
    )


def _next_observation(payload: dict[str, Any]) -> str:
    """Descriptive guidance from existing owner fields, never a next-action grant."""
    failure = payload.get("error") or {}
    if failure.get("code") == "original_review_record_required":
        return (
            "Use aware workspace review evidence for this record kind, with the "
            "same explicit roots and exact SDK reference. This read does not "
            "clear retention/cleanup uncertainty or authorize mutation."
        )
    if _incomplete_owner_evidence(payload) or payload.get("cleanup_error"):
        return (
            "Stop before further mutation; inspect this invocation's full values "
            "and any verified earlier evidence. Do not repeat scope/apply or "
            "refresh guards to recover output. No cleanup outcome is promised."
        )
    if payload.get("purpose") == "history":
        return (
            "Observe history only. Any current mutation needs its own valid "
            "admission and fresh explicit reviews; history is not a decision."
        )
    if failure.get("refusal") is not None and failure.get("code") in (
        "review_issue_changed",
        "review_authority_sources_changed",
    ):
        return (
            "Inspect the original refusal first. If you choose a new operation, "
            "explicitly prepare and review again; do not repair or refresh an "
            "old request automatically."
        )
    if failure:
        return "Inspect the original failure evidence before any further mutation; its reason alone grants no retry or fresh-operation authority."
    result = (payload.get("result") or {}).get("value") or {}
    if payload.get("ready_for_decision"):
        if result.get("decision_required") == "scope_review":
            return (
                "Review the proposed physical Issue scope. A scope request needs "
                "--accept-reviewed-effect-scope and original SDK validation."
            )
        if result.get("decision_required") == "apply_review":
            return (
                "Review the second preview and final files. An apply request needs "
                "--accept-reviewed-final-files and original SDK validation."
            )
    if result.get("product_status") == "apply_completed":
        return (
            "Observe the original outcome; do not repeat a completed apply to "
            "recreate its receipt. Issue publication/closeout remain separate."
        )
    return "Inspect the original evidence before choosing another operation; no mutation is authorized by this explanation."


def _summary(payload: dict[str, Any], *, focus: str | None = None) -> str:
    lines = [f"Workspace review {payload['action']}: {payload['status']}"]
    if focus is not None:
        lines.append(
            "Requested historical focus: "
            + _terminal_text(focus)
            + "; no current-use authority."
        )
    failure = payload.get("error") or {}
    scope = payload.get("scope_completion") or failure.get("scope_completion")
    lines.append("What happened:")
    lines.append(
        "Agent stage: " + _terminal_text(payload.get("stage", "unknown/not returned"))
    )
    if failure:
        lines.append(
            "Primary failure: "
            + _terminal_text(failure.get("code", failure.get("error_type", "unknown")))
        )
        if "phase" in failure:
            lines.append("Owner phase: " + _terminal_text(failure["phase"]))
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
    if scope is not None:
        lines.append(
            "Issue scope completion status: " + _terminal_text(scope["status"])
        )
    if failure:
        outcome = payload.get("outcome") or failure.get("outcome")
        if outcome is not None:
            lines.append(
                "Original product outcome returned: " + outcome["product_status"]
            )
    outcome = payload.get("outcome") or failure.get("outcome")
    original = None if outcome is None else outcome.get("original_evidence")
    lines.append("What changed:")
    if scope is not None:
        original_scope = scope.get("original_outcome") or {}
        lines.append(
            "Original Issue scope mutation outcome: "
            + _terminal_text(original_scope.get("outcome", "unknown/not returned"))
        )
        if payload["action"] == "scope":
            lines.append(
                "Manifest apply is a separate operation; this scope action does not invoke it."
            )
    workspace = None
    if original is not None and original.get("workspace_result") is not None:
        workspace = original["workspace_result"]["value"]
        effects = sorted(
            {effect["value"]["effect_state"] for effect in workspace["effects"]}
        )
        paths = sorted(
            {effect["value"]["primary_path"] for effect in workspace["effects"]}
        )
        lines.extend(
            (
                "Original physical effect states: "
                + ", ".join(map(_terminal_text, effects)),
                "Owner-observed effect paths: "
                + ", ".join(map(_terminal_text, paths[:8])),
                "Original Workspace durability: "
                + _terminal_text(workspace["durability"]),
                f"Original remaining effects: {len(workspace['remaining_effects'])}; scratch residue: {len(workspace['scratch_residue'])}",
            )
        )
        if len(paths) > 8:
            lines.append(
                "Additional effect paths omitted; full original evidence remains required."
            )
    elif failure.get("refusal") is not None:
        refusal = failure["refusal"]["value"]
        lines.append(
            "Product dispatch for this refused action: "
            + _terminal_text(refusal["product_dispatch"])
            + ". This does not describe historical effects or evidence writes."
        )
    else:
        lines.append(
            "Workspace manifest-apply effect observations not returned here; absence is not proof of no other effects."
            if scope is not None
            else "Product-effect observations not returned here; absence is not proof of no effects."
        )
    if (failure.get("retention") or {}).get("value", {}).get(
        "physical_refusal"
    ) is not None:
        lines.append(
            "Original physical refusal evidence is present. Its code alone does "
            "not prove spent-reuse causality or rollback of earlier effects."
        )
    if "review" in payload:
        record = payload["review"]["value"]
        request = record["request"]["value"]
        target = request["target"]["value"]
        architecture = request["architecture_request"]["value"]
        lines.extend(
            (
                "Reviewed proposal/context, not a claim these paths were applied:",
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
            if (
                focus == "guards"
                or focus == "files"
                and key != "final_files"
                or focus == "scope"
                and key == "final_files"
            ):
                continue
            paths = record[key]
            shown = paths if focus in ("scope", "files") else paths[:8]
            lines.append(
                f"{label} ({len(paths)}): " + ", ".join(map(_terminal_text, shown))
            )
            if len(paths) > len(shown):
                lines.append(
                    "Additional paths omitted; inspect --json before deciding."
                )
        if focus == "guards":
            guards = record["review_guards"]["value"]
            for key, label in (
                ("issue_source_sha256", "Original Issue byte guard"),
                ("authority_manifest_sha256", "Original authority-manifest byte guard"),
                ("plan_sha256", "Original review-plan guard"),
            ):
                lines.append(label + ": " + _terminal_text(guards.get(key)))
        if not payload.get("ready_for_decision"):
            lines.append(
                "Not ready for a decision; inspect the retained diagnostics. Do not retry automatically."
            )
    lines.append("What remains uncertain:")
    if workspace is not None:
        lines.append(
            "Original Workspace release: "
            + _terminal_text(workspace.get("release", "unknown"))
        )
        lines.append(
            "Later client cleanup does not change these original qualifications; inspect full evidence for details."
        )
    else:
        lines.append("Original Workspace release: unknown/not returned here.")
    if outcome is not None:
        lines.append(_retention_summary("Outcome evidence retention", outcome))
    if scope is not None:
        lines.append(_retention_summary("Issue scope evidence retention", scope))
    if failure:
        lines.append(_retention_summary("Evidence retention", failure))
        lines.extend(_resource_release_summary(payload))
        lines.append(
            "A confirmed resource release does not establish complete retention, "
            "composite cleanup or historical Workspace completion."
        )
        if failure.get("cleanup") is not None:
            lines.append(
                "Original owner cleanup complete: "
                + _completion_text(failure["cleanup"]["value"].get("ledger_complete"))
            )
        if "retention_error" in failure:
            lines.append(
                "Independent retention error: "
                + _terminal_text(failure["retention_error"]["error_type"])
            )
    if payload.get("client_cleanup") is not None:
        lines.append(
            "Client cleanup complete: "
            + _completion_text(
                payload["client_cleanup"]["value"].get("ledger_complete")
            )
        )
    else:
        lines.append("Client cleanup complete: unknown/not returned.")
    if payload.get("cleanup_error"):
        cleanup_error = payload["cleanup_error"]
        lines.append(
            "Independent client cleanup failure: "
            + _terminal_text(
                cleanup_error.get("code", cleanup_error.get("error_type", "unknown"))
            )
        )
    lines.append("What next (guidance, not authority): " + _next_observation(payload))
    lines.append("Where is full evidence:")
    reference = payload.get("reference")
    if reference is not None:
        kind = reference["value"].get("record_contract", "unknown")
        retention = (failure.get("retention") or {}).get("value", {})
        if failure and retention.get("status") in ("incomplete", "unknown"):
            label = "Returned reference (may identify earlier evidence; current failure capture not confirmed): "
        elif failure.get("refusal") is not None:
            label = "Owner reference (evidence only, not a review or admission): "
        else:
            label = "Reference (exact SDK JSON, reuse unchanged): "
        lines.append(
            label + json.dumps(reference, sort_keys=True, separators=(",", ":"))
        )
        lines.append("Reference container kind: " + _terminal_text(kind))
        lines.append(
            "Full retained bytes: aware workspace review evidence --repository-root "
            "<same explicit root> --evidence-root <same explicit evidence root> "
            "--reference <exact SDK JSON>. The bytes may be an original command "
            "capture, not the container schema; the reference is not mutation authority."
        )
    else:
        lines.append(
            "No SDK evidence reference was returned here. Do not invent one or redispatch to manufacture a receipt."
        )
    lines.append(
        "No automatic retry or guard refresh. show accepts historical review records only; evidence reads retained refusals/outcomes and other supported kinds."
    )
    return "\n".join(lines)


def _emit_review_output(text: str, stream: Any, *, end: str = "\n") -> bool:
    """One terminal write/flush; retire only a poisoned output buffer."""
    failed = False
    try:
        print(text, file=stream, end=end)
    except (OSError, UnicodeError):
        failed = True
    try:
        stream.flush()
    except (OSError, UnicodeError):
        failed = True
        try:
            stream.close()
        except (OSError, UnicodeError):
            pass
    return not failed


def _handle(invocation: AwareCommandInvocation) -> int:
    payload, code, raw = review_payload(invocation.args)
    focus = getattr(invocation.args, "focus", None)

    def human_summary() -> str:
        # Omitted focus preserves both the original call and its exact output.
        return _summary(payload) if focus is None else _summary(payload, focus=focus)

    try:
        if raw is not None:
            # Original UTF-8 capture, not parsed or reserialized JSON v1.
            raw_ok = _emit_review_output(raw.decode("utf-8"), sys.stdout, end="")
            cleanup = {
                "client_cleanup": payload.get("client_cleanup"),
                "error": payload.get("error"),
                "cleanup_error": payload.get("cleanup_error"),
            }
            if "reference_input" in payload:
                cleanup["reference_input"] = payload["reference_input"]
            cleanup_ok = _emit_review_output(
                json.dumps(
                    cleanup,
                    sort_keys=True,
                ),
                sys.stderr,
            )
            if not raw_ok or not cleanup_ok:
                return 130 if code == 130 else 3
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
            unavailable_capture = unavailable_capture or _incomplete_owner_evidence(
                payload
            )
            if unavailable_capture and not invocation.args.json:
                # Each stream gets one independent attempt. A summary-channel
                # failure must not suppress the available original full values.
                human_ok = _emit_review_output(
                    f"Operation exit before reporting: {code}\n"
                    + human_summary()
                    + "\nFull available values for this invocation follow on stdout. "
                    "An earlier reference need not contain this failure/cleanup; "
                    "do not repeat the operation with --json to recover it.",
                    sys.stderr,
                )
                evidence_ok = _emit_review_output(
                    json.dumps(payload, sort_keys=True), sys.stdout
                )
                return (
                    130
                    if code == 130
                    else 3
                    if not human_ok or not evidence_ok
                    else code
                )
            output_ok = _emit_review_output(
                json.dumps(payload, sort_keys=True)
                if invocation.args.json
                else f"Operation exit before reporting: {code}\n" + human_summary(),
                sys.stdout,
            )
            if not output_ok:
                # No prior stderr attempt in this branch. Preserve available
                # original values there once rather than repeating an operation.
                _emit_review_output(json.dumps(payload, sort_keys=True), sys.stderr)
                return 130 if code == 130 else 3
    except (OSError, UnicodeError):
        # Output failure cannot erase interruption or cause redispatch/cleanup.
        return 130 if code == 130 else 3
    return code
