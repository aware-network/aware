"""Source registrar parity; synthetic transport cases are not publication proof."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import tomllib
import types
from dataclasses import replace
from pathlib import Path

import pytest
from aware_command_runtime import (
    AwareCommandRegistry,
    CommandRegistrationError,
    build_parser,
    dispatch_command,
)
from test_issue_sdk_result_boundary import CASES, result_for
from test_sdk_return_failure import (
    ISSUE_REF,
    ReturnedFailure,
    _digest,
    _git,
    _mutation_kwargs,
    _publication_repository,
    _publish_implementation,
)

cli = importlib.import_module("aware_issue_cli.main")
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
)


@pytest.fixture(scope="module")
def predecessor():
    root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / ".git").exists()
    )
    path = "workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/aware_issue_cli/main.py"
    source = subprocess.check_output(
        ["git", "show", "3d6f9cd9b09a53fce61219022824a5715417ebfa:" + path],
        cwd=root,
        timeout=10,
    )
    assert (
        hashlib.sha256(source).hexdigest()
        == "ec2039f6a23e066ae230b97169a0ee04c6d417f6fbc3b9472f56d3ee4172ee46"
    )
    module = types.ModuleType("aware_issue_cli.registrar_predecessor_oracle")
    module.__package__ = "aware_issue_cli"
    # Exact hash-pinned authored test oracle; never an operational CLI fallback.
    exec(compile(source, path, "exec"), module.__dict__)  # noqa: S102
    return module


def invoke_mounted(argv, *, context=None):
    """Test mounting only; the genuine runtime dispatches the supplier handler."""
    registry = AwareCommandRegistry()
    cli.register_issue_commands(registry)
    parser = argparse.ArgumentParser(prog="test-composition")
    family = parser.add_subparsers(dest="command", required=True).add_parser("issue")
    leaves = family.add_subparsers(dest="leaf", required=True)
    for spec in registry:
        leaf = leaves.add_parser(spec.name)
        spec.configure_parser(leaf)
        leaf.set_defaults(_aware_command_name=spec.name)
    mounted = ["issue", *argv]
    return dispatch_command(
        registry,
        args=parser.parse_args(mounted),
        parser=parser,
        argv=mounted,
        context=context,
    )


def arguments(command, request, format_name):
    values = [
        command,
        "--repository-root",
        "/explicit/repository",
        "--protocol-source",
        "selection/aware.protocol.toml",
        "--issue-ref",
        request.issue_ref,
        "--format",
        format_name,
    ]
    if command == "resolve-read-projection":
        return values
    if command == "commit-workspace":
        return values + [
            "--expected-issue-source-sha256",
            request.expected_issue_source_sha256,
            "--path",
            "src/a.py",
            "--message",
            request.message,
            "--actor-ref",
            request.actor_ref,
            "--actor-evidence-ref",
            request.actor_evidence_ref,
        ]
    values += [
        "--client-intent-id",
        request.client_intent_id,
        "--actor-ref",
        request.actor_ref,
        "--actor-evidence-ref",
        request.actor_evidence_ref,
    ]
    if command == "ensure-snapshot":
        return values + [
            "--title",
            request.title,
            "--priority",
            request.priority,
        ]
    values += ["--expected-source-sha256", request.expected_source_sha256]
    additional = {
        "set-owner": ["--new-owner-ref", "codex-next"],
        "bind-scope": ["--scope-path", "src/a.py"],
        "append-update": ["--message", "test"],
        "append-evidence": ["--path", "evidence:x"],
        "close": [
            "--resolution",
            "test",
            "--verified-by",
            "test",
            "--publication-receipt-ref",
            "git:" + "a" * 40,
        ],
    }
    return values + additional.get(command, [])


def test_registration_is_pure_and_presentation_is_not_an_sdk_operation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("registration must not invoke an owner")

    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", forbidden)
    monkeypatch.setattr(cli, "IssueSdkOperationClient", forbidden)
    registry = AwareCommandRegistry()
    cli.register_issue_commands(registry)
    assert registry.names() == ("present-receipt", *COMMANDS)
    for spec, (method, request) in zip(tuple(registry)[1:], CASES, strict=True):
        expected = (
            "issue_sdk.resolve_issue_read_projection"
            if method == "resolve_read_projection"
            else request.operation_ref
        )
        assert spec.operation_ref == expected
        assert spec.projection_ref is None
        assert spec.source == "aware_issue_cli"
    presentation = registry.require("present-receipt")
    assert presentation.operation_ref is None
    assert presentation.projection_ref == "aware_issue_cli.present_receipt"
    build_parser(registry, prog="test-composition")


@pytest.mark.parametrize("collision", ["present-receipt", *COMMANDS])
def test_collision_refuses_whole_family_without_replacement(collision):
    registry = AwareCommandRegistry()
    registry.register_command(name=collision, help="foreign", handle=lambda _: 91)
    original = tuple(registry)
    with pytest.raises(CommandRegistrationError, match="already registered"):
        cli.register_issue_commands(registry)
    assert tuple(registry) == original


@pytest.mark.parametrize("command,case", zip(COMMANDS, CASES, strict=True))
@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize("malformed", [False, True])
def test_every_operation_preserves_request_result_stream_and_exit(
    monkeypatch, capsys, predecessor, command, case, format_name, malformed
):
    method, request = case
    result = result_for(method, request)
    if malformed:
        result = replace(result, issue_ref="fb/2026-10-08/foreign")
    received = []
    constructed = []

    class RecordingProvider:
        def __getattr__(self, selected):
            assert selected == method

            def call(actual):
                received.append(actual)
                return result

            return call

    def provider(**kwargs):
        constructed.append(kwargs)
        return RecordingProvider()

    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", provider)
    monkeypatch.setattr(predecessor, "FilesystemIssueOperationProvider", provider)
    argv = arguments(command, request, format_name)
    previous_exit = predecessor.main(argv)
    previous = capsys.readouterr()
    native_exit = cli.main(argv)
    native = capsys.readouterr()
    mounted_exit = invoke_mounted(
        argv, context={"actor_ref": "forged", "authorizes_retry": True}
    )
    mounted = capsys.readouterr()
    assert mounted_exit == native_exit == previous_exit
    assert mounted == native == previous and native.err == ""
    assert received == [request, request, request]
    assert (
        constructed
        == [
            {
                "repository_root": "/explicit/repository",
                "protocol_source_ref": "selection/aware.protocol.toml",
            }
        ]
        * 3
    )
    payload = json.loads(mounted.out)
    if malformed:
        assert mounted_exit == 2
        assert payload["effect"] == "unknown"
        assert payload["authorizes_retry"] is False
        assert payload["provider_report_grade"] == "unvalidated_provider_report"
        if command == "commit-workspace":
            assert payload["provider_result"]["commit_hash"] == "a" * 40
            assert payload["provider_result"]["index_reconciliation_pending"] is True
    elif command == "commit-workspace":
        assert mounted_exit == 0
        assert payload["reference_update"] == "cas_applied"
        index_result = payload["index_result"] if format_name == "summary" else payload
        assert index_result["index_reconciliation_pending"] is True
    else:
        assert mounted_exit == 2  # genuine typed absent/stale transport result


@pytest.mark.parametrize("format_name", ["json", "summary"])
def test_mounted_saved_presentation_never_calls_provider(
    tmp_path, monkeypatch, capsys, format_name
):
    receipt = tmp_path / "receipt.json"
    value = {"operation_ref": "issue_sdk.commit_workspace", "outcome": "unknown"}
    receipt.write_text(json.dumps(value))
    original = receipt.read_bytes()

    def forbidden(*args, **kwargs):
        raise AssertionError("presentation is not replay")

    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", forbidden)
    argv = [
        "present-receipt",
        "--receipt-path",
        str(receipt),
        "--format",
        format_name,
    ]
    assert cli.main(argv) == invoke_mounted(argv) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2 and lines[0] == lines[1]
    payload = json.loads(lines[1])
    assert payload["presentation"]["operation_invoked"] is False
    assert payload["presentation"]["authority_restored"] is False
    assert payload["result"]["outcome"] == "unknown"
    assert receipt.read_bytes() == original


@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize("mode", ["foreign", "raise"])
@pytest.mark.parametrize("method", ["commit_workspace", "close_issue"])
def test_mounted_real_publication_then_invalid_return_preserves_effects(
    tmp_path, monkeypatch, capsys, format_name, mode, method
):
    # Reuse the original owner fixture and return-failure injector. Git fixture
    # preparation is not customer tooling or another publication implementation.
    repository, target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    provider = cli.FilesystemIssueOperationProvider(repository_root=repository)
    argv = [
        "commit-workspace" if method == "commit_workspace" else "close",
        "--repository-root",
        str(repository),
        "--issue-ref",
        ISSUE_REF,
        "--format",
        format_name,
        "--actor-ref",
        "codex-example",
        "--actor-evidence-ref",
        "evidence:boundary",
    ]
    if method == "close_issue":
        issue.write_text(
            issue.read_text().replace(
                "- `src/example.py`",
                "- `src/example.py`\n- `docs/issues/2026/09/20/fb-2026-09-20-example.md`",
            )
        )
        implementation = _publish_implementation(
            repository=repository,
            issue=issue,
            client=cli.IssueSdkOperationClient(provider),
        )
        argv += [
            "--expected-source-sha256",
            _digest(issue),
            "--client-intent-id",
            _mutation_kwargs(issue, intent="close-boundary")["client_intent_id"],
            "--resolution",
            "Test complete",
            "--verified-by",
            "test:proof",
            "--publication-receipt-ref",
            implementation,
        ]
    else:
        argv += [
            "--expected-issue-source-sha256",
            _digest(issue),
            "--path",
            "src/example.py",
            "--message",
            "real mounted boundary proof",
        ]
    foreign = repository / "foreign.txt"
    foreign.write_text("foreign staged bytes\n")
    _git(repository, "add", "foreign.txt")
    foreign.write_text("foreign working bytes\n")
    index = _git(repository, "ls-files", "--stage", "foreign.txt")
    before = _git(repository, "rev-parse", "HEAD")
    wrapped = ReturnedFailure(provider, method, mode)
    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", lambda **_: wrapped)
    assert invoke_mounted(argv) == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert payload["effect"] == "unknown" and payload["authorizes_retry"] is False
    report = payload["provider_result"]
    head = _git(repository, "rev-parse", "HEAD")
    assert _git(repository, "rev-list", "--count", f"{before}..{head}") == "1"
    assert wrapped.calls == 1
    field = (
        "publication_receipt_ref"
        if method == "commit_workspace"
        else "closeout_publication_receipt_ref"
    )
    assert report[field] == "git:" + head
    assert report["index_reconciliation_pending"] is False
    if method == "close_issue":
        assert "- Status: Closed" in issue.read_text()
    else:
        assert report["reference_update"] == "cas_applied"
        assert _git(repository, "show", "HEAD:src/example.py") == "after"
    assert target.read_text() == "after\n"
    assert _git(repository, "ls-files", "--stage", "foreign.txt") == index
    assert foreign.read_text() == "foreign working bytes\n"


def test_successor_dependency_and_existing_entrypoint_are_explicit():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert project["project"]["version"] == "0.8.0"
    assert "aware-command-runtime>=0.1.1,<0.2.0" in project["project"]["dependencies"]
    assert project["project"]["scripts"] == {
        "aware-issue-cli": "aware_issue_cli.main:main"
    }


def test_labels_match_real_authored_operation_selection():
    from test_issue_sdk_authored_closure import source_contract

    contract = source_contract()
    registry = AwareCommandRegistry()
    cli.register_issue_commands(registry)
    assert {
        spec.operation_ref for spec in registry if spec.operation_ref is not None
    } == {operation.operation_ref for operation in contract.manifest.operations}


@pytest.mark.parametrize("command", ["present-receipt", *COMMANDS])
def test_argument_actions_defaults_and_requiredness_match_predecessor(
    predecessor, command
):
    old = predecessor._parser()
    registry = AwareCommandRegistry()
    cli.register_issue_commands(registry)
    new = cli._parser(registry)

    def shape(parser):
        sub = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        return tuple(
            (
                type(action).__name__,
                tuple(action.option_strings),
                action.dest,
                action.required,
                action.default,
                action.nargs,
                action.choices,
                action.type,
            )
            for action in sub.choices[command]._actions
        )

    assert shape(old) == shape(new)
