"""Goal registrar and disposable qualified-input customer journey."""

import importlib
import json
import subprocess
import sys

import pytest
from aware_command_runtime import AwareCommandRegistry, run_cli
from aware_goal_native_cli.commands import register_goal_commands
from test_consumer_read import consumer_fixture
from test_native_provider import CUSTOMER_PATH, _git


def invoke(args):
    registry = AwareCommandRegistry()
    register_goal_commands(registry)
    return run_cli(registry, argv=args, prog="aware goal")


def common(root):
    return [
        "--repository-root",
        str(root),
        "--protocol-manifest",
        "aware.protocol.toml",
        "--goal-path",
        CUSTOMER_PATH,
    ]


@pytest.mark.parametrize("v3", [False, True])
def test_already_qualified_customer_goal_show_then_eligibility(
    tmp_path, monkeypatch, capsys, v3
):
    root, _ = consumer_fixture(tmp_path, monkeypatch, v3=v3)
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain=v1"))
    assert invoke(["show", *common(root), "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["operation"] == "show"
    assert result["reading"]["source"]["source_revision"] == before[0]
    assert (
        invoke(
            [
                "eligibility",
                *common(root),
                "--lane-key",
                "runtime",
                "--phase-key",
                "first",
            ]
        )
        == 0
    )
    summary = capsys.readouterr().out
    assert "Eligibility: eligible (observed)" in summary
    assert "Eligible is not authorized to RUN" in summary
    assert "Suggested next step:" in summary
    assert "permitted" not in summary.lower()
    assert (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "status", "--porcelain=v1"),
    ) == before


def test_summary_keeps_unknown_facts_explicit(tmp_path, monkeypatch, capsys):
    root, _ = consumer_fixture(tmp_path, monkeypatch)
    assert invoke(["show", *common(root)]) == 0
    summary = capsys.readouterr().out
    assert "definition only" in summary or "operational" in summary
    assert "unavailable" in summary and "Source epoch:" in summary
    assert "authorizes no work" in summary


def test_goal_family_calls_the_original_registrar(tmp_path, monkeypatch, capsys):
    from aware_goal_native_cli.customer_commands import (
        register_create_first_goal_commands,
    )

    root, _ = consumer_fixture(tmp_path, monkeypatch)
    agent = importlib.import_module("aware_agent_cli.main")
    registry = AwareCommandRegistry()
    agent.register_family_commands(registry, "goal")
    expected = AwareCommandRegistry()
    register_create_first_goal_commands(expected)
    assert registry.names() == expected.names() == ("create", "show", "eligibility")
    for actual, original in zip(registry, expected, strict=True):
        assert actual.handle is original.handle
    assert agent.main(["goal", "show", *common(root), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["operation"] == "show"


def test_standalone_and_agent_mount_return_the_same_eligibility(
    tmp_path, monkeypatch, capsys
):
    root, _ = consumer_fixture(tmp_path, monkeypatch)
    args = [
        "eligibility",
        *common(root),
        "--lane-key",
        "runtime",
        "--phase-key",
        "first",
        "--format",
        "json",
    ]
    assert importlib.import_module("aware_goal_native_cli.main").main(args) == 0
    standalone = json.loads(capsys.readouterr().out)
    assert importlib.import_module("aware_agent_cli.main").main(["goal", *args]) == 0
    assert json.loads(capsys.readouterr().out) == standalone


def test_missing_configuration_refuses_without_creating_it(
    tmp_path, monkeypatch, capsys
):
    root, _ = consumer_fixture(tmp_path, monkeypatch)
    (root / "aware.protocol.toml").unlink()
    before = _git(root, "status", "--porcelain=v1")
    assert invoke(["show", *common(root)]) == 2
    assert not capsys.readouterr().out
    assert not (root / "aware.protocol.toml").exists()
    assert _git(root, "status", "--porcelain=v1") == before


def test_legacy_configuration_refuses_without_upgrade(tmp_path, monkeypatch, capsys):
    root, _ = consumer_fixture(tmp_path, monkeypatch)
    manifest = root / "aware.protocol.toml"
    manifest.write_text(
        manifest.read_text().replace(
            "aware.collaboration.fs_v2", "aware.collaboration.fs_v1"
        )
    )
    before = manifest.read_bytes(), _git(root, "status", "--porcelain=v1")
    assert (
        invoke(
            [
                "eligibility",
                *common(root),
                "--lane-key",
                "runtime",
                "--phase-key",
                "first",
            ]
        )
        == 2
    )
    assert not capsys.readouterr().out
    assert (manifest.read_bytes(), _git(root, "status", "--porcelain=v1")) == before


def test_prerequisite_hints_are_explicit_not_guessed(tmp_path, monkeypatch, capsys):
    root, _ = consumer_fixture(tmp_path, monkeypatch)
    args = [
        "eligibility",
        *common(root),
        "--lane-key",
        "runtime",
        "--phase-key",
        "first",
    ]
    assert invoke([*args, "--prerequisite-goal", "bad-hint"]) == 2
    assert "invalid_or_duplicate_prerequisite_goal" in capsys.readouterr().err


def test_help_never_imports_or_invokes_source_provider():
    script = """
import sys, importlib.abc
sys.path[:0] = SOURCE_PATHS
class RejectProvider(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_goal_native_fs_adapter', 'aware_protocol_fs_adapter', 'aware_service')):
            raise AssertionError('help imported source owner: ' + fullname)
sys.meta_path.insert(0, RejectProvider())
from aware_agent_cli.main import main
try:
    main(['goal', '--help'])
except SystemExit as error:
    assert error.code == 0
""".replace("SOURCE_PATHS", repr(sys.path))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "show" in result.stdout and "eligibility" in result.stdout


def test_summary_reports_missing_evidence_without_promising_permission(
    tmp_path, monkeypatch, capsys
):
    root, _ = consumer_fixture(tmp_path, monkeypatch, dependency=True)
    assert (
        invoke(
            [
                "eligibility",
                *common(root),
                "--lane-key",
                "runtime",
                "--phase-key",
                "first",
            ]
        )
        == 0
    )
    summary = capsys.readouterr().out
    assert "Eligibility: held" in summary
    assert "not_evaluated: first-requires-later" in summary
    assert "coverage:" in summary
    assert "Eligible is not authorized to RUN" in summary
