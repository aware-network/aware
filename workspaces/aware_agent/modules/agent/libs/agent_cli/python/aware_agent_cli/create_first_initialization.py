"""Explicit fresh-root composition of original owners, never a second writer.

The live preparation and Protocol plans are frozen before consent. Later stages
consume their original outputs. Failure preserves every returned receipt; it
never adopts files, re-enrolls, refreshes a plan or dispatches a second attempt.
This is cooperative local-policy authoring, not Identity or RUN authority.
"""

from __future__ import annotations

import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry


class _ReportingIncomplete(RuntimeError):
    """Owner result is retained, but the original output channel failed."""


def _emit(
    payload: dict[str, Any], *, format: str, report: Callable[[str, Any], bool]
) -> None:
    def send(value: str, stream: Any) -> bool:
        try:
            return report(value, stream)
        except (OSError, ValueError, UnicodeError):
            return False

    wire = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if format == "json":
        okay = send(wire, sys.stdout)
        if not okay:
            # Preserve THIS invocation's returned receipts on the remaining
            # channel, never repeat a mutation to regenerate output.
            _ = send(wire, sys.stderr)
    else:
        status = payload["status"]
        if payload.get("operation") == "recover":
            summary = (
                f"Create-first recovery: {status}. Repository: {payload['repository_root']}\n"
                "Historical original-owner evidence only. No new publication, projection, retry or permission.\n"
                "Recovery success is not setup completion."
            )
            selected = payload.get("original_selection") or {}
            recovered = selected.get("recovery") or {}
            original = recovered.get("original_result") or {}
            summary += "\nOriginal publication: " + json.dumps(
                original.get("publication_state", "unavailable")
            )
            summary += "\nOriginal cleanup: " + json.dumps(
                original.get("cleanup_state", "unavailable")
            )
        else:
            summary = (
                f"Create-first setup: {status}. Repository: {payload['repository_root']}\n"
                "Explicit effects: create an empty Git repository, retain local initial-authoring "
                "records, commit and project aware.protocol.toml (fs_v4).\n"
                "No Project, Goal, Issue, AGENTS.md, remote or work is created. No RUN authority."
            )
        if payload.get("git_identity") is not None:
            summary += "\nGit metadata observation: " + json.dumps(
                payload["git_identity"], sort_keys=True
            )
        if payload.get("reason") == "git_commit_identity_unavailable":
            summary += "\nChoose Git author/committer metadata explicitly before a new plan. Aware did not configure Git."
        if status == "configured":
            summary += "\nNext: create an empty Project, then a Proposed Goal with explicit membership."
        if payload.get("reason"):
            summary += f"\nReason: {payload['reason']}. Retain the complete evidence; do not retry automatically."
        human = send(summary, sys.stdout)
        evidence = send(wire, sys.stderr)
        okay = human and evidence
    if not okay:
        raise _ReportingIncomplete("initializer_output_incomplete")


def _recover_initial_setup(args, *, execution, report) -> int:
    """Original-owner historical read; no preparation, Protocol plan or writer."""
    payload = {
        "contract": "aware.agent.create-first-init-recovery.v1",
        "operation": "recover",
        "repository_root": args.repository_root,
        "status": "refused",
        "completion_verified": False,
        "authorizes_retry": False,
        "authorizes_redispatch": False,
        "historical_only": True,
    }
    try:
        if (
            args.create_repository
            or args.no_agent_contract
            or args.goal_root is not None
            or args.project_root is not None
            or args.issue_root != "docs/issues"
        ):
            raise ValueError("recovery_rejects_new_setup_options")
        from aware_workspace_sdk.repository_publication import (
            WorkspaceRepositoryCommitResult,
            WorkspaceRepositoryPublicationClient,
            repository_publication_value_to_payload,
        )

        payload["execution_id"] = execution()
        original = WorkspaceRepositoryPublicationClient.filesystem(
            repository_root=args.repository_root
        )
        selected = original.observe_initial_authoring_request("configuration")

        def wire(value):
            if isinstance(value, WorkspaceRepositoryCommitResult):
                return repository_publication_value_to_payload(value)
            if type(value) is dict:
                return {key: wire(item) for key, item in value.items()}
            if type(value) in (tuple, list):
                return [wire(item) for item in value]
            if value is None or type(value) in (str, bool, int):
                return value
            raise TypeError("unrecognized_original_recovery_evidence")

        selection = {
            **selected,
            "request": selected["request"].to_wire()
            if selected["request"] is not None
            else None,
        }
        payload["original_selection"] = wire(selection)
        recovered = selected.get("recovery") or {}
        payload["status"] = (
            "recovered" if recovered.get("disposition") == "recorded" else "uncertain"
        )
        payload["recovery_verified"] = payload["status"] == "recovered"
        _emit(payload, format=args.format, report=report)
        return 0 if payload["status"] == "recovered" else 3
    except _ReportingIncomplete:
        return 3
    except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 -- preserve historical uncertainty, never retry
        payload.update(status="refused", reason=str(error) or type(error).__name__)
        try:
            _emit(payload, format=args.format, report=report)
        except _ReportingIncomplete:
            return 3
        return 130 if isinstance(error, KeyboardInterrupt) else 2


def handle_create_first_init(
    invocation: AwareCommandInvocation,
    *,
    execution: Callable[[], str],
    report: Callable[[str, Any], bool],
) -> int:
    args = invocation.args
    if getattr(args, "recover", False):
        return _recover_initial_setup(args, execution=execution, report=report)
    payload: dict[str, Any] = {
        "contract": "aware.agent.create-first-init.v1",
        "repository_root": args.repository_root,
        "profile": "aware.collaboration.fs_v4",
        "status": "refused",
        "completion_verified": False,
        "authorizes_retry": False,
        "authorizes_redispatch": False,
        "assurance": "cooperative_same_execution_local_policy",
        "agent_contract": "not_installed",
        "stages": {},
    }
    attempted = False
    stage = "preflight"
    evidence_encoders: tuple[Callable[..., Any], ...] = ()
    try:
        if not args.create_repository:
            raise ValueError("create_first_requires_explicit_create_repository")
        if args.no_agent_contract:
            raise ValueError("no_agent_contract_is_issue_first_only")
        if args.apply and not (sys.stdin.isatty() and sys.stdout.isatty()):
            raise ValueError(
                "noninteractive_apply_requires_original_durable_review_binding"
            )
        # Resolve both optional families before any filesystem preparation. Missing
        # suppliers never select a different environment or compatibility writer.
        registrars = importlib.import_module("aware_goal_native_cli.customer_commands")
        for name in (
            "register_project_commands",
            "register_create_first_goal_commands",
        ):
            registrar = getattr(registrars, name)
            if not callable(registrar):
                raise ImportError("qualified_create_first_registrar_required")  # noqa: TRY004 -- incompatible supplier export
            registrar(AwareCommandRegistry())

        from aware_protocol_fs_adapter.project_bootstrap import (
            prepare_planning_project_configuration,
            require_project_configuration,
        )
        from aware_protocol_fs_adapter.project_resolver import (
            admit_project_resolver,
            require_project_resolver,
        )
        from aware_workspace_sdk.repository_preparation import (
            RepositoryPrepareRequest,
            WorkspaceRepositoryPreparationClient,
            repository_preparation_value_to_payload,
        )
        from aware_workspace_sdk.repository_publication import (
            WorkspaceRepositoryCommitResult,
            WorkspaceRepositoryPublicationClient,
            repository_publication_value_to_payload,
        )

        def projection_wire(value: Any) -> Any:
            if isinstance(value, WorkspaceRepositoryCommitResult):
                return repository_publication_value_to_payload(value)
            if type(value) is dict:
                return {key: projection_wire(item) for key, item in value.items()}
            if type(value) in (tuple, list):
                return [projection_wire(item) for item in value]
            if value is None or type(value) in (str, int, bool):
                return value
            raise TypeError("unrecognized_original_projection_evidence")

        evidence_encoders = (
            repository_preparation_value_to_payload,
            repository_publication_value_to_payload,
        )
        execution_id = execution()
        payload["execution_id"] = execution_id
        roots = {"issue_root": args.issue_root}
        for name in ("goal_root", "project_root"):
            if getattr(args, name) is not None:
                roots[name] = getattr(args, name)
        configuration = prepare_planning_project_configuration(
            repository_root=args.repository_root, **roots
        )
        frozen = require_project_configuration(configuration).to_wire()
        payload["configuration"] = frozen
        preparation = WorkspaceRepositoryPreparationClient.filesystem(
            repository_root=args.repository_root, execution_id=execution_id
        )
        request = RepositoryPrepareRequest(args.repository_root, True)
        # This is the REAL live plan, not a dry-run result later reconstructed as
        # permission. Preview releases it; apply admits exactly this same handle.
        with preparation.plan_repository_preparation(request) as plan:
            observation = plan.observe()
            payload["preparation_plan"] = repository_preparation_value_to_payload(
                observation
            )
            if (
                str(Path(args.repository_root) / ".git")
                not in observation.ordered_effect_paths
            ):
                raise ValueError("fresh_empty_repository_preparation_required")
            identity = WorkspaceRepositoryPublicationClient.observe_filesystem_initial_git_identity(
                repository_root=args.repository_root
            )
            payload["git_identity"] = identity
            if identity["status"] != "available":
                raise ValueError("git_commit_identity_unavailable")
            payload["status"] = "preview"
            _emit(payload, format=args.format, report=report)
            if not args.apply:
                return 0
            print(
                "Type 'initialize create-first' to confirm this exact plan: ",
                file=sys.stderr,
                end="",
                flush=True,
            )
            if sys.stdin.readline().rstrip("\r\n") != "initialize create-first":
                raise ValueError("exact_plan_confirmation_not_given")
            if require_project_configuration(configuration).to_wire() != frozen:
                raise ValueError("configuration_changed_after_confirmation")
            if (
                WorkspaceRepositoryPublicationClient.observe_filesystem_initial_git_identity(
                    repository_root=args.repository_root
                )
                != identity
            ):
                raise ValueError("git_commit_identity_changed_after_confirmation")
            stage = "repository_preparation"
            attempted = True
            prepared = preparation.prepare_repository(
                request, admission=preparation.admit_repository_preparation(plan)
            )
            payload["stages"][stage] = repository_preparation_value_to_payload(prepared)
            if prepared.outcome != "created":
                raise ValueError("original_fresh_preparation_not_created")
        stage = "enrollment"
        workspace = WorkspaceRepositoryPublicationClient.filesystem(
            repository_root=args.repository_root
        )
        enrollment = workspace.enroll_initial_authoring(preparation)
        stage = "configuration_publication"
        publication_plan = workspace.plan_initial_configuration(
            enrollment, configuration, idempotency_key="configuration"
        )
        publication = workspace.publish_initial_configuration(
            workspace.admit_initial_configuration(publication_plan)
        )
        payload["stages"][stage] = repository_publication_value_to_payload(publication)
        if publication.publication_state != "published":
            raise ValueError("configuration_publication_not_verified")
        stage = "configuration_projection"
        projection = workspace.project_initial_configuration(
            configuration, idempotency_key="configuration"
        )
        payload["stages"][stage] = projection_wire(projection)
        if (
            projection["projection_state"] != "installed"
            or projection["original_result"] != publication
        ):
            raise ValueError("configuration_projection_not_verified")
        stage = "protocol_admission"
        selected = admit_project_resolver(
            repository_root=Path(args.repository_root),
            manifest_path=Path(args.repository_root) / "aware.protocol.toml",
        )
        capability = require_project_resolver(selected.capability)
        if capability.protocol_profile != "aware.collaboration.fs_v4":
            raise ValueError("planning_profile_required")
        payload["stages"][stage] = {
            "profile": capability.protocol_profile,
            "manifest_sha256": capability.manifest_sha256,
            "project_root": capability.project_root,
            "capability": "issued_live_not_transportable",
        }
        # Owner-qualified committed projection at the final boundary; no recovery
        # or new historical selection runs after this qualification.
        stage = "terminal_qualification"
        terminal = workspace.observe_initial_configuration_projection(
            configuration, idempotency_key="configuration"
        )
        payload["stages"][stage] = projection_wire(terminal)
        if (
            terminal["projection_state"] != "installed"
            or terminal["original_result"] != publication
        ):
            raise ValueError("terminal_configuration_unavailable")
        payload.update(status="configured", completion_verified=True)
        _emit(payload, format=args.format, report=report)
        return 0
    except _ReportingIncomplete:
        return 3
    except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 -- retain partial owner effects, never claim rollback
        payload.update(
            status="uncertain" if attempted else "refused",
            completion_verified=False,
            reason=str(error) or type(error).__name__,
            failed_stage=stage,
        )
        # Original errors can carry physical/commit evidence even without a
        # result return. Preserve those claims separately, never infer rollback.
        evidence = getattr(error, "evidence", None)
        if evidence is not None:
            for encode in evidence_encoders:
                try:
                    payload["error_evidence"] = encode(evidence)
                    break
                except (TypeError, ValueError):
                    continue
            if "error_evidence" not in payload:
                payload["error_evidence_unavailable"] = True
        try:
            _emit(payload, format=args.format, report=report)
        except (OSError, ValueError, _ReportingIncomplete):
            return 3
        return 130 if isinstance(error, KeyboardInterrupt) else (3 if attempted else 2)
