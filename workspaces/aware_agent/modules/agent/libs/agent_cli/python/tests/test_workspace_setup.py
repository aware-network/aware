"""Setup-only source mounting and local owner parity, not A1/A2 authority."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest
from aware_command_runtime import (
    AwareCommandRegistry,
    CommandRegistrationError,
    build_parser,
    dispatch_command,
)
from aware_workspace_command import architecture_setup_command as owner
from packaging.requirements import Requirement

client = importlib.import_module("aware_agent_cli.main")


def files(root):
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mode)
        for path in root.rglob("*")
        if path.is_file()
    }


def invoke(root, capsys, *arguments):
    code = client.main(
        ["workspace", "setup", *arguments, "--repository-root", str(root), "--json"]
    )
    streams = capsys.readouterr()
    assert streams.err == ""
    return code, json.loads(streams.out)


def apply_local(root, capsys, *arguments):
    """Exercise the original local SDK; this is not an Issue admission helper."""
    before = files(root)
    code, preview = invoke(root, capsys, *arguments)
    assert code == 0 and preview["status"] == "planned"
    assert files(root) == before
    scopes = [
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
        *scopes,
    )
    assert code == 0 and result["status"] in ("succeeded", "unchanged")
    return result


def test_only_original_setup_port_mounts_and_duplicates_are_not_overwritten():
    registry = AwareCommandRegistry()
    client.register_family_commands(registry, "workspace")
    assert registry.names() == ("setup", "review")
    original = registry.require("setup")
    with pytest.raises(CommandRegistrationError):
        client.register_family_commands(registry, "workspace")
    assert registry.require("setup") is original


def test_setup_help_does_not_import_other_families_or_broad_workspace_in_fresh_process():
    script = """
import sys, importlib.abc
sys.path[:0] = ROOTS
class RejectOtherRails(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_issue', 'aware_protocol', 'aware_specification',
                                'aware_agent_sdk', 'aware_local_service', 'aware_ontology')) or fullname in (
            'aware_workspace',
            'aware_workspace_command.workspace_command',
            'aware_workspace_command.materialize_command',
            'aware_workspace_command.checkout_command',
        ) or fullname.startswith('aware_workspace.') or 'orm_models' in fullname:
            raise AssertionError('unsupported import: ' + fullname)
sys.meta_path.insert(0, RejectOtherRails())
import aware_workspace_command, aware_workspace_command.pack
def forbidden_discovery():
    raise AssertionError('setup help invoked generic command-pack discovery')
aware_workspace_command.get_command_specs = forbidden_discovery
aware_workspace_command.pack.get_command_specs = forbidden_discovery
from aware_agent_cli.main import main
try:
    main(['workspace', 'setup', '--help'])
except SystemExit as error:
    assert error.code == 0
else:
    raise AssertionError('help did not stop')
""".replace("ROOTS", repr(sys.path))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "repository,workspace,module,python-package,align,locks" in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize(
    "arguments",
    [
        ["checkout"],
        ["materialize"],
        ["service-host"],
        ["publication"],
        ["setup", "aware-package"],
        ["setup", "materialize"],
        ["setup", "service-host"],
    ],
)
def test_unsupported_surface_refuses_before_provider_selection(arguments, monkeypatch):
    def forbidden(**kwargs):
        pytest.fail("unsupported command selected a provider")

    monkeypatch.setattr(owner.WorkspaceSetupClient, "filesystem", forbidden)
    with pytest.raises(SystemExit) as caught:
        client.main(["workspace", *arguments])
    assert caught.value.code == 2


@pytest.mark.parametrize("code", [0, 1, 2, 3])
def test_exact_parsed_namespace_argv_and_original_return_code(code, monkeypatch):
    seen = []

    def handle(args):
        seen.append(args)
        return code

    monkeypatch.setattr(owner, "handle_workspace_setup_command", handle)
    registry = AwareCommandRegistry()
    client.register_family_commands(registry, "workspace")
    parser = build_parser(registry, prog="aware workspace")
    argv = (
        "setup",
        "align",
        "--repository-root",
        "/exact/repository",
        "--workspace",
        "app",
    )
    args = parser.parse_args(argv)
    assert (
        dispatch_command(
            registry,
            args=args,
            parser=parser,
            argv=argv,
            context={"not_authority": object()},
        )
        == code
    )
    assert seen == [args] and seen[0] is args
    assert args.setup_repository_root == Path("/exact/repository")
    assert args.workspace == "app" and args._aware_command_name == "setup"


def test_mounted_and_standalone_readonly_receipts_match(tmp_path, capsys):
    (tmp_path / "foreign.txt").write_text("untouched\n")
    before = files(tmp_path)
    arguments = ["repository", "--name", "example", "--license-expression", "MIT"]
    code, mounted = invoke(tmp_path, capsys, *arguments)
    assert code == 0 and files(tmp_path) == before
    assert (
        owner.main(["setup", *arguments, "--repository-root", str(tmp_path), "--json"])
        == 0
    )
    standalone = json.loads(capsys.readouterr().out)
    assert mounted == standalone
    assert mounted["contract"] == "aware.workspace.architecture-setup-command.v1"
    assert files(tmp_path) == before


@pytest.mark.parametrize("wrong", ["digest", "missing", "extra", "duplicate"])
def test_transport_context_cannot_replace_plan_currentness_or_exact_paths(
    tmp_path, capsys, wrong
):
    (tmp_path / "foreign.txt").write_text("untouched\n")
    before = files(tmp_path)
    arguments = ["repository", "--name", "example", "--license-expression", "MIT"]
    _, preview = invoke(tmp_path, capsys, *arguments)
    digest = (
        "sha256:" + "0" * 64 if wrong == "digest" else preview["preview"]["plan_sha256"]
    )
    paths = {
        "digest": ["aware.repo.toml"],
        "missing": [],
        "extra": ["aware.repo.toml", "foreign.txt"],
        "duplicate": ["aware.repo.toml", "aware.repo.toml"],
    }[wrong]
    argv = [
        "setup",
        *arguments,
        "--repository-root",
        str(tmp_path),
        "--json",
        "--apply",
        "--expected-plan-sha256",
        digest,
    ]
    argv += [arg for path in paths for arg in ("--allowed-path", path)]
    assert (
        client.run_family(
            "workspace", argv, context={"approved": True, "issue_admitted": True}
        )
        == 2
    )
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "refused"
    assert result["error"] == (
        "setup_plan_changed" if wrong == "digest" else "setup_write_scope_mismatch"
    )
    assert files(tmp_path) == before


@pytest.mark.parametrize("owner_kind", ["repository", "workspace", "module"])
def test_real_local_creation_preserves_original_owner_registration_and_foreign_work(
    tmp_path, capsys, owner_kind
):
    (tmp_path / "foreign.txt").write_text("untouched\n")
    foreign = files(tmp_path)["foreign.txt"]
    apply_local(
        tmp_path,
        capsys,
        "repository",
        "--name",
        "example",
        "--license-expression",
        "MIT",
    )
    selectors = ["--owner", owner_kind]
    if owner_kind != "repository":
        apply_local(tmp_path, capsys, "workspace", "--name", "app")
        selectors.extend(("--workspace", "app"))
    if owner_kind == "module":
        apply_local(
            tmp_path, capsys, "module", "--workspace", "app", "--name", "greeting"
        )
        selectors.extend(("--module", "greeting"))
    result = apply_local(
        tmp_path,
        capsys,
        "python-package",
        *selectors,
        "--name",
        "base",
        "--distribution",
        "example-base",
        "--import-root",
        "example_base",
    )
    paths = result["receipt"]["written_paths"]
    parent = {
        "repository": "aware.repo.toml",
        "workspace": "workspaces/app/aware.workspace.toml",
        "module": "workspaces/app/modules/greeting/aware.module.toml",
    }[owner_kind]
    assert parent in paths and len(paths) == 3
    assert all((tmp_path / path).is_file() for path in paths)
    assert files(tmp_path)["foreign.txt"] == foreign
    # Source-local capability, not a hidden bootstrap or genuine A1/A2 proof.
    assert not any(
        (tmp_path / path).exists()
        for path in (
            ".git",
            "aware.protocol.toml",
            "AGENTS.md",
            "docs/issues",
            "uv.lock",
        )
    )


def test_stale_parent_registration_refuses_before_child_creation(tmp_path, capsys):
    apply_local(
        tmp_path,
        capsys,
        "repository",
        "--name",
        "example",
        "--license-expression",
        "MIT",
    )
    _, preview = invoke(tmp_path, capsys, "workspace", "--name", "app")
    manifest = tmp_path / "aware.repo.toml"
    manifest.write_bytes(manifest.read_bytes() + b"\n# intervening work\n")
    before = files(tmp_path)
    flags = [
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
        *flags,
    )
    assert code == 2 and result["error"] == "setup_plan_changed"
    assert files(tmp_path) == before and not (tmp_path / "workspaces").exists()


def test_real_apply_then_failed_observation_preserves_original_effect_receipt(
    tmp_path, capsys, monkeypatch
):
    original = owner.WorkspaceSetupClient.apply
    seen = []

    def failed_return(self, request, **kwargs):
        receipt = original(self, request, **kwargs)
        seen.append(receipt)
        raise owner.ArchitectureSetupError(
            "injected_post_effect_observation_failure",
            receipt=replace(
                receipt, status="uncertain", diagnostics=("injected_return_failure",)
            ),
        )

    monkeypatch.setattr(owner.WorkspaceSetupClient, "apply", failed_return)
    arguments = ["repository", "--name", "example", "--license-expression", "MIT"]
    _, preview = invoke(tmp_path, capsys, *arguments)
    code, result = invoke(
        tmp_path,
        capsys,
        *arguments,
        "--apply",
        "--expected-plan-sha256",
        preview["preview"]["plan_sha256"],
        "--allowed-path",
        "aware.repo.toml",
    )
    assert code == 3 and result["status"] == "uncertain" and len(seen) == 1
    assert result["receipt"]["written_paths"] == ["aware.repo.toml"]
    assert result["receipt"]["diagnostics"] == ["injected_return_failure"]
    assert (tmp_path / "aware.repo.toml").is_file()


def test_source_metadata_requires_actual_setup_ports_without_service_extra():
    metadata = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text()
    )["project"]
    requirements = {r.name: r for r in map(Requirement, metadata["dependencies"])}
    assert metadata["version"] == "0.2.0a11"
    sdk = requirements["aware-workspace-sdk"]
    runtime = requirements["aware-workspace-runtime"]
    assert sdk.extras == {"preparation", "setup", "setup_admission", "setup_review"}
    assert "0.2.11" in sdk.specifier and "0.2.10" not in sdk.specifier
    assert "0.2.16" in runtime.specifier and "0.2.15" not in runtime.specifier
    assert "0.3.0" not in sdk.specifier and "0.3.0" not in runtime.specifier
    assert runtime.extras == {"setup_admission", "setup_review"}
    issue = requirements["aware-issue-sdk"]
    assert issue.extras == {"workspace_setup_admission"}
    assert "0.10.6" in issue.specifier and "0.10.5" not in issue.specifier
    assert "0.11.0" not in issue.specifier
