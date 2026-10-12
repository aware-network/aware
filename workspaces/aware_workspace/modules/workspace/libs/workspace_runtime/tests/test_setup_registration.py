"""Source qualification of the setup supplier through the original registry."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from aware_command_runtime import (
    AwareCommandRegistry,
    CommandRegistrationError,
    build_parser,
    dispatch_command,
    run_cli,
)
from aware_workspace_command.architecture_setup_command import main
from aware_workspace_command.setup_registration import register_workspace_setup_commands


def registry():
    result = AwareCommandRegistry()
    register_workspace_setup_commands(result)
    return result


def files(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def invoke(root, capsys, *arguments, context=None):
    code = run_cli(
        registry(),
        argv=["setup", *arguments, "--repository-root", str(root), "--json"],
        prog="workspace-supplier-proof",
        context=context,
    )
    return code, json.loads(capsys.readouterr().out)


def apply(root, capsys, *arguments):
    before = files(root)
    code, preview = invoke(root, capsys, *arguments)
    assert code == 0 and files(root) == before
    scope = [
        arg
        for path in preview["proposed_write_paths"]
        for arg in ("--allowed-path", path)
    ]
    code, result = invoke(
        root,
        capsys,
        *arguments,
        "--apply",
        "--expected-plan-sha256",
        preview["preview"]["plan_sha256"],
        *scope,
    )
    assert code == 0 and result["status"] in ("succeeded", "unchanged")
    return result


def test_registrar_adds_only_setup_and_preserves_registry_duplicate_rules():
    commands = registry()
    assert commands.names() == ("setup",)
    with pytest.raises(CommandRegistrationError):
        register_workspace_setup_commands(commands)


def test_setup_help_refuses_legacy_imports_in_fresh_source_process():
    script = """
import sys, importlib.abc
sys.path[:0] = ROOTS
class RejectLegacy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'aware_workspace' or fullname.startswith('aware_workspace.') or fullname in (
            'aware_workspace_command.workspace_command',
            'aware_workspace_command.materialize_command',
            'aware_workspace_command.checkout_command',
        ) or 'orm_models' in fullname or 'service_sdk_adapter' in fullname:
            raise AssertionError('legacy import: ' + fullname)
sys.meta_path.insert(0, RejectLegacy())
from aware_command_runtime import AwareCommandRegistry, run_cli
from aware_workspace_command.setup_registration import register_workspace_setup_commands
r = AwareCommandRegistry()
register_workspace_setup_commands(r)
assert r.names() == ('setup',)
try:
    run_cli(r, argv=['setup', '--help'], prog='workspace-supplier-proof')
except SystemExit as error:
    assert error.code == 0
else:
    raise AssertionError('help did not stop')
""".replace("ROOTS", repr(sys.path))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "repository,workspace,module,python-package,align,locks" in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize(
    "arguments",
    [
        ("checkout",),
        ("materialize",),
        ("service-host",),
        ("publication",),
        ("setup", "service-host"),
        ("setup", "aware-package"),
        ("setup", "materialize"),
    ],
)
def test_unsupported_commands_refuse_before_provider_selection(arguments, monkeypatch):
    module = importlib.import_module(
        "aware_workspace_command.architecture_setup_command"
    )

    def forbidden(**kwargs):
        pytest.fail("syntax refusal selected a provider")

    monkeypatch.setattr(module.WorkspaceSetupClient, "filesystem", forbidden)
    with pytest.raises(SystemExit) as error:
        run_cli(registry(), argv=arguments, prog="workspace-supplier-proof")
    assert error.value.code == 2


@pytest.mark.parametrize("returncode", [0, 1, 2, 3])
def test_original_namespace_and_return_code_pass_unchanged(returncode, monkeypatch):
    module = importlib.import_module(
        "aware_workspace_command.architecture_setup_command"
    )
    received = []

    def handle(args):
        received.append(args)
        return returncode

    monkeypatch.setattr(module, "handle_workspace_setup_command", handle)
    commands = registry()
    parser = build_parser(commands, prog="workspace-supplier-proof")
    argv = (
        "setup",
        "align",
        "--repository-root",
        "/original/root",
        "--workspace",
        "app",
    )
    args = parser.parse_args(argv)
    assert (
        dispatch_command(
            commands,
            args=args,
            parser=parser,
            argv=argv,
            context={"not_authority": object()},
        )
        == returncode
    )
    assert received == [args] and received[0] is args
    assert (
        args.setup_repository_root == Path("/original/root") and args.workspace == "app"
    )


def test_standalone_and_host_preview_have_identical_original_evidence(tmp_path, capsys):
    arguments = ["repository", "--name", "example", "--license-expression", "MIT"]
    code, mounted = invoke(tmp_path, capsys, *arguments)
    assert code == 0 and files(tmp_path) == {}
    assert (
        main(["setup", *arguments, "--repository-root", str(tmp_path), "--json"]) == 0
    )
    standalone = json.loads(capsys.readouterr().out)
    assert mounted == standalone and files(tmp_path) == {}


@pytest.mark.parametrize("wrong_digest", [False, True])
def test_host_context_does_not_replace_exact_plan_or_write_scope(
    tmp_path, capsys, wrong_digest
):
    arguments = ["repository", "--name", "example", "--license-expression", "MIT"]
    _, preview = invoke(tmp_path, capsys, *arguments)
    digest = "sha256:" + "0" * 64 if wrong_digest else preview["preview"]["plan_sha256"]
    allowed = "aware.repo.toml" if wrong_digest else "other.toml"
    code, refused = invoke(
        tmp_path,
        capsys,
        *arguments,
        "--apply",
        "--expected-plan-sha256",
        digest,
        "--allowed-path",
        allowed,
        context={"approved": True, "issue_admitted": True},
    )
    assert code == 2 and refused["status"] == "refused" and files(tmp_path) == {}
    assert refused["error"] == (
        "setup_plan_changed" if wrong_digest else "setup_write_scope_mismatch"
    )


@pytest.mark.parametrize("separate_workspace", [False, True])
def test_real_setup_and_selected_locks_through_original_registry(
    tmp_path, capsys, separate_workspace
):
    uv = shutil.which("uv")
    assert uv is not None, "the qualified UV 0.11.19 tool is required"
    apply(
        tmp_path,
        capsys,
        "repository",
        "--name",
        "example",
        "--license-expression",
        "MIT",
    )
    apply(
        tmp_path,
        capsys,
        "python-package",
        "--owner",
        "repository",
        "--name",
        "base",
        "--distribution",
        "example-base",
        "--import-root",
        "example_base",
    )
    apply(tmp_path, capsys, "workspace", "--name", "app")
    apply(tmp_path, capsys, "module", "--workspace", "app", "--name", "greeting")
    apply(
        tmp_path,
        capsys,
        "python-package",
        "--workspace",
        "app",
        "--module",
        "greeting",
        "--name",
        "client",
        "--distribution",
        "example-client",
        "--import-root",
        "example_client",
        "--dependency",
        "example-base>=0.1,<0.2",
    )
    selectors = [("--workspace", "app"), ()] if separate_workspace else [()]
    for selector in selectors:
        apply(tmp_path, capsys, "align", *selector)
    for selector in selectors:
        code, updated = invoke(
            tmp_path, capsys, "locks", "update", *selector, "--uv-executable", uv
        )
        assert code == 0
        before = files(tmp_path)
        code, checked = invoke(
            tmp_path, capsys, "locks", "check", *selector, "--uv-executable", uv
        )
        assert code == 0 and files(tmp_path) == before
        update, check = updated["receipts"][0], checked["receipts"][0]
        expected_root = tmp_path / "workspaces/app" if selector else tmp_path
        assert (
            update["resolution_root"] == check["resolution_root"] == str(expected_root)
        )
        assert (
            update["after_lock_sha256"]
            == check["before_lock_sha256"]
            == check["after_lock_sha256"]
        )
        assert update["status"] == check["status"] == "completed"
    assert len(list(tmp_path.rglob("uv.lock"))) == len(selectors)
    assert not (tmp_path / ".git").exists()


def test_shared_parser_configuration_matches_standalone_operations():
    parser = build_parser(registry(), prog="workspace-supplier-proof")
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    assert tuple(subparsers.choices) == ("setup",)
