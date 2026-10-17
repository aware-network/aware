"""Presentation edge cases; synthetic evidence is never an admission proof."""

from dataclasses import replace

from aware_workspace_command.architecture_setup_a1_command import _path_diagnostic
from aware_workspace_command.architecture_setup_a1_command_values import (
    WorkspaceSetupA1ClientCleanup,
    WorkspaceSetupA1CommandEvidence,
    WorkspaceSetupA1ReviewGuards,
)
from aware_workspace_command.architecture_setup_a1_presentation import render_a1_review
from aware_workspace_sdk.architecture_setup_admission_values import (
    WorkspaceSetupPrimaryFailure,
)


def test_long_diagnostic_is_bounded_and_explicit_about_omitted_paths():
    paths = tuple("long/" + "x" * 1024 for _ in range(256))
    message = _path_diagnostic("supplied_final_paths", paths)
    assert len(message.encode("utf-8")) <= 256
    assert "256 entries; list omitted; sha256=" in message
    assert "retain original binding/argv" in message
    assert message != _path_diagnostic("supplied_final_paths", paths[:-1])


def test_diagnostic_escapes_control_characters_without_terminal_injection():
    text = _path_diagnostic("supplied_final_paths", ("bad\n\x1b[31m",))
    assert "\n" not in text and "\x1b" not in text
    assert "\\n" in text and "\\u001b" in text


def test_missing_observation_and_failure_never_invent_admission_or_cleanup():
    evidence = WorkspaceSetupA1CommandEvidence(
        "aware.workspace.architecture-setup-a1-command.v1",
        "apply",
        "repository",
        "refused",
        False,
        None,
        WorkspaceSetupA1ReviewGuards(None, None, None),
        None,
        None,
        None,
        None,
        WorkspaceSetupPrimaryFailure(
            "observed",
            "workspace-setup-command",
            "command",
            "setup_write_scope_mismatch",
            "_WriteScopeMismatch",
            False,
        ),
        None,
        None,
        WorkspaceSetupA1ClientCleanup(None, None),
        (),
        (),
        False,
        False,
    )
    text = render_a1_review(
        evidence, supplied_final_paths=("x\n\x1b[31m", "x\n\x1b[31m")
    )
    assert "Workspace plan: unavailable; no effect scope inferred." in text
    assert "Issue admission: not observed" in text
    assert "Workspace client: not observed" in text
    assert "Evidence ledger complete: False" in text
    assert text.count('"x\\n\\u001b[31m"') == 2
    assert "Refusal/failure: setup_write_scope_mismatch" in text
    assert "Do not refresh guards or retry automatically." in text
    assert "\x1b" not in text
    unknown = replace(evidence, command_status="incomplete")
    assert "— incomplete" in render_a1_review(unknown)
