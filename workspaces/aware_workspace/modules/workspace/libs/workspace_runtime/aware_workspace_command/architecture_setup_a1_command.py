"""One-process original SDK preview/admission/apply and complete owner cleanup."""

from __future__ import annotations

import argparse
import importlib
from typing import Any, cast

from aware_workspace_sdk.architecture_setup import (
    ArchitectureSetupError,
    WorkspaceSetupClient,
)
from aware_workspace_sdk.architecture_setup_admission import observe_original_setup_plan
from aware_workspace_sdk.architecture_setup_admission_values import (
    WorkspaceSetupClientCleanup,
    WorkspaceSetupPrimaryFailure,
)

from .architecture_setup_a1_command_values import (
    OwnerFamily,
    WorkspaceSetupA1ClientCleanup,
    WorkspaceSetupA1CommandEvidence,
    WorkspaceSetupA1CommandRequest,
    WorkspaceSetupA1ReviewGuards,
    WorkspaceSetupA1UnvalidatedReport,
    command_value_to_json,
)

_NONE = WorkspaceSetupPrimaryFailure("none", None, None, None, None, False)


def configure_a1_arguments(parser: argparse.ArgumentParser):
    for flag in (
        "governed",
        "issue-ref",
        "authority-manifest",
        "issue-source-sha256",
        "authority-manifest-sha256",
        "client-intent-id",
        "actor-ref",
        "actor-evidence-ref",
    ):
        parser.add_argument(
            "--" + flag,
            action="store_true" if flag == "governed" else "store",
            default=argparse.SUPPRESS,
        )


def run_a1(args):
    _execution = importlib.import_module(
        "aware_issue_fs_adapter.source_change"
    )._execution
    from aware_issue_sdk.workspace_setup_admission import (
        IssueWorkspaceSetupAdmissionClient,
    )
    from aware_issue_sdk.workspace_setup_admission_values import (
        IssueWorkspaceSetupRequest,
    )

    _request = importlib.import_module(
        "aware_workspace_command.architecture_setup_command"
    )._request

    workspace: Any = None
    issuer: Any = None
    plan = issue_plan = issue_admission = None
    request = observation = sources = issue_observation = result = plan_cleanup = (
        admission_cleanup
    ) = None
    workspace_cleanup: Any = None
    issue_cleanup: Any = None
    reports = []
    primary = _NONE
    status = "refused"
    complete = True
    started = False
    apply = bool(getattr(args, "apply", False))
    mode = "apply" if apply else "preview"
    operation = (
        "package_manager"
        if args.setup_operation == "align"
        else "python_package"
        if args.setup_operation == "python-package"
        else args.setup_operation
    )
    guards = WorkspaceSetupA1ReviewGuards(
        getattr(args, "issue_source_sha256", None),
        getattr(args, "authority_manifest_sha256", None),
        getattr(args, "expected_plan_sha256", None),
    )
    try:
        if operation == "locks":
            raise ArchitectureSetupError("a1_locks_are_separate")
        if not all(
            getattr(args, key, None)
            for key in ("issue_ref", "authority_manifest", "client_intent_id")
        ):
            raise ArchitectureSetupError("a1_explicit_authority_inputs_required")
        if apply and None in (
            guards.issue_source_sha256,
            guards.authority_manifest_sha256,
            guards.plan_sha256,
        ):
            raise ArchitectureSetupError("a1_apply_requires_three_review_guards")
        execution = _execution()
        architecture = _request(args)
        workspace = WorkspaceSetupClient.filesystem(
            repository_root=args.setup_repository_root
        )
        issuer = IssueWorkspaceSetupAdmissionClient.filesystem(
            repository_root=args.setup_repository_root,
            execution_id=execution,
            authority_manifest_locator=args.authority_manifest,
        )
        sources = issuer.observe_authority_sources(issue_ref=args.issue_ref)
        preview = workspace.preview(architecture)
        selected = preview.plan_sha256 if not apply else guards.plan_sha256
        plan = workspace.prepare_setup(architecture, expected_plan_sha256=selected)
        observation = observe_original_setup_plan(plan)
        issue_request = IssueWorkspaceSetupRequest(
            args.issue_ref,
            sources.issue_source.content_sha256
            if not apply
            else guards.issue_source_sha256 or "",
            getattr(args, "actor_ref", None),
            getattr(args, "actor_evidence_ref", None),
            args.client_intent_id,
            "workspace_setup_a1_v1",
            sources.authority_manifest_source.content_sha256
            if not apply
            else guards.authority_manifest_sha256 or "",
        )
        from aware_issue_sdk.workspace_setup_admission_codec import (
            issue_setup_value_to_payload,
        )

        issue_setup_value_to_payload(issue_request)
        request = WorkspaceSetupA1CommandRequest(
            architecture,
            issue_request,
            str(args.setup_repository_root),
            args.authority_manifest,
            args.issue_ref,
            execution,
            args.client_intent_id,
        )
        if not apply:
            guards = WorkspaceSetupA1ReviewGuards(
                sources.issue_source.content_sha256,
                sources.authority_manifest_source.content_sha256,
                preview.plan_sha256,
            )
            status = "preview_completed"
        else:
            if observation.binding is None:
                raise ArchitectureSetupError("original_workspace_binding_required")
            paths = tuple(row.path for row in observation.binding.file_transitions)
            allowed = getattr(args, "allowed_path", ())
            if len(set(allowed)) != len(allowed) or set(allowed) != set(paths):
                raise ArchitectureSetupError("setup_write_scope_mismatch")
            issue_plan = issuer.prepare_setup_admission(
                issue_request, workspace_plan=plan, expected_binding=observation.binding
            )
            issue_admission = issuer.admit_setup(issue_plan)
            admission = workspace.enroll_setup_admission(
                plan, issue_admission=issue_admission
            )
            started = True
            result = workspace.apply_setup_plan(plan, admission=admission)
            issue_observation = issuer.observe_setup_admission(issue_plan)
            status = "apply_completed"
    except BaseException as error:  # noqa: BLE001 - retain cancellation with original cleanup
        primary = WorkspaceSetupPrimaryFailure(
            "observed",
            "workspace-setup-command",
            "command",
            getattr(error, "code", "setup_command_failed"),
            type(error).__name__,
            not isinstance(error, Exception),
        )
        original_result = getattr(error, "result", None)
        if original_result is not None:
            result = original_result
        partial_cleanup = getattr(error, "client_cleanup", None)
        if type(partial_cleanup) is WorkspaceSetupClientCleanup:
            workspace_cleanup = partial_cleanup
            complete = (
                complete
                and partial_cleanup.ledger_complete
                and partial_cleanup.outcome == "confirmed"
            )
        status = "incomplete" if started else "refused"
        if issue_plan is not None:
            try:
                issue_observation = issuer.observe_setup_admission(issue_plan)
            except BaseException:  # noqa: BLE001 - no interruption may skip independent cleanup/output evidence
                complete = False
                reports.append(
                    WorkspaceSetupA1UnvalidatedReport(
                        "issue",
                        "aware.issue.setup-a1-observation.v1",
                        "failure",
                        "owner_observation_unavailable",
                    )
                )
    finally:
        # Fixed dependency order; one owner's failure never prevents independent
        # original cleanup. No borrowed disposal or unknown close retry.
        owners: tuple[tuple[Any, Any, Any], ...] = (
            (workspace, plan, "workspace"),
            (issuer, issue_plan, "issue"),
        )
        for owner, handle, family in owners:
            if owner is None or handle is None:
                continue
            try:
                if family == "workspace":
                    plan_cleanup = owner.release_setup_plan(handle)
                else:
                    admission_cleanup = owner.release_setup_admission(handle)
            except BaseException:  # noqa: BLE001 - no interruption may skip independent cleanup/output evidence
                complete = False
                reports.append(
                    WorkspaceSetupA1UnvalidatedReport(
                        cast(OwnerFamily, family),
                        "aware." + family + ".setup-a1-cleanup.v1",
                        "cleanup",
                        "owner_cleanup_unavailable",
                    )
                )
        for owner, family in ((issuer, "issue"), (workspace, "workspace")):
            if owner is None:
                continue
            try:
                cleanup = owner.release_client()
                if family == "issue":
                    issue_cleanup = cleanup
                else:
                    workspace_cleanup = cleanup
                complete = (
                    complete
                    and cleanup.ledger_complete
                    and cleanup.outcome == "confirmed"
                )
            except BaseException:  # noqa: BLE001 - no interruption may skip independent cleanup/output evidence
                complete = False
                reports.append(
                    WorkspaceSetupA1UnvalidatedReport(
                        cast(OwnerFamily, family),
                        "aware." + family + ".setup-a1-client-cleanup.v1",
                        "cleanup",
                        "client_cleanup_unavailable",
                    )
                )
        for cleanup in (plan_cleanup, admission_cleanup):
            if cleanup is not None:
                complete = (
                    complete
                    and cleanup.ledger_complete
                    and getattr(cleanup, "release", getattr(cleanup, "outcome", None))
                    == "confirmed"
                )
    if not complete:
        status = "incomplete"
    success = status in ("preview_completed", "apply_completed") and complete
    evidence = WorkspaceSetupA1CommandEvidence(
        "aware.workspace.architecture-setup-a1-command.v1",
        mode,
        operation,
        status,
        success,
        request,
        guards,
        observation,
        sources,
        issue_observation,
        result,
        primary,
        plan_cleanup,
        admission_cleanup,
        WorkspaceSetupA1ClientCleanup(issue_cleanup, workspace_cleanup),
        tuple(reports),
        (),
        complete,
        False,
    )
    return evidence, 0 if success else 3 if status == "incomplete" else 2


def handle_a1(args):
    evidence, code = run_a1(args)
    try:
        print(command_value_to_json(evidence))
    except BaseException:  # noqa: BLE001 - no interruption may skip independent cleanup/output evidence
        # Output failure cannot replay effects or become a success exit.
        return 3
    return code
