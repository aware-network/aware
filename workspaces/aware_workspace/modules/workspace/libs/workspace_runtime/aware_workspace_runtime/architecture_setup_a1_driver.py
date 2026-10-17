"""One-process original SDK preview/admission/apply and complete owner cleanup."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
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
from aware_workspace_sdk.architecture_setup_command_values import (
    CommandMode,
    OwnerFamily,
    WorkspaceSetupA1ClientCleanup,
    WorkspaceSetupA1CommandEvidence,
    WorkspaceSetupA1CommandRequest,
    WorkspaceSetupA1ReviewGuards,
    WorkspaceSetupA1UnvalidatedReport,
)

_NONE = WorkspaceSetupPrimaryFailure("none", None, None, None, None, False)


class _WriteScopeMismatch(ArchitectureSetupError):
    code = "setup_write_scope_mismatch"


def _path_diagnostic(label: str, paths: tuple[str, ...]) -> str:
    text = json.dumps(paths, ensure_ascii=True, separators=(",", ":"))
    message = label + ": " + text
    if len(message.encode("utf-8")) <= 256:
        return message
    return (
        f"{label}: {len(paths)} entries; list omitted; "
        f"sha256={hashlib.sha256(text.encode('utf-8')).hexdigest()}; "
        "retain original binding/argv for complete paths"
    )


def run_setup_a1(
    command_request: WorkspaceSetupA1CommandRequest,
    *,
    mode: CommandMode,
    review_guards: WorkspaceSetupA1ReviewGuards,
    allowed_final_files: tuple[str, ...] = (),
    actor_ref: str | None = None,
    actor_evidence_ref: str | None = None,
):
    from aware_issue_sdk.workspace_setup_admission import (
        IssueWorkspaceSetupAdmissionClient,
    )
    from aware_issue_sdk.workspace_setup_admission_values import (
        IssueWorkspaceSetupRequest,
    )
    from aware_workspace_sdk.architecture_setup_command_values import (
        command_value_to_payload,
    )

    workspace: Any = None
    issuer: Any = None
    plan = issue_plan = issue_admission = None
    request = observation = sources = issue_observation = result = plan_cleanup = (
        admission_cleanup
    ) = None
    workspace_cleanup: Any = None
    issue_cleanup: Any = None
    reports = []
    diagnostics: tuple[str, ...] = ()
    primary = _NONE
    status = "refused"
    complete = True
    started = False
    interruption: BaseException | None = None
    apply = mode == "apply"
    operation = None
    guards = review_guards
    try:
        if mode not in ("preview", "apply"):
            raise ArchitectureSetupError("a1_command_mode_invalid")
        if type(command_request) is not WorkspaceSetupA1CommandRequest:
            raise ArchitectureSetupError("a1_typed_command_required")
        if not all(
            (
                command_request.issue_ref,
                command_request.authority_manifest_locator,
                command_request.client_intent_id,
            )
        ):
            raise ArchitectureSetupError("a1_explicit_authority_inputs_required")
        command_value_to_payload(command_request)
        command_value_to_payload(guards)
        if type(allowed_final_files) is not tuple or any(
            type(p) is not str for p in allowed_final_files
        ):
            raise ArchitectureSetupError("a1_exact_final_paths_required")
        operation = command_request.architecture_request.operation
        if apply and None in (
            guards.issue_source_sha256,
            guards.authority_manifest_sha256,
            guards.plan_sha256,
        ):
            raise ArchitectureSetupError("a1_apply_requires_three_review_guards")
        execution = command_request.execution_ref
        architecture = command_request.architecture_request
        workspace = WorkspaceSetupClient.filesystem(
            repository_root=Path(command_request.repository_root)
        )
        issuer = IssueWorkspaceSetupAdmissionClient.filesystem(
            repository_root=Path(command_request.repository_root),
            execution_id=execution,
            authority_manifest_locator=command_request.authority_manifest_locator,
        )
        sources = issuer.observe_authority_sources(issue_ref=command_request.issue_ref)
        preview = workspace.preview(architecture)
        selected = preview.plan_sha256 if not apply else guards.plan_sha256
        plan = workspace.prepare_setup(architecture, expected_plan_sha256=selected)
        observation = observe_original_setup_plan(plan)
        issue_request = IssueWorkspaceSetupRequest(
            command_request.issue_ref,
            sources.issue_source.content_sha256
            if not apply
            else guards.issue_source_sha256 or "",
            command_request.issue_request.actor_ref
            if command_request.issue_request
            else actor_ref,
            command_request.issue_request.actor_evidence_ref
            if command_request.issue_request
            else actor_evidence_ref,
            command_request.client_intent_id,
            "workspace_setup_a1_v1",
            sources.authority_manifest_source.content_sha256
            if not apply
            else guards.authority_manifest_sha256 or "",
        )
        from aware_issue_sdk.workspace_setup_admission_codec import (
            issue_setup_value_to_payload,
        )

        issue_setup_value_to_payload(issue_request)
        if (
            command_request.issue_request is not None
            and command_request.issue_request != issue_request
        ):
            raise ArchitectureSetupError("a1_original_issue_request_mismatch")
        request = WorkspaceSetupA1CommandRequest(
            architecture,
            issue_request,
            command_request.repository_root,
            command_request.authority_manifest_locator,
            command_request.issue_ref,
            execution,
            command_request.client_intent_id,
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
            allowed = allowed_final_files
            if len(set(allowed)) != len(allowed) or set(allowed) != set(paths):
                diagnostics = (
                    _path_diagnostic("expected_final_paths", paths),
                    _path_diagnostic("supplied_final_paths", tuple(allowed)),
                    (
                        "Review final file_transitions and supply each final path once. "
                        "Do not add scratch/effect paths or refresh guards automatically."
                    ),
                )
                raise _WriteScopeMismatch("setup_write_scope_mismatch")
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
        if not isinstance(error, Exception):
            interruption = error
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
        diagnostics,
        complete,
        False,
    )
    if interruption is not None:
        BaseException.__setattr__(interruption, "setup_command_evidence", evidence)
        raise interruption
    return evidence, 0 if success else 3 if status == "incomplete" else 2
