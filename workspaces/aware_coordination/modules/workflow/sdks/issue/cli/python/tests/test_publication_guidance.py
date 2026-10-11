"""Both CLI entrances explain existing publication boundaries without effects."""

from __future__ import annotations

import importlib

import pytest
from aware_agent_cli.main import main as agent_main

cli = importlib.import_module("aware_issue_cli.main")


@pytest.mark.parametrize("mounted", [False, True])
@pytest.mark.parametrize(
    ("command", "required"),
    [
        (
            "publish-close",
            (
                "Two non-atomic effects",
                "same original owners in this invocation",
                "publication may succeed while closeout refuses",
                "cannot restore completion authority",
                "issue_publication_source_stale",
                "issue_source_out_of_scope",
                "do not silently refresh guards",
                "No automatic retry",
            ),
        ),
        (
            "commit-workspace",
            (
                "retain full JSON",
                "known publication and unknown cleanup",
                "issue_publication_source_stale",
                "issue_source_out_of_scope",
                "No automatic retry",
            ),
        ),
        (
            "close",
            (
                "issue_closeout_original_implementation_required",
                "saved Git receipt",
                "request supported owner recovery",
                "do not republish to regain authority",
            ),
        ),
        (
            "present-receipt",
            (
                "no operation replay, guard refresh or authority restoration",
                "Exit 0 means presentation succeeded",
                "not that the recorded operation succeeded",
                "Currentness is not revalidated",
            ),
        ),
    ],
)
def test_publication_help_explains_supported_boundary_without_owner_calls(
    mounted, command, required, monkeypatch, capsys
):
    text = _help_text(command, mounted, monkeypatch, capsys)
    for phrase in required:
        assert phrase in text


def _help_text(command, mounted, monkeypatch, capsys):
    # Both entrances parse help; neither invokes an operational owner.
    def forbidden(*args, **kwargs):
        raise AssertionError("Help must not construct or invoke an owner")

    for name in (
        "FilesystemIssueOperationProvider",
        "IssueSdkOperationClient",
        "create_repository_client",
    ):
        monkeypatch.setattr(cli, name, forbidden)
    entrance = agent_main if mounted else cli.main
    arguments = ["issue", command, "--help"] if mounted else [command, "--help"]
    with pytest.raises(SystemExit) as caught:
        entrance(arguments)
    assert caught.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    return " ".join(captured.out.split())


@pytest.mark.parametrize("mounted", [False, True])
@pytest.mark.parametrize("command", ["commit-workspace", "publish-close"])
def test_publication_guard_and_preview_are_not_other_coordinates(
    mounted, command, monkeypatch, capsys
):
    text = _help_text(command, mounted, monkeypatch, capsys)
    assert "--expected-issue-source-sha256" in text
    assert "projection.source.digest from resolve-read-projection --format json" in text
    assert "Exact Issue Markdown bytes" in text
    assert "Not HEAD, a Protocol semantic digest or a work-file digest" in text
    assert "same guard without refreshing it" in text
    assert "Preview implementation only; no publication or closeout" in text
    assert "Apply prepares afresh" in text
    assert "earlier HEAD and work-file bytes are not pinned" in text


@pytest.mark.parametrize("mounted", [False, True])
@pytest.mark.parametrize(
    "command",
    [
        "start-progress",
        "block",
        "resume",
        "set-owner",
        "bind-scope",
        "append-update",
        "append-evidence",
        "close",
    ],
)
def test_mutation_guard_is_exact_issue_source_not_silent_refresh(
    mounted, command, monkeypatch, capsys
):
    text = _help_text(command, mounted, monkeypatch, capsys)
    assert "--expected-source-sha256" in text
    assert "Exact Issue Markdown bytes" in text
    assert "projection.source.digest" in text
    assert "never silently refresh on refusal" in text
    assert "fb/2026-10-11/json-checker-draft" in text
