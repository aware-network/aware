"""One-process original SDK preview/admission/apply and complete owner cleanup."""

from __future__ import annotations

import argparse
import importlib

from aware_workspace_runtime.architecture_setup_a1_driver import (
    _path_diagnostic as _path_diagnostic,  # noqa: PLC0414 - historical import compatibility
)
from aware_workspace_runtime.architecture_setup_a1_driver import run_setup_a1

from .architecture_setup_a1_command_values import (
    WorkspaceSetupA1ClientCleanup,
    WorkspaceSetupA1CommandEvidence,
    WorkspaceSetupA1CommandRequest,
    WorkspaceSetupA1ReviewGuards,
    command_value_to_json,
)


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
    """Compatibility Namespace adapter; all owner execution stays in one driver."""
    from aware_issue_fs_adapter.source_change import _execution
    from aware_workspace_sdk.architecture_setup_admission_values import (
        WorkspaceSetupPrimaryFailure,
    )

    _request = importlib.import_module(
        "aware_workspace_command.architecture_setup_command"
    )._request

    guards = WorkspaceSetupA1ReviewGuards(
        getattr(args, "issue_source_sha256", None),
        getattr(args, "authority_manifest_sha256", None),
        getattr(args, "expected_plan_sha256", None),
    )
    mode = "apply" if getattr(args, "apply", False) else "preview"
    try:
        execution = _execution()
        request = WorkspaceSetupA1CommandRequest(
            _request(args),
            None,
            str(args.setup_repository_root),
            getattr(args, "authority_manifest", ""),
            getattr(args, "issue_ref", ""),
            execution,
            getattr(args, "client_intent_id", ""),
        )
    except BaseException as error:  # noqa: BLE001 - preserve original interruption in command evidence
        evidence = WorkspaceSetupA1CommandEvidence(
            "aware.workspace.architecture-setup-a1-command.v1",
            mode,
            None,
            "refused",
            False,
            None,
            guards,
            None,
            None,
            None,
            None,
            WorkspaceSetupPrimaryFailure(
                "observed",
                "workspace-setup-command",
                "command",
                getattr(error, "code", "setup_command_failed"),
                type(error).__name__,
                not isinstance(error, Exception),
            ),
            None,
            None,
            WorkspaceSetupA1ClientCleanup(None, None),
            (),
            (),
            True,
            False,
        )
        return evidence, 2
    try:
        return run_setup_a1(
            request,
            mode=mode,
            review_guards=guards,
            allowed_final_files=tuple(getattr(args, "allowed_path", ())),
            actor_ref=getattr(args, "actor_ref", None),
            actor_evidence_ref=getattr(args, "actor_evidence_ref", None),
        )
    except BaseException as error:
        evidence = getattr(error, "setup_command_evidence", None)
        if type(evidence) is not WorkspaceSetupA1CommandEvidence:
            raise
        return evidence, 3 if evidence.command_status == "incomplete" else 2


def handle_a1(args):
    evidence, code = run_a1(args)
    try:
        encoded = command_value_to_json(evidence)
        if not getattr(args, "json", False):
            from .architecture_setup_a1_presentation import render_a1_review

            print(
                render_a1_review(
                    evidence,
                    supplied_final_paths=tuple(getattr(args, "allowed_path", ())),
                )
            )
            print("Complete owner evidence JSON:")
        print(encoded)
    except BaseException:  # noqa: BLE001 - no interruption may skip independent cleanup/output evidence
        # Output failure cannot replay effects or become a success exit.
        return 3
    return code
