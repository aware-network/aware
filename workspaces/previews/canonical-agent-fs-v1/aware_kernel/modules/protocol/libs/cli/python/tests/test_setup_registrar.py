"""Real mounted setup integration; no consumer launcher or installed proof."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
import types
from dataclasses import replace
from pathlib import Path

import pytest
import test_specification_setup_integration as owner
from aware_command_runtime import (
    AwareCommandRegistry,
    CommandRegistrationError,
    build_parser,
    dispatch_command,
)
from aware_protocol_sdk import PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF
from test_specification_setup_command import arguments

cli = importlib.import_module("aware_protocol_cli.main")


@pytest.fixture(scope="module")
def predecessor():
    root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / ".git").exists()
    )
    path = "workspaces/aware_kernel/modules/protocol/libs/cli/python/aware_protocol_cli/main.py"
    source = subprocess.check_output(
        ["git", "show", "3d6f9cd9b09a53fce61219022824a5715417ebfa:" + path],
        cwd=root,
        timeout=10,
    )
    assert (
        hashlib.sha256(source).hexdigest()
        == "1beb5af00bfe0391ea5403a64b515985a3f934b0e3d49af5b29219ba695517c4"
    )
    module = types.ModuleType("aware_protocol_cli.registrar_predecessor_oracle")
    module.__package__ = "aware_protocol_cli"
    # Exact hash-pinned authored diagnostic oracle, not installed product proof.
    exec(compile(source, path, "exec"), module.__dict__)  # noqa: S102
    return module


@pytest.fixture
def setup(tmp_path, monkeypatch):
    tree = owner.canonical_tree.__wrapped__(tmp_path)
    return owner.setup.__wrapped__(tree, monkeypatch)


def invoke(argv, *, context=None):
    registry = AwareCommandRegistry()
    cli.register_setup_specification_command(registry)
    parser = build_parser(registry, prog="test-composition")
    args = parser.parse_args(argv)
    args.command = "protocol-family"  # family selectors do not alter leaf dispatch
    return dispatch_command(
        registry, args=args, parser=parser, argv=argv, context=context
    )


def test_setup_registration_remains_lazy_and_refuses_collision(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("registration must not construct an owner")

    monkeypatch.setattr(cli, "FilesystemProtocolSdkProvider", forbidden)
    registry = AwareCommandRegistry()
    cli.register_setup_specification_command(registry)
    spec = registry.require("setup-specification")
    assert spec.operation_ref == PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF
    assert spec.source == "aware_protocol_cli"
    assert spec.projection_ref is None
    with pytest.raises(CommandRegistrationError, match="already registered"):
        cli.register_setup_specification_command(registry)
    assert tuple(registry) == (spec,)


@pytest.mark.parametrize("command", ["register", "help", "version"])
def test_default_source_entrance_does_not_import_optional_issue_owners(command):
    script = """
import sys
import importlib.abc
sys.path[:0] = ROOTS
class RejectOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('aware_issue'):
            raise AssertionError('optional Issue import: ' + fullname)
sys.meta_path.insert(0, RejectOptional())
from aware_command_runtime import AwareCommandRegistry, build_parser
from aware_protocol_cli.main import register_setup_specification_command, main
registry = AwareCommandRegistry()
register_setup_specification_command(registry)
assert registry.names() == ('setup-specification',)
if COMMAND == 'help':
    assert 'setup-specification' in build_parser(registry, prog='test').format_help()
elif COMMAND == 'version':
    assert main(['version']) == 0
""".replace("ROOTS", repr(sys.path)).replace("COMMAND", repr(command))
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""


def test_registrars_share_runtime_without_selecting_an_operation():
    from aware_issue_cli.main import register_issue_commands
    from aware_specification_cli.draft_commands import register_draft_commands
    from aware_specification_cli.read_commands import register_read_commands

    registry = AwareCommandRegistry()
    register_issue_commands(registry)
    cli.register_admit_command(registry)
    cli.register_setup_specification_command(registry)
    register_read_commands(registry)
    register_draft_commands(registry)
    assert len(registry) == 17
    assert (
        registry.require("commit-workspace").operation_ref
        == "issue_sdk.commit_workspace"
    )
    assert (
        registry.require("create-draft").operation_ref
        == "specification_sdk.create_draft"
    )
    assert (
        registry.require("setup-specification").operation_ref
        == PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF
    )
    # Registry construction and parser help are not a provider admission.
    assert (
        "create-draft" in build_parser(registry, prog="test-composition").format_help()
    )


@pytest.mark.parametrize("explicit", [False, True])
def test_preview_exact_stream_and_exit_parity(setup, capsys, predecessor, explicit):
    root, manifest, issue, request = setup
    original = (
        manifest.read_bytes(),
        issue.read_bytes(),
        (root / "dirty.txt").read_bytes(),
    )
    argv = arguments(request) + (["--dry-run"] if explicit else [])
    assert predecessor.main(argv) == 0
    previous = capsys.readouterr()
    assert cli.main(argv) == 0
    standalone = capsys.readouterr()
    assert invoke(argv, context={"actor_ref": "forged"}) == 0
    mounted = capsys.readouterr()
    assert mounted == standalone == previous and mounted.err == ""
    result = json.loads(mounted.out)
    assert result["status"] == "planned" and result["effect"] == "none"
    assert result["execution_ref"] is None
    assert original == (
        manifest.read_bytes(),
        issue.read_bytes(),
        (root / "dirty.txt").read_bytes(),
    )


def test_real_mounted_apply_and_fresh_spec_observation(setup, capsys):
    root, manifest, issue, request = setup
    untouched = (
        issue.read_bytes(),
        (root / "dirty.txt").read_bytes(),
        (root / "AGENTS.md").read_bytes(),
    )
    assert invoke(arguments(request) + ["--apply"]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    result = json.loads(output.out)
    assert result["status"] == "completed" and result["effect"] == "applied"
    assert result["manifest_postimage_sha256"] == owner.digest(manifest.read_bytes())
    assert result["execution_ref"] == "codex-setup-integration"
    assert result["ordered_effect_paths"] == ["contracts", "aware.protocol.toml"]
    assert len(owner.observe(root, manifest).snapshot.definitions) == 1
    assert untouched == (
        issue.read_bytes(),
        (root / "dirty.txt").read_bytes(),
        (root / "AGENTS.md").read_bytes(),
    )
    assert manifest.stat().st_mode & 0o7777 == 0o664


@pytest.mark.parametrize(
    "kind", ["owner", "issue_digest", "manifest_digest", "ancestor"]
)
def test_real_refusals_do_not_accept_dispatch_context_as_authority(setup, capsys, kind):
    root, manifest, issue, request = setup
    if kind == "owner":
        issue.write_text(
            issue.read_text().replace("codex-setup-integration", "codex-foreign")
        )
        request = replace(
            request, expected_issue_sha256=owner.digest(issue.read_bytes())
        )
    elif kind == "issue_digest":
        issue.write_text(issue.read_text() + "\nConcurrent change\n")
    elif kind == "manifest_digest":
        manifest.write_bytes(manifest.read_bytes() + b"\n# concurrent change\n")
    else:
        request = replace(
            request,
            specification_root="missing/specs",
            directory_paths=("missing/specs",),
        )
    before = manifest.read_bytes(), issue.read_bytes()
    assert (
        invoke(
            arguments(request) + ["--apply"],
            context={"actor_ref": "codex-setup-integration", "approved": True},
        )
        == 2
    )
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert output.err == "" and result["status"] == "refused"
    assert result["effect"] == "none"
    assert before == (manifest.read_bytes(), issue.read_bytes())
    assert not (root / "missing").exists()


@pytest.mark.parametrize("unknown", [False, True])
def test_real_late_failure_keeps_publication_effect_evidence(
    setup, monkeypatch, capsys, unknown
):
    _, manifest, issue, request = setup
    original = manifest.read_bytes()
    native_replace = os.replace

    def changed_after_replacement(*args, **kwargs):
        result = native_replace(*args, **kwargs)
        if unknown:
            raise OSError("replacement completion unknown")
        issue.write_text(issue.read_text() + "\nConcurrent authority change\n")
        return result

    monkeypatch.setattr(os, "replace", changed_after_replacement)
    assert invoke(arguments(request) + ["--apply"]) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "refused"
    assert output["effect"] == ("unknown" if unknown else "applied")
    assert output["effects"][-1]["path"] == "aware.protocol.toml"
    assert manifest.read_bytes() != original  # neither rollback nor retry


def test_missing_required_args_refuse_before_invocation(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("usage refusal must precede dispatch")

    monkeypatch.setattr(cli, "dispatch_command", forbidden)
    with pytest.raises(SystemExit) as error:
        cli.main(["setup-specification"])
    assert error.value.code == 2
    assert "--repository-root" in capsys.readouterr().err
