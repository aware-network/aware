"""CLI proofs through the original SDK and physical adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from aware_workspace_command.architecture_setup_command import main
from aware_workspace_command.workspace_command import (
    handle_workspace_command,
    register_workspace_parser,
)


def files(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def invoke(root, capsys, operation, *options):
    prefix = ["setup", operation]
    if operation == "locks":
        prefix.append(options[0])
        options = options[1:]
    code = main([*prefix, "--repository-root", str(root), "--json", *options])
    return code, json.loads(capsys.readouterr().out)


def apply(root, capsys, operation, *options):
    code, preview = invoke(root, capsys, operation, *options)
    assert code == 0 and preview["status"] == "planned", preview
    scopes = [
        arg
        for path in preview["proposed_write_paths"]
        for arg in ("--allowed-path", path)
    ]
    code, result = invoke(
        root,
        capsys,
        operation,
        *options,
        "--apply",
        "--expected-plan-sha256",
        preview["preview"]["plan_sha256"],
        *scopes,
    )
    assert code == 0, result
    return result


def repository(root, capsys):
    return apply(
        root, capsys, "repository", "--name", "example", "--license-expression", "MIT"
    )


def member(root, capsys):
    repository(root, capsys)
    apply(root, capsys, "workspace", "--name", "app")
    apply(root, capsys, "module", "--workspace", "app", "--name", "base")
    apply(
        root,
        capsys,
        "python-package",
        "--workspace",
        "app",
        "--module",
        "base",
        "--name",
        "base",
        "--distribution",
        "example-base",
        "--import-root",
        "example_base",
    )


@pytest.mark.parametrize("owner", ["repository", "workspace", "module"])
def test_cli_selects_original_package_owner_and_exact_scope(tmp_path, capsys, owner):
    repository(tmp_path, capsys)
    selectors = ["--owner", owner]
    prefix = ""
    if owner != "repository":
        apply(tmp_path, capsys, "workspace", "--name", "app")
        selectors += ["--workspace", "app"]
        prefix = "workspaces/app/"
    if owner == "module":
        apply(tmp_path, capsys, "module", "--workspace", "app", "--name", "base")
        selectors += ["--module", "base"]
        prefix += "modules/base/"
    options = [
        *selectors,
        "--name",
        "support",
        "--distribution",
        "example-support",
        "--import-root",
        "example_support",
    ]
    before = files(tmp_path)
    code, plan = invoke(tmp_path, capsys, "python-package", *options)
    assert code == 0 and files(tmp_path) == before
    owner_manifest = {
        "repository": "aware.repo.toml",
        "workspace": "aware.workspace.toml",
        "module": "aware.module.toml",
    }[owner]
    assert set(plan["proposed_write_paths"]) == {
        prefix + owner_manifest,
        prefix + "libs/support/python/pyproject.toml",
        prefix + "libs/support/python/src/example_support/__init__.py",
    }
    assert apply(tmp_path, capsys, "python-package", *options)["status"] == "succeeded"
    assert apply(tmp_path, capsys, "python-package", *options)["status"] == "unchanged"


@pytest.mark.parametrize(
    "selectors",
    [
        [],
        ["--owner", "repository", "--workspace", "app"],
        ["--owner", "workspace"],
        ["--owner", "workspace", "--workspace", "app", "--module", "base"],
    ],
)
def test_cli_owner_selection_refuses_incomplete_or_conflicting_dimensions(
    tmp_path, capsys, selectors
):
    repository(tmp_path, capsys)
    before = files(tmp_path)
    code, result = invoke(
        tmp_path,
        capsys,
        "python-package",
        *selectors,
        "--name",
        "support",
        "--distribution",
        "support",
        "--import-root",
        "support",
    )
    assert code == 2 and result["error"] == "package_owner_selection_conflicts"
    assert files(tmp_path) == before


def test_cli_support_stale_plan_refuses_registration_drift(tmp_path, capsys):
    repository(tmp_path, capsys)
    options = [
        "--owner",
        "repository",
        "--name",
        "support",
        "--distribution",
        "support",
        "--import-root",
        "support",
    ]
    _, preview = invoke(tmp_path, capsys, "python-package", *options)
    apply(tmp_path, capsys, "workspace", "--name", "app")
    before = files(tmp_path)
    scopes = [
        arg
        for path in preview["proposed_write_paths"]
        for arg in ("--allowed-path", path)
    ]
    code, result = invoke(
        tmp_path,
        capsys,
        "python-package",
        *options,
        "--apply",
        "--expected-plan-sha256",
        preview["preview"]["plan_sha256"],
        *scopes,
    )
    assert code == 2 and result["error"] == "setup_plan_changed"
    assert files(tmp_path) == before


def test_workspace_mount_selects_setup_without_legacy_parser(tmp_path, capsys):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    register_workspace_parser(commands, args_list=("workspace", "setup"))
    workspace = commands.choices["workspace"]
    mounted = next(
        action
        for action in workspace._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    assert tuple(mounted.choices) == ("setup",)
    args = parser.parse_args(
        [
            "workspace",
            "setup",
            "repository",
            "--repository-root",
            str(tmp_path),
            "--name",
            "example",
            "--license-expression",
            "MIT",
            "--json",
        ]
    )
    assert handle_workspace_command(args, parser, object()) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "planned"
    assert files(tmp_path) == {}


def test_four_layer_creation_and_empty_module_through_cli(tmp_path, capsys):
    member(tmp_path, capsys)
    from aware_code_module_manifest_contract_runtime import parse_module_manifest

    mod = apply(tmp_path, capsys, "module", "--workspace", "app", "--name", "empty")
    assert mod["receipt"]["status"] == "succeeded"
    path = tmp_path / "workspaces/app/modules/empty/aware.module.toml"
    assert parse_module_manifest(path.read_bytes()).packages == ()
    assert (
        tmp_path
        / "workspaces/app/modules/base/libs/base/python/src/example_base/__init__.py"
    ).is_file()
    assert not (tmp_path / ".git").exists()
    assert not (tmp_path / "uv.lock").exists()
    apply(tmp_path, capsys, "align")
    assert (
        "example-base = { workspace = true }"
        in (tmp_path / "pyproject.toml").read_text()
    )


@pytest.mark.parametrize(
    "scope", [[], ["unrelated"], ["aware.repo.toml", "aware.repo.toml"]]
)
def test_apply_scope_mismatch_refuses_before_writes(tmp_path, capsys, scope):
    code, preview = invoke(
        tmp_path,
        capsys,
        "repository",
        "--name",
        "example",
        "--license-expression",
        "MIT",
    )
    assert code == 0
    flags = [arg for path in scope for arg in ("--allowed-path", path)]
    code, result = invoke(
        tmp_path,
        capsys,
        "repository",
        "--name",
        "example",
        "--license-expression",
        "MIT",
        "--apply",
        "--expected-plan-sha256",
        preview["preview"]["plan_sha256"],
        *flags,
    )
    assert code == 2 and result["error"] == "setup_write_scope_mismatch"
    assert files(tmp_path) == {}


def test_stale_preview_refuses_before_child_creation(tmp_path, capsys):
    repository(tmp_path, capsys)
    _, preview = invoke(tmp_path, capsys, "workspace", "--name", "app")
    path = tmp_path / "aware.repo.toml"
    path.write_bytes(path.read_bytes() + b"\n# concurrent edit\n")
    before = files(tmp_path)
    scopes = [
        arg
        for path in preview["proposed_write_paths"]
        for arg in ("--allowed-path", path)
    ]
    code, result = invoke(
        tmp_path,
        capsys,
        "workspace",
        "--name",
        "app",
        "--apply",
        "--expected-plan-sha256",
        preview["preview"]["plan_sha256"],
        *scopes,
    )
    assert code == 2 and result["error"] == "setup_plan_changed"
    assert files(tmp_path) == before


def test_repeat_uses_empty_write_scope_and_preserves_authored_source(tmp_path, capsys):
    member(tmp_path, capsys)
    source = (
        tmp_path
        / "workspaces/app/modules/base/libs/base/python/src/example_base/__init__.py"
    )
    source.write_text("answer = 42\n")
    before = files(tmp_path)
    result = apply(
        tmp_path,
        capsys,
        "python-package",
        "--workspace",
        "app",
        "--module",
        "base",
        "--name",
        "base",
        "--distribution",
        "example-base",
        "--import-root",
        "example_base",
    )
    assert result["receipt"]["status"] == "unchanged"
    assert files(tmp_path) == before


@pytest.mark.parametrize(
    "options, error",
    [
        (["--apply"], "apply_requires_expected_plan_sha256"),
        (
            ["--preview", "--allowed-path", "aware.repo.toml"],
            "apply_options_require_apply",
        ),
    ],
)
def test_explicit_apply_admission_required(tmp_path, capsys, options, error):
    code, result = invoke(
        tmp_path,
        capsys,
        "repository",
        "--name",
        "example",
        "--license-expression",
        "MIT",
        *options,
    )
    assert code == 2 and result["error"] == error
    assert files(tmp_path) == {}


def test_alignment_preserves_normalized_policy_refusal(tmp_path, capsys):
    member(tmp_path, capsys)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.sources]\nExample_Base = { path = "vendor/original", editable = false }\n'
    )
    before = files(tmp_path)
    code, result = invoke(
        tmp_path, capsys, "align", "--apply", "--expected-plan-sha256", "stale"
    )
    assert code == 2 and result["error"] == "explicit_source_policy_requires_review"
    assert files(tmp_path) == before


@pytest.mark.parametrize("operation", ["check", "update"])
def test_lock_timeout_keeps_sdk_receipt_and_refuses_retry(
    tmp_path, capsys, monkeypatch, operation
):
    member(tmp_path, capsys)
    apply(tmp_path, capsys, "align")
    lock = tmp_path / "uv.lock"
    lock.write_bytes(b"before\n")
    calls = []

    def run(command, **kwargs):
        calls.append(tuple(command))
        if command[1] == "--version":
            return subprocess.CompletedProcess(command, 0, "uv 0.11.19\n", "")
        lock.write_bytes(b"changed\n")
        raise subprocess.TimeoutExpired(
            command, 120, output=b"partial output", stderr=b"partial error"
        )

    monkeypatch.setattr(subprocess, "run", run)
    code = main(
        [
            "setup",
            "locks",
            operation,
            "--repository-root",
            str(tmp_path),
            "--uv-executable",
            shutil.which("uv"),
            "--json",
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert code == 3 and result["status"] == "uncertain"
    receipt = result["receipt"]
    assert receipt["command"] == list(calls[1]) and len(calls) == 2
    assert (
        receipt["stdout"] == "partial output" and receipt["stderr"] == "partial error"
    )
    assert (
        receipt["before_lock_sha256"]
        == "sha256:" + hashlib.sha256(b"before\n").hexdigest()
    )
    assert (
        receipt["after_lock_sha256"]
        == "sha256:" + hashlib.sha256(b"changed\n").hexdigest()
    )
    assert receipt["status"] == "uncertain" and receipt["returncode"] is None


def test_completed_uv_failure_remains_visible(tmp_path, capsys, monkeypatch):
    member(tmp_path, capsys)
    apply(tmp_path, capsys, "align")

    def run(command, **kwargs):
        if command[1] == "--version":
            return subprocess.CompletedProcess(command, 0, "uv 0.11.19\n", "")
        return subprocess.CompletedProcess(command, 7, "partial", "resolution refused")

    monkeypatch.setattr(subprocess, "run", run)
    code = main(
        [
            "setup",
            "locks",
            "update",
            "--repository-root",
            str(tmp_path),
            "--uv-executable",
            shutil.which("uv"),
            "--json",
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert code == 1 and result["status"] == "failed"
    assert result["receipts"][0]["returncode"] == 7
    assert result["receipts"][0]["stderr"] == "resolution refused"


def test_setup_help_does_not_import_physical_or_semantic_providers():
    script = """
import sys
from aware_workspace_command.architecture_setup_command import main
try:
    main(['setup', '--help'])
except SystemExit as error:
    assert error.code == 0
assert not any(n == 'aware_workspace' or n.startswith('aware_workspace.') or
               n.startswith('aware_workspace_fs_adapter') or 'orm_models' in n
               for n in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_environment_cli_mount_help():
    root = Path(__file__).resolve().parents[7]
    result = subprocess.run(
        [
            str(root / ".venv/bin/aware-cli"),
            "workspace",
            "setup",
            "python-package",
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (
        "--distribution" in result.stdout and "--expected-plan-sha256" in result.stdout
    )


@pytest.mark.parametrize("symlink", [False, True])
def test_environment_cli_preserves_original_provider_root(tmp_path, symlink):
    root = Path(__file__).resolve().parents[7]
    target = tmp_path / "prepared"
    target.mkdir()
    selected = target
    if symlink:
        selected = tmp_path / "alias"
        selected.symlink_to(target, target_is_directory=True)
    result = subprocess.run(
        [
            str(root / ".venv/bin/aware-cli"),
            "workspace",
            "setup",
            "repository",
            "--repository-root",
            str(selected),
            "--name",
            "example",
            "--license-expression",
            "MIT",
            "--preview",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == (2 if symlink else 0), result.stderr
    payload = json.loads(result.stdout)
    assert payload["resolution_root"] == str(selected)
    assert payload["status"] == ("refused" if symlink else "planned")
    if symlink:
        assert payload["error"] == "repository_root_symlink_denied"
    assert files(target) == {}


def test_cli_registered_workspace_alignment_and_selected_lock(tmp_path, capsys):
    member(tmp_path, capsys)
    aligned = apply(tmp_path, capsys, "align", "--workspace", "app")
    assert all(
        path.startswith("workspaces/app/")
        for path in aligned["receipt"]["written_paths"]
    )
    apply(tmp_path, capsys, "align")
    for mode in ("update", "check"):
        code, outcome = invoke(
            tmp_path,
            capsys,
            "locks",
            mode,
            "--workspace",
            "app",
            "--uv-executable",
            shutil.which("uv"),
        )
        assert code == 0, outcome
        expected = str(tmp_path / "workspaces/app")
        assert outcome["resolution_root"] == expected
        assert outcome["receipts"][0]["resolution_root"] == expected
        assert outcome["receipts"][0]["command"][6] == expected
    assert not (tmp_path / "uv.lock").exists()
    assert (tmp_path / "workspaces/app/uv.lock").exists()


def test_cli_workspace_alignment_stale_plan_and_scope(tmp_path, capsys):
    member(tmp_path, capsys)
    code, preview = invoke(tmp_path, capsys, "align", "--workspace", "app")
    assert code == 0
    (tmp_path / "workspaces/app/pyproject.toml").write_text("# new\n")
    before = files(tmp_path)
    scope = [
        arg
        for path in preview["proposed_write_paths"]
        for arg in ("--allowed-path", path)
    ]
    code, result = invoke(
        tmp_path,
        capsys,
        "align",
        "--workspace",
        "app",
        "--apply",
        "--expected-plan-sha256",
        preview["preview"]["plan_sha256"],
        *scope,
    )
    assert code == 2 and result["error"] == "setup_plan_changed"
    assert files(tmp_path) == before


@pytest.mark.parametrize("operation", ["align", "locks"])
def test_cli_unknown_workspace_does_not_dispatch(tmp_path, capsys, operation):
    repository(tmp_path, capsys)
    before = files(tmp_path)
    extra = (
        ("update", "--uv-executable", shutil.which("uv"))
        if operation == "locks"
        else ()
    )
    code, result = invoke(tmp_path, capsys, operation, *extra, "--workspace", "absent")
    assert code == 2 and result["error"] == "workspace_not_registered"
    assert files(tmp_path) == before
