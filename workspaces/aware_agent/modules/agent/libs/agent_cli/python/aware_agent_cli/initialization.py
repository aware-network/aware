"""Sequential SDK composition only; no filesystem writer or domain policy."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry

if TYPE_CHECKING:
    from aware_protocol_sdk.bootstrap import ProtocolBootstrapError
    from aware_workspace_sdk.repository_preparation import RepositoryPreparationError


def register_init_command(registry: AwareCommandRegistry) -> None:
    registry.register_command(
        name="init",
        help="Preview or explicitly initialize an Issue-only filesystem repository.",
        description=(
            "Preview by default. --create-repository admits an empty repository; "
            "--apply requests effects. Both SDK owners retain separate evidence. "
            "No seed commit, staging, remote, Issue or service is created."
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
    parser.add_argument("--issue-root", default="docs/issues")
    parser.add_argument("--no-agent-contract", action="store_true")
    intent = parser.add_mutually_exclusive_group()
    intent.add_argument("--dry-run", action="store_true")
    intent.add_argument("--apply", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")


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
        stage["rendered_input"] = bootstrap_evidence_payload(
            rendered, summary=args.format == "summary"
        )
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


def _handle_init(invocation: AwareCommandInvocation) -> int:
    payload, exit_code = initialization_payload(invocation.args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code
