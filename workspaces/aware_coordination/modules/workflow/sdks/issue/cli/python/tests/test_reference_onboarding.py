"""The standalone and real Agent mounting expose identical owner guidance."""

from __future__ import annotations

import json

import pytest
from aware_agent_cli.main import main as agent_main
from aware_issue_cli.main import main as issue_main
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import IssueEnsureSnapshotRequest, IssueSdkOperationClient
from test_provider import _repository

EXAMPLE = "fb/2026-10-11/json-checker-draft"
INVALID = "docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md"
COMMANDS = (
    "resolve-read-projection",
    "ensure-snapshot",
    "start-progress",
    "block",
    "resume",
    "set-owner",
    "bind-scope",
    "append-update",
    "append-evidence",
    "close",
    "commit-workspace",
    "publish-close",
)


@pytest.mark.parametrize("mounted", [False, True])
@pytest.mark.parametrize("command", COMMANDS)
def test_every_target_help_explains_reference_not_markdown_path(
    capsys, mounted, command
):
    entrance = agent_main if mounted else issue_main
    arguments = ["issue", command, "--help"] if mounted else [command, "--help"]
    with pytest.raises(SystemExit) as exit_value:
        entrance(arguments)
    assert exit_value.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "fb/YYYY-MM-DD/<slug>" in help_text
    assert "lowercase letters or digits" in help_text
    assert "single hyphens" in help_text
    assert EXAMPLE in help_text
    assert "not a Markdown path" in help_text


@pytest.mark.parametrize("mounted", [False, True])
@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize("command", ["resolve-read-projection", "ensure-snapshot"])
def test_invalid_reference_cli_preserves_exact_sdk_diagnostics_and_no_effects(
    tmp_path, capsys, mounted, format_name, command
):
    repository = tmp_path / "absent"
    kwargs = {
        "issue_ref": INVALID,
        "title": "JSON checker",
        "priority": "P1",
        "client_intent_id": "test:guidance",
        "actor_ref": "codex-reference-test",
        "actor_evidence_ref": "test:synthetic-harness",
    }
    original = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    ).ensure_issue_snapshot(IssueEnsureSnapshotRequest(**kwargs))
    arguments = [
        command,
        "--repository-root",
        str(repository),
        "--issue-ref",
        INVALID,
        "--format",
        format_name,
    ]
    if command == "ensure-snapshot":
        for name in (
            "title",
            "priority",
            "client_intent_id",
            "actor_ref",
            "actor_evidence_ref",
        ):
            arguments.extend(["--" + name.replace("_", "-"), kwargs[name]])
    entrance = agent_main if mounted else issue_main
    assert entrance(["issue", *arguments] if mounted else arguments) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["issue_ref"] == INVALID
    assert payload["outcome"] == "malformed"
    assert payload["diagnostics"] == list(original.diagnostics)
    assert payload["diagnostics"][0] == "issue_ref_invalid"
    assert EXAMPLE in " ".join(payload["diagnostics"])
    assert not repository.exists()


@pytest.mark.parametrize("mounted", [False, True])
def test_documented_reference_creates_and_observes_issue_through_real_owners(
    tmp_path, monkeypatch, capsys, mounted
):
    repository = _repository(tmp_path)
    monkeypatch.setenv("CODEX_THREAD_ID", "reference-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    entrance = agent_main if mounted else issue_main
    target = ["--repository-root", str(repository), "--issue-ref", EXAMPLE]
    create = [
        "ensure-snapshot",
        *target,
        "--title",
        "JSON checker draft",
        "--priority",
        "P1",
        "--owner-ref",
        "codex-reference-test",
        "--actor-ref",
        "codex-reference-test",
        "--actor-evidence-ref",
        "harness:reference-test",
        "--client-intent-id",
        "test:create-documented-reference",
    ]
    assert entrance(["issue", *create] if mounted else create) == 0
    created = json.loads(capsys.readouterr().out)
    assert created["outcome"] == "applied"
    assert created["issue_ref"] == EXAMPLE
    source = repository / "docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md"
    before = source.read_bytes()
    read = ["resolve-read-projection", *target]
    assert entrance(["issue", *read] if mounted else read) == 0
    observed = json.loads(capsys.readouterr().out)
    assert observed["outcome"] == "found"
    assert observed["issue_ref"] == EXAMPLE
    assert source.read_bytes() == before
