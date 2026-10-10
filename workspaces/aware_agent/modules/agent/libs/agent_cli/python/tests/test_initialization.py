"""Real source SDK chains in synthetic repositories, not installed onboarding."""

from __future__ import annotations

import builtins
import json
import os
import stat
import subprocess
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest
from aware_agent_cli.initialization import register_init_command
from aware_agent_cli.main import main
from aware_command_runtime import AwareCommandRegistry, CommandRegistrationError
from packaging.requirements import Requirement


@pytest.fixture(autouse=True)
def execution(monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "agent-init-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False, timeout=10
    )


def descriptors():
    return set(os.listdir("/proc/self/fd"))


def invoke(root, capsys, *args):
    before = descriptors()
    code = main(["init", "--repo-root", str(root), *args])
    streams = capsys.readouterr()
    assert not streams.err
    assert descriptors() == before
    return code, json.loads(streams.out)


@pytest.mark.parametrize("exists", [False, True])
@pytest.mark.parametrize("format_name", ["json", "summary"])
def test_absent_preview_is_prospective_not_an_admission(
    tmp_path, capsys, exists, format_name
):
    root = tmp_path / "customer"
    if exists:
        root.mkdir()
    code, payload = invoke(root, capsys, "--create-repository", "--format", format_name)
    assert code == 0 and payload["status"] == "planned"
    assert payload["workspace"]["result"]["outcome"] == "planned"
    assert payload["protocol"]["status"] == "prospective_only"
    assert "result" not in payload["protocol"]
    assert payload["effect"] == "none" and not payload["completion_verified"]
    assert not payload["authorizes_retry"]
    assert not (root / ".git").exists() and root.exists() == exists
    files = payload["protocol"]["rendered_input"]["files"]
    assert all(("content_utf8" in item) == (format_name == "json") for item in files)
    assert all(item["source_sha256"].startswith("sha256:") for item in files)


@pytest.mark.parametrize("exists", [False, True])
@pytest.mark.parametrize("templates", [False, True])
def test_new_repository_apply_preserves_both_receipts(
    tmp_path, capsys, exists, templates
):
    root = tmp_path / "customer"
    if exists:
        root.mkdir()
    flags = ["--create-repository", "--apply", "--issue-root", "work/issues"]
    if not templates:
        flags += ["--no-agent-contract"]
    code, payload = invoke(root, capsys, *flags)
    assert (
        code == 0
        and payload["status"] == "completed"
        and payload["completion_verified"]
    )
    assert payload["effect"] == "applied" and not payload["authorizes_retry"]
    workspace, protocol = payload["workspace"]["result"], payload["protocol"]["result"]
    assert workspace["outcome"] == "created" and protocol["outcome"] == "initialized"
    assert workspace["request"]["create_if_missing"]
    assert workspace["attempt_ref"].startswith("repository-attempt:")
    assert protocol["attempt_ref"].startswith("protocol-attempt:")
    assert workspace["cleanup_state"] == protocol["cleanup_state"] == "completed"
    assert (
        workspace["execution_id"] == protocol["execution_id"] == "codex-agent-init-test"
    )
    assert workspace["head"] is None
    assert (root / "AGENTS.md").exists() == templates
    assert (root / "work/issues/PROTOCOL.md").exists() == templates
    manifest = tomllib.loads((root / "aware.protocol.toml").read_text())
    assert manifest["protocol"]["profile"] == "aware.collaboration.fs_v1"
    assert manifest["records"]["issue"]["root"] == "work/issues"
    assert all(
        manifest["records"][name]["role"] == "unavailable"
        for name in ("goal", "specification", "feed", "evidence")
    )
    assert git(root, "symbolic-ref", "HEAD").stdout == b"refs/heads/main\n"
    assert git(root, "rev-parse", "--verify", "HEAD").returncode != 0
    assert git(root, "remote").stdout == b""
    assert not (root / ".git/index").exists()
    assert stat.S_IMODE((root / "aware.protocol.toml").stat().st_mode) == 0o644
    assert stat.S_IMODE((root / "work").stat().st_mode) == 0o700


@pytest.mark.parametrize("apply", [False, True])
def test_missing_creation_intent_retains_owner_diagnostics(tmp_path, capsys, apply):
    root = tmp_path / "customer"
    code, payload = invoke(root, capsys, *(["--apply"] if apply else []))
    assert code == 2 and payload["effect"] == "none" and not root.exists()
    stage = payload["workspace"]
    evidence = stage.get("result", stage.get("error"))
    assert evidence["diagnostics"]
    assert payload["protocol"]["status"] == "input_validated"
    assert "result" not in payload["protocol"]


@pytest.mark.parametrize("apply", [False, True])
def test_existing_repository_preserves_foreign_work_and_index(tmp_path, capsys, apply):
    root = tmp_path / "existing"
    root.mkdir(mode=0o750)
    assert git(root, "init", "--initial-branch=foreign").returncode == 0
    foreign = root / "foreign.txt"
    foreign.write_text("retained\n")
    foreign.chmod(0o640)
    assert git(root, "add", "foreign.txt").returncode == 0
    assert (
        git(
            root, "remote", "add", "origin", "https://example.invalid/fixture"
        ).returncode
        == 0
    )
    index = (root / ".git/index").read_bytes()
    head = (root / ".git/HEAD").read_bytes()
    code, payload = invoke(root, capsys, *(["--apply"] if apply else []))
    assert code == 0 and payload["workspace"]["result"]["outcome"] == "existing"
    assert payload["protocol"]["result"]["outcome"] == (
        "initialized" if apply else "planned"
    )
    assert (
        foreign.read_text() == "retained\n"
        and stat.S_IMODE(foreign.stat().st_mode) == 0o640
    )
    assert (root / ".git/index").read_bytes() == index
    assert (root / ".git/HEAD").read_bytes() == head
    assert git(root, "remote").stdout == b"origin\n"
    assert stat.S_IMODE(root.stat().st_mode) == 0o750
    assert (root / "aware.protocol.toml").exists() == apply


@pytest.mark.parametrize(
    "issue_root",
    [
        "../escape",
        "/absolute",
        ".git",
        "docs/.git",
        "AGENTS.md",
        "aware.protocol.toml/sub",
        "docs//issues",
    ],
)
def test_invalid_protocol_input_refuses_before_git_creation(
    tmp_path, capsys, issue_root
):
    root = tmp_path / "customer"
    code, payload = invoke(
        root, capsys, "--create-repository", "--apply", "--issue-root", issue_root
    )
    assert code == 2 and payload["workspace"]["status"] == "not_started"
    assert payload["effect"] == "none" and not root.exists()


@pytest.mark.parametrize(
    "providers",
    [
        ({},),
        ({"CODEX_THREAD_ID": ""},),
        ({"CODEX_THREAD_ID": "has space"},),
        ({"CODEX_THREAD_ID": "codex", "CLAUDE_CODE_SESSION_ID": "claude"},),
    ],
)
def test_missing_or_ambiguous_harness_refuses(tmp_path, capsys, monkeypatch, providers):
    for name in ("CODEX_THREAD_ID", "CLAUDE_CODE_SESSION_ID"):
        monkeypatch.delenv(name, raising=False)
    for name, value in providers[0].items():
        monkeypatch.setenv(name, value)
    root = tmp_path / "customer"
    code, payload = invoke(root, capsys, "--create-repository", "--apply")
    assert code == 2 and payload["preflight_error"]["diagnostics"] == [
        "unambiguous_provider_execution_required"
    ]
    assert not root.exists() and payload["effect"] == "none"


def test_claude_harness_is_not_renamed(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("CODEX_THREAD_ID")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "genuine-claude")
    _, payload = invoke(tmp_path / "customer", capsys, "--create-repository", "--apply")
    assert payload["execution_id"] == "claude_code-genuine-claude"
    assert (
        payload["workspace"]["result"]["execution_id"] == "claude_code-genuine-claude"
    )
    assert "CODEX_THREAD_ID" not in os.environ


@pytest.mark.parametrize(
    "target", ["relative", "symlink", "missing_parent", "nonempty", "nested"]
)
def test_physical_targets_refuse_without_adopting_existing_work(
    tmp_path, capsys, target
):
    root = tmp_path / "customer"
    if target == "relative":
        root = Path("relative")
    elif target == "symlink":
        other = tmp_path / "other"
        other.mkdir()
        root.symlink_to(other, target_is_directory=True)
    elif target == "missing_parent":
        root = tmp_path / "absent" / "customer"
    elif target == "nonempty":
        root.mkdir()
        (root / "foreign.txt").write_text("preserve")
    elif target == "nested":
        root.mkdir()
        assert git(root, "init").returncode == 0
        root /= "nested"
    code, payload = invoke(root, capsys, "--create-repository", "--apply")
    assert code == 2 and payload["effect"] == "none"
    if target == "nonempty":
        assert (root / "foreign.txt").read_text() == "preserve"
    else:
        assert not (root / ".git").exists()


def test_protocol_refusal_after_real_git_creation_keeps_first_receipt(
    tmp_path, capsys, monkeypatch
):
    from aware_protocol_sdk.bootstrap import ProtocolBootstrapClient

    root = tmp_path / "customer"
    original = ProtocolBootstrapClient.plan_initialization
    calls = []

    def competing_file(client, request):
        calls.append(request)
        assert (root / ".git/HEAD").exists()
        (root / "AGENTS.md").write_text("foreign winner\n")
        return original(client, request)

    monkeypatch.setattr(ProtocolBootstrapClient, "plan_initialization", competing_file)
    code, payload = invoke(root, capsys, "--create-repository", "--apply")
    assert code == 2 and len(calls) == 1
    assert payload["workspace"]["result"]["outcome"] == "created"
    assert payload["workspace"]["result"]["effects"]
    assert payload["protocol"]["error"]["phase"] == "plan"
    assert payload["effect"] == "applied" and not payload["completion_verified"]
    assert (root / "AGENTS.md").read_text() == "foreign winner\n"
    assert not (root / "aware.protocol.toml").exists()


def test_partial_protocol_publication_retains_unknown_cleanup(
    tmp_path, capsys, monkeypatch
):
    from aware_file_system.retained_bootstrap import RetainedBootstrapCreation

    root = tmp_path / "customer"
    original = RetainedBootstrapCreation.create_next_file
    calls = []

    def interrupted(handle):
        calls.append(handle)
        original(handle)
        raise KeyboardInterrupt("controlled interruption after file creation")

    monkeypatch.setattr(RetainedBootstrapCreation, "create_next_file", interrupted)
    code, payload = invoke(root, capsys, "--create-repository", "--apply")
    assert code == 2 and len(calls) == 1
    assert payload["workspace"]["result"]["outcome"] == "created"
    error = payload["protocol"]["error"]
    assert error["effects"] and error["cleanup_state"] == "unknown"
    assert not error["authorizes_retry"] and not payload["authorizes_retry"]
    assert (root / "aware.protocol.toml").exists() and (root / ".git/HEAD").exists()
    assert not (root / "AGENTS.md").exists()


@pytest.mark.parametrize("format_name", ["json", "summary"])
def test_workspace_return_failure_keeps_actual_creation_evidence(
    tmp_path, capsys, monkeypatch, format_name
):
    from aware_workspace_runtime.repository_preparation import (
        WorkspaceRepositoryPreparationRuntime,
    )

    original = WorkspaceRepositoryPreparationRuntime.prepare_repository

    def invalid(provider, request, *, admission=None):
        result = original(provider, request, admission=admission)
        return replace(result, request=replace(result.request, create_if_missing=False))

    monkeypatch.setattr(
        WorkspaceRepositoryPreparationRuntime, "prepare_repository", invalid
    )
    root = tmp_path / "customer"
    code, payload = invoke(
        root, capsys, "--create-repository", "--apply", "--format", format_name
    )
    assert code == 2 and (root / ".git/HEAD").exists()
    evidence = payload["workspace"]["error"]
    assert evidence["provider_invoked"] and evidence["attempt_ref"]
    assert len(evidence["effects"]) == 3 and evidence["reported_result"]
    assert payload["protocol"]["status"] == "input_validated"
    assert not payload["authorizes_retry"]


@pytest.mark.parametrize("format_name", ["json", "summary"])
def test_protocol_return_failure_retains_known_publication(
    tmp_path, capsys, monkeypatch, format_name
):
    from aware_protocol_runtime.bootstrap import _BootstrapRuntime

    original = _BootstrapRuntime.initialize_profile

    def invalid(provider, request, *, admission=None):
        result = original(provider, request, admission=admission)
        return replace(result, request=replace(result.request, issue_root="foreign"))

    monkeypatch.setattr(_BootstrapRuntime, "initialize_profile", invalid)
    root = tmp_path / "customer"
    code, payload = invoke(
        root, capsys, "--create-repository", "--apply", "--format", format_name
    )
    assert code == 2 and (root / "aware.protocol.toml").exists()
    error = payload["protocol"]["error"]
    assert error["effects"] and error["attempt_ref"] and error["reported_result"]
    assert error["request"]["issue_root"] == "docs/issues"
    assert payload["workspace"]["result"]["outcome"] == "created"
    assert not payload["authorizes_retry"]


def test_repeat_apply_does_not_republish_or_overwrite(tmp_path, capsys):
    root = tmp_path / "customer"
    assert invoke(root, capsys, "--create-repository", "--apply")[0] == 0
    before = {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    code, payload = invoke(root, capsys, "--create-repository", "--apply")
    assert code == 2 and not payload["completion_verified"]
    assert before == {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    assert not payload["authorizes_retry"]


def test_root_and_init_help_do_not_import_suppliers():
    script = """
import sys, importlib.abc
sys.path[:0] = ROOTS
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_workspace', 'aware_protocol', 'aware_issue', 'aware_specification', 'aware_file_system')):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Refuse())
from aware_agent_cli.main import main
for argv in (['--help'], ['init', '--help']):
    try: main(argv)
    except SystemExit as error: assert error.code == 0
    else: raise AssertionError('help did not stop')
""".replace("ROOTS", repr(sys.path))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--create-repository" in result.stdout and "--repo-root" in result.stdout


def test_registrar_collision_refuses():
    registry = AwareCommandRegistry()
    register_init_command(registry)
    with pytest.raises(CommandRegistrationError):
        register_init_command(registry)


@pytest.mark.parametrize(
    "module",
    [
        "aware_workspace_sdk.repository_preparation",
        "aware_protocol_sdk.bootstrap",
        "aware_protocol_cli.bootstrap",
    ],
)
def test_missing_public_integration_refuses_before_owner_dispatch(
    tmp_path, capsys, monkeypatch, module
):
    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == module:
            raise ImportError("controlled missing integration")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    root = tmp_path / "customer"
    code, payload = invoke(root, capsys, "--create-repository", "--apply")
    assert code == 2 and payload["effect"] == "none" and not root.exists()
    assert payload["workspace"]["status"] == "not_started"


def test_first_issue_is_created_through_original_sdk_after_init(tmp_path, capsys):
    root = tmp_path / "customer"
    assert invoke(root, capsys, "--create-repository", "--apply")[0] == 0
    before = descriptors()
    argv = [
        "issue",
        "ensure-snapshot",
        "--repository-root",
        str(root),
        "--issue-ref",
        "fb/2026-10-10/customer-task",
        "--title",
        "Customer task",
        "--priority",
        "P1",
        "--owner-ref",
        "codex-agent-init-test",
        "--problem",
        "Need a governed task",
        "--objective",
        "Preserve coordination",
        "--acceptance",
        "Tooling-created Issue observes correctly",
        "--client-intent-id",
        "initial-customer-task",
        "--actor-ref",
        "codex-agent-init-test",
        "--actor-evidence-ref",
        "evidence:synthetic-harness",
    ]
    assert main(argv) == 0
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["outcome"] == "applied"
    issue = root / "docs/issues/2026/10/10/fb-2026-10-10-customer-task.md"
    assert issue.is_file() and "Customer task" in issue.read_text()
    assert git(root, "rev-parse", "--verify", "HEAD").returncode != 0
    assert not (root / ".git/index").exists() and descriptors() == before


@pytest.mark.parametrize("owner", ["workspace", "protocol"])
def test_late_plan_release_failure_preserves_original_result(
    tmp_path, capsys, monkeypatch, owner
):
    if owner == "workspace":
        from aware_workspace_sdk.repository_preparation import (
            RepositoryPreparationPlan as Plan,
        )
    else:
        from aware_protocol_sdk.bootstrap import ProtocolBootstrapPlan as Plan
    original = Plan.release

    def interrupted(plan):
        original(plan)
        raise KeyboardInterrupt("controlled consumer release observation failure")

    monkeypatch.setattr(Plan, "release", interrupted)
    root = tmp_path / "customer"
    code, payload = invoke(root, capsys, "--create-repository", "--apply")
    assert code == 2 and not payload["completion_verified"]
    stage = payload[owner]
    assert stage["result"]["outcome"] == (
        "created" if owner == "workspace" else "initialized"
    )
    assert stage["result"]["effects"] and stage["cleanup_unverified"]
    assert payload["effect"] == "unknown" and not payload["authorizes_retry"]
    assert (root / ".git/HEAD").exists()
    assert (root / "aware.protocol.toml").exists() == (owner == "protocol")


def test_real_init_does_not_import_service_or_generated_packages(tmp_path):
    root = tmp_path / "isolated"
    script = """
import sys, importlib.abc
sys.path[:0] = ROOTS
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_service', 'aware_local_service', 'aware_issue_local_service', 'aware_workspace_sdk_service', 'aware_ontology', 'aware_issue_service_api', 'aware_workspace_service_api')):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Refuse())
from aware_agent_cli.main import main
raise SystemExit(main(['init', '--repo-root', TARGET, '--create-repository', '--apply']))
""".replace("ROOTS", repr(sys.path)).replace("TARGET", repr(str(root)))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["completion_verified"]
    assert (root / "aware.protocol.toml").exists()


def test_successor_metadata_names_accepted_ports_and_floors():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())[
        "project"
    ]
    deps = {r.name: r for r in map(Requirement, project["dependencies"])}
    assert project["version"] == "0.2.0a2"
    assert deps["aware-workspace-sdk"].extras == {"preparation"}
    assert "0.2.1" in deps["aware-workspace-sdk"].specifier
    assert "0.2.0" not in deps["aware-workspace-sdk"].specifier
    assert "0.3.0" not in deps["aware-workspace-sdk"].specifier
    assert deps["aware-protocol-cli"].extras == {"bootstrap", "specification-setup"}
    assert "0.3.5" in deps["aware-protocol-cli"].specifier
    assert "0.3.4" not in deps["aware-protocol-cli"].specifier
    assert "0.4.0" not in deps["aware-protocol-cli"].specifier
