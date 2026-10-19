"""Sequential SDK composition only; no filesystem writer or domain policy."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry

if TYPE_CHECKING:
    from aware_protocol_sdk.bootstrap import ProtocolBootstrapError
    from aware_workspace_sdk.repository_preparation import RepositoryPreparationError


def register_init_command(registry: AwareCommandRegistry) -> None:
    registry.register_command(
        name="init",
        help="Preview Issue-first setup or explicitly opt into create-first bootstrap.",
        description=(
            "Preview by default. --create-repository admits an empty repository; "
            "--apply requests effects. Both SDK owners retain separate evidence. "
            "Default issue-first creates no seed commit, staging, remote, Issue or service. "
            "Explicit create-first commits one Protocol manifest after interactive confirmation; "
            "it creates no Project, Goal, Issue or AGENTS.md."
        ),
        configure_parser=_configure_parser,
        handle=_handle_init,
        source="aware_agent_cli",
        projection_ref="aware.agent.init.v1",
    )


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root", "--repository-root", dest="repository_root", required=True
    )
    parser.add_argument("--create-repository", action="store_true")
    parser.add_argument(
        "--profile", choices=("issue-first", "create-first"), default="issue-first"
    )
    parser.add_argument("--issue-root", default="docs/issues")
    parser.add_argument(
        "--goal-root", help="Create-first only; default belongs to Protocol."
    )
    parser.add_argument(
        "--project-root", help="Create-first only; default belongs to Protocol."
    )
    parser.add_argument("--no-agent-contract", action="store_true")
    intent = parser.add_mutually_exclusive_group()
    intent.add_argument("--dry-run", action="store_true")
    intent.add_argument("--apply", action="store_true")
    intent.add_argument(
        "--recover",
        action="store_true",
        help="Create-first only: read the original retained configuration result; never retry or repair.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="json",
        help=(
            "json (default): full original receipts on stdout. summary: human "
            "explanation on stdout and full receipt JSON on stderr in this same "
            "invocation; retain both streams, never rerun apply for evidence."
        ),
    )


def _execution() -> str:
    # Harness discovery is correlation, never an authenticated actor issuer.
    candidates = [
        prefix + os.environ[name].strip()
        for name, prefix in (
            ("CODEX_THREAD_ID", "codex-"),
            ("CLAUDE_CODE_SESSION_ID", "claude_code-"),
        )
        if os.environ.get(name, "").strip()
    ]
    if len(candidates) != 1 or any(c.isspace() for c in candidates[0]):
        raise ValueError("unambiguous_provider_execution_required")
    return candidates[0]


def _unknown(error: BaseException, *, invoked: bool) -> dict[str, Any]:
    return {
        "code": "initializer_stage_unverified",
        "error_type": type(error).__name__,
        "diagnostics": [str(error)],
        "effect": "unknown" if invoked else "none",
        "operation_invoked": invoked,
        "ledger_complete": False,
        "authorizes_retry": False,
    }


def _invoke(
    client: Any,
    request: Any,
    *,
    apply: bool,
    plan_method: str,
    admit_method: str,
    operation: str,
    error_type: type[ProtocolBootstrapError | RepositoryPreparationError],
    encode: Callable[[Any], dict[str, Any]],
    stage: dict[str, Any],
) -> bool:
    """Release this invocation's plan without masking either owner carrier."""
    plan = None
    invoked = False
    try:
        if apply:
            plan = getattr(client, plan_method)(request)
            admission = getattr(client, admit_method)(plan)
        else:
            admission = None
        invoked = True
        result = getattr(client, operation)(request, admission=admission)
        stage["result"] = encode(result)
        stage["status"] = "refused" if result.outcome == "refused" else "completed"
    except error_type as error:
        stage["status"] = "refused"
        stage["error"] = encode(error.evidence)
    except BaseException as error:  # noqa: BLE001 -- never imply no effects after SDK invocation
        stage["status"] = "refused"
        stage["unverified_error"] = _unknown(error, invoked=invoked)
    finally:
        if plan is not None:
            try:
                plan.release()
            except error_type as error:
                stage["cleanup_error"] = encode(error.evidence)
                stage["status"] = "refused"
            except BaseException as error:  # noqa: BLE001 -- retain success and uncertain release independently
                stage["cleanup_unverified"] = _unknown(error, invoked=invoked)
                stage["status"] = "refused"
    return stage["status"] == "completed"


def _effect(payload: dict[str, Any]) -> str:
    states = []
    for name in ("workspace", "protocol"):
        stage = payload[name]
        for key in ("result", "error", "cleanup_error"):
            states.extend(
                item["state"] for item in stage.get(key, {}).get("effects", [])
            )
        for key in ("unverified_error", "cleanup_unverified"):
            if key in stage:
                states.append(stage[key]["effect"])
    if "unknown" in states:
        return "unknown"
    return "applied" if "applied" in states else "none"


def initialization_payload(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """Project exact SDK receipts; this aggregate is not another authority."""
    payload: dict[str, Any] = {
        "contract": "aware.agent.init.v1",
        "status": "refused",
        "repository_root": args.repository_root,
        "profile": "aware.collaboration.fs_v1",
        "authorizes_retry": False,
        "completion_verified": False,
        "workspace": {"status": "not_started"},
        "protocol": {"status": "not_started"},
    }
    stage = payload["protocol"]
    # Resolve public composition imports before any owner is dispatched. Missing imports
    # refuse; they never select a raw writer, different environment or service.
    try:
        execution = _execution()
        from aware_protocol_cli.bootstrap import (
            bootstrap_evidence_payload,
            prepare_bootstrap_input,
        )
        from aware_protocol_sdk.bootstrap import (
            ProtocolBootstrapClient,
            ProtocolBootstrapError,
        )
        from aware_workspace_sdk.repository_preparation import (
            RepositoryPreparationError,
            RepositoryPrepareRequest,
            WorkspaceRepositoryPreparationClient,
            repository_preparation_value_to_payload,
        )

        payload["execution_id"] = execution
        protocol = ProtocolBootstrapClient.filesystem(
            repository_root=args.repository_root, execution_id=execution
        )
        request, rendered = prepare_bootstrap_input(
            protocol,
            issue_root=args.issue_root,
            install_agent_contract=not args.no_agent_contract,
            dry_run=not args.apply,
        )
        stage["rendered_input"] = bootstrap_evidence_payload(rendered)
        stage["status"] = "input_validated"
        workspace = WorkspaceRepositoryPreparationClient.filesystem(
            repository_root=args.repository_root, execution_id=execution
        )
        workspace_request = RepositoryPrepareRequest(
            args.repository_root,
            create_if_missing=args.create_repository,
            dry_run=not args.apply,
        )
    except BaseException as error:  # noqa: BLE001 -- no owner operation has been invoked
        payload["preflight_error"] = _unknown(error, invoked=False)
        payload["effect"] = "none"
        return payload, 2

    if not _invoke(
        workspace,
        workspace_request,
        apply=args.apply,
        plan_method="plan_repository_preparation",
        admit_method="admit_repository_preparation",
        operation="prepare_repository",
        error_type=RepositoryPreparationError,
        encode=repository_preparation_value_to_payload,
        stage=payload["workspace"],
    ):
        payload["effect"] = _effect(payload)
        return payload, 2

    if not args.apply and payload["workspace"]["result"]["outcome"] == "planned":
        # An absent/empty non-Git root has prospective validated inputs, not a
        # live Protocol plan or result. Never pretend it has filesystem authority.
        stage["status"] = "prospective_only"
        payload["status"] = "planned"
        payload["effect"] = "none"
        return payload, 0

    # The previous owner has returned after confirmed cleanup. The SDK obtains
    # a fresh original Protocol plan, not authority from the Workspace receipt.
    if not _invoke(
        protocol,
        request,
        apply=args.apply,
        plan_method="plan_initialization",
        admit_method="admit_initialization",
        operation="initialize_profile",
        error_type=ProtocolBootstrapError,
        encode=bootstrap_evidence_payload,
        stage=stage,
    ):
        payload["effect"] = _effect(payload)
        return payload, 2
    payload["status"] = "completed" if args.apply else "planned"
    payload["completion_verified"] = True
    payload["effect"] = _effect(payload)
    return payload, 0


def _display(value: Any) -> str:
    """ASCII-escaped display only; never a changed SDK coordinate or decision."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _init_summary(payload: dict[str, Any], exit_code: int) -> str:
    """Explain original owner observations, never reinterpret provider authority."""
    lines = [
        "Init: " + _display(payload.get("status", "unknown/not returned")),
        "Operation exit before reporting: " + str(exit_code),
        "Repository: " + _display(payload.get("repository_root")),
        "What happened:",
    ]
    for owner in ("workspace", "protocol"):
        stage = payload.get(owner) or {}
        lines.append(
            owner.title()
            + " stage: "
            + _display(stage.get("status", "unknown/not returned"))
        )
        result = stage.get("result")
        if result is not None:
            lines.append(
                owner.title()
                + " original outcome: "
                + _display(result.get("outcome", "unknown/not returned"))
            )
        if owner == "workspace":
            request = (result or stage.get("error") or {}).get("request") or {}
            lines.append(
                "Repository creation intent: "
                + _display(request.get("create_if_missing", "unknown/not returned"))
                + "; dry run: "
                + _display(request.get("dry_run", "unknown/not returned"))
            )
        if stage.get("status") == "prospective_only":
            lines.append(
                "Protocol inputs are prospective only, not an admitted Protocol plan or result. Apply requires fresh original admission after Workspace preparation."
            )
        for key in ("error", "unverified_error"):
            error = stage.get(key)
            if error is not None:
                lines.append(
                    owner.title()
                    + " original failure: "
                    + _display(
                        error.get(
                            "code", error.get("error_type", "unknown/not returned")
                        )
                    )
                )
                if "phase" in error:
                    lines.append(
                        owner.title() + " failure phase: " + _display(error["phase"])
                    )
    if payload.get("preflight_error") is not None:
        error = payload["preflight_error"]
        lines.append(
            "Preflight failure: "
            + _display(
                error.get("code", error.get("error_type", "unknown/not returned"))
            )
        )
        for diagnostic in error.get("diagnostics", [])[:4]:
            lines.append("Preflight diagnostic: " + _display(diagnostic))
    lines.append("What changed:")
    lines.append(
        "Aggregate observed effect: "
        + _display(payload.get("effect", "unknown/not returned"))
        + "; this describes this invocation, not repository history or rollback."
    )
    for owner in ("workspace", "protocol"):
        stage = payload.get(owner) or {}
        for key in ("result", "error", "cleanup_error"):
            evidence = stage.get(key)
            if evidence is None:
                continue
            prefix = owner.title() + " " + key
            effects = evidence.get("effects", [])
            if not effects:
                lines.append(
                    prefix
                    + " reports no effect rows; absence is not proof of no historical effects."
                )
            for effect in effects[:8]:
                lines.append(
                    prefix
                    + " effect: "
                    + _display(effect.get("state", "unknown/not returned"))
                    + " at "
                    + _display(effect.get("path", "unknown/not returned"))
                )
            if len(effects) > 8:
                lines.append(
                    prefix
                    + ": additional effects omitted from explanation; full rows remain in stderr JSON."
                )
            if evidence.get("reported_result") is not None:
                lines.append(
                    prefix
                    + " contains an unvalidated provider report in full evidence; it is not promoted to a verified outcome."
                )
    protocol = payload.get("protocol") or {}
    rendered = protocol.get("rendered_input") or {}
    request = rendered.get("request") or {}
    files = rendered.get("files", [])
    if files:
        lines.append(
            "Requested Protocol files (inputs, not proof of publication): "
            + ", ".join(_display(row.get("path")) for row in files[:8])
        )
        if len(files) > 8:
            lines.append("Additional requested files remain in full evidence.")
        lines.append(
            "Issue records root: "
            + _display(request.get("issue_root", "unknown/not returned"))
        )
        lines.append(
            "Protocol input guard: "
            + _display(rendered.get("input_sha256", "unknown/not returned"))
            + " (observation, not write authority)."
        )
        if request.get("install_agent_contract") is False:
            lines.append(
                "Guidance files were explicitly omitted; do not assume AGENTS.md or the Issue protocol was provisioned."
            )
    lines.append("What remains uncertain:")
    lines.append(
        "Aggregate completion verified: "
        + _display(payload.get("completion_verified", "unknown/not returned"))
    )
    for owner in ("workspace", "protocol"):
        stage = payload.get(owner) or {}
        for key in ("result", "error", "cleanup_error"):
            evidence = stage.get(key)
            if evidence is None:
                continue
            lines.append(
                owner.title()
                + " "
                + key
                + " cleanup: "
                + _display(evidence.get("cleanup_state", "unknown/not returned"))
                + "; ledger complete: "
                + _display(evidence.get("ledger_complete", "unknown/not returned"))
            )
        for key in ("unverified_error", "cleanup_unverified"):
            evidence = stage.get(key)
            if evidence is not None:
                lines.append(
                    owner.title()
                    + " "
                    + key
                    + ": "
                    + _display(evidence.get("error_type", "unknown/not returned"))
                    + "; original effect: "
                    + _display(evidence.get("effect", "unknown/not returned"))
                    + "; ledger complete: "
                    + _display(evidence.get("ledger_complete", "unknown/not returned"))
                )
        if not any(
            key in stage
            for key in (
                "result",
                "error",
                "cleanup_error",
                "cleanup_unverified",
                "unverified_error",
            )
        ):
            lines.append(
                owner.title()
                + " operation/cleanup evidence: not returned; no completion inferred."
            )
    lines.append(
        "Later cleanup does not upgrade an original unknown outcome. Retain both owners' evidence."
    )
    lines.append("What next (guidance, not authority):")
    if payload.get("status") == "refused" or exit_code != 0:
        lines.append(
            "Stop and inspect the original failure, effects and cleanup before any further mutation. Do not retry apply, refresh guards, repair or overwrite automatically."
        )
    elif payload.get("status") == "planned":
        lines.append(
            "Review the selected root, creation intent, Issue root and requested files. Only an explicit --apply invokes owner admission; this preview grants none."
        )
    elif payload.get("completion_verified") is True:
        lines.append(
            "Issue-only initialization completed. A first Issue requires its own explicit task and admission; initialization creates no Issue or approval."
        )
    else:
        lines.append(
            "Inspect the full evidence before choosing further work; no completion or action authority is inferred."
        )
    lines.extend(
        [
            "Profile: "
            + _display(payload.get("profile", "unknown/not returned"))
            + "; SPEC, Goal and other families need separately governed configuration.",
            "Initialization does not create a seed commit, stage work, add a remote or start a service.",
            "Where is full evidence:",
            "Full aware.agent.init.v1 JSON is emitted on stderr in this invocation, including both owner receipts and rendered inputs. Retain both streams; no durable evidence reference is issued by this explanation.",
            "Do not repeat a mutating command with --format json to recover output. Default/json mode remains full JSON on stdout.",
        ]
    )
    return "\n".join(lines)


def _report_init_output(value: str, stream: Any) -> bool:
    """Flush within reporting; retire a poisoned buffer before process shutdown."""
    failed = False
    try:
        print(value, file=stream)
    except (OSError, UnicodeError):
        failed = True
    try:
        stream.flush()
    except (OSError, UnicodeError):
        failed = True
        # TextIOWrapper.close also closes its buffer when flushing raises.
        # Otherwise Python's final flush can replace our exit with 120.
        try:
            stream.close()
        except (OSError, UnicodeError):
            pass
    return not failed


def _handle_init(invocation: AwareCommandInvocation) -> int:
    if getattr(invocation.args, "profile", "issue-first") == "create-first":
        from .create_first_initialization import handle_create_first_init

        return handle_create_first_init(
            invocation, execution=_execution, report=_report_init_output
        )
    if getattr(invocation.args, "recover", False):
        print(
            json.dumps({"error": "recovery_requires_create_first", "effect": "none"}),
            file=sys.stderr,
        )
        return 2
    if (
        getattr(invocation.args, "goal_root", None) is not None
        or getattr(invocation.args, "project_root", None) is not None
    ):
        print(
            json.dumps(
                {"error": "planning_roots_require_create_first", "effect": "none"}
            ),
            file=sys.stderr,
        )
        return 2
    payload, exit_code = initialization_payload(invocation.args)
    if invocation.args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return exit_code
    # Report once on each channel even when the other channel is unavailable.
    # Neither reporting failure dispatches an owner again or repeats cleanup.
    human_ok = _report_init_output(_init_summary(payload, exit_code), sys.stdout)
    evidence_ok = _report_init_output(
        json.dumps(payload, indent=2, sort_keys=True), sys.stderr
    )
    if not human_ok or not evidence_ok:
        return 130 if exit_code == 130 else 3
    return exit_code
