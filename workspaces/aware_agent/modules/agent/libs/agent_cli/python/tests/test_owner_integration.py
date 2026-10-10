"""Actual SDK owners and synthetic prepared inputs, not customer onboarding."""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path

import pytest
from aware_agent_cli.main import main

ROOT = Path(__file__).resolve().parents[8]
SPEC = ROOT / "workspaces/aware_kernel/modules/specification/sdks/specification/python"
PROTOCOL = ROOT / "workspaces/aware_kernel/modules/protocol/libs/cli/python/tests"
ISSUE = (
    ROOT / "workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/tests"
)


def original_fixture(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


read_owner = original_fixture(
    "agent_original_read_fixture", SPEC / "fs_adapter/tests/test_protocol_selection.py"
)
draft_owner = original_fixture(
    "agent_original_draft_fixture", SPEC / "cli/tests/test_draft_commands.py"
)
setup_owner = original_fixture(
    "agent_original_setup_fixture", PROTOCOL / "test_setup_registrar.py"
)
issue_owner = original_fixture(
    "agent_original_issue_fixture", ISSUE / "test_registrars.py"
)
canonical_tree = read_owner.canonical_tree
selected = read_owner.selected
inputs = draft_owner.inputs
setup = setup_owner.setup


def fds():
    return set(os.listdir("/proc/self/fd"))


@pytest.mark.parametrize(
    "family, leaf",
    [
        ("issue", "resolve-read-projection"),
        ("protocol", "admit"),
        ("protocol", "setup-specification"),
        ("spec", "observe"),
        ("spec", "iteration-identity"),
        ("spec", "create-draft"),
    ],
)
def test_real_leaf_help_has_original_flags_without_effects(family, leaf, capsys):
    with pytest.raises(SystemExit) as caught:
        main([family, leaf, "--help"])
    assert caught.value.code == 0
    out = capsys.readouterr().out
    assert "--repository-root" in out
    assert "aware " + family in out


@pytest.mark.parametrize("leaf", ["observe", "iteration-identity"])
@pytest.mark.parametrize("stale", [False, True])
def test_actual_spec_read_and_refusal_parity(selected, leaf, stale, capsys):
    base, _ = selected
    argv = [
        leaf,
        "--repository-root",
        str(base),
        "--spec-manifest",
        read_owner.ROOT + "/aware.spec.toml",
    ]
    if leaf == "iteration-identity":
        argv += ["--iteration-ref", read_owner.ITERATION]
    if stale:
        argv += ["--expected-manifest-sha256", "sha256:" + "a" * 64]
    before = read_owner.bodies(base)
    descriptors = fds()
    from aware_specification_cli.main import main as standalone

    expected_exit = standalone(argv)
    expected = capsys.readouterr()
    assert main(["spec", *argv]) == expected_exit == (2 if stale else 0)
    assert capsys.readouterr() == expected
    assert read_owner.bodies(base) == before
    assert fds() == descriptors


@pytest.mark.parametrize("apply", [False, True])
def test_genuine_draft_preserves_publication_and_cleanup_evidence(
    inputs, apply, capsys
):
    root, _, _, _, args = inputs
    before = read_owner.bodies(root)
    descriptors = fds()
    assert main(["spec", *args, *(["--apply"] if apply else [])]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["effect"] == ("published" if apply else "none")
    assert result["consumer_completion_verified"] is True
    assert result["cleanup_evidence"]["context_state"] == "closed"
    assert read_owner.bodies(root).items() >= before.items()
    assert fds() == descriptors
    if apply:
        assert len(result["created_paths"]) == 6
    else:
        assert read_owner.bodies(root) == before


def test_real_issue_guard_refuses_before_draft_effect(inputs, capsys):
    root, _, _, _, args = inputs
    args = list(args)
    args[args.index("--expected-issue-sha256") + 1] = "sha256:" + "a" * 64
    before = read_owner.bodies(root)
    descriptors = fds()
    assert main(["spec", *args]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["effect"] == "none"
    assert result["error"]
    assert read_owner.bodies(root) == before
    assert fds() == descriptors


@pytest.mark.parametrize("apply", [False, True])
def test_real_setup_chain_and_fresh_spec_read(setup, apply, capsys):
    root, manifest, issue, request = setup
    before = read_owner.bodies(root)
    argv = setup_owner.arguments(request) + (["--apply"] if apply else [])
    assert main(["protocol", *argv]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == ("completed" if apply else "planned")
    assert result["effect"] == ("applied" if apply else "none")
    assert issue.read_bytes() == before[issue.relative_to(root).as_posix()]
    assert (root / "dirty.txt").read_bytes() == before["dirty.txt"]
    if apply:
        assert len(setup_owner.owner.observe(root, manifest).snapshot.definitions) == 1
    else:
        assert read_owner.bodies(root) == before


@pytest.mark.parametrize(
    "kind", ["owner", "issue_digest", "manifest_digest", "ancestor"]
)
def test_real_setup_refusals_through_production_mount(setup, monkeypatch, capsys, kind):
    from aware_agent_cli.main import run_family

    monkeypatch.setattr(
        setup_owner,
        "invoke",
        lambda argv, context=None: run_family("protocol", argv, context=context),
    )
    setup_owner.test_real_refusals_do_not_accept_dispatch_context_as_authority(
        setup,
        capsys,
        kind,
    )


def test_real_successful_issue_publication_and_closeout(tmp_path, capsys):
    repository, target = issue_owner._publication_repository(tmp_path)
    issue_path = "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue = repository / issue_path
    # Synthetic input preparation admits the fixture's closeout path before
    # customer command execution. This is not an Issue scope writer.
    issue.write_text(
        issue.read_text().replace(
            "- `src/example.py`",
            "- `src/example.py`\n- `" + issue_path + "`",
        )
    )
    common = [
        "--repository-root",
        str(repository),
        "--issue-ref",
        issue_owner.ISSUE_REF,
        "--actor-ref",
        "codex-example",
        "--actor-evidence-ref",
        "evidence:fixture",
    ]
    assert (
        main(
            [
                "issue",
                "commit-workspace",
                *common,
                "--expected-issue-source-sha256",
                issue_owner._digest(issue),
                "--path",
                "src/example.py",
                "--path",
                issue_path,
                "--message",
                "publish synthetic governed work",
            ]
        )
        == 0
    )
    publication = json.loads(capsys.readouterr().out)
    assert publication["reference_update"] == "cas_applied"
    assert publication["publication_receipt_ref"].startswith("git:")
    assert (
        main(
            [
                "issue",
                "close",
                *common,
                "--expected-source-sha256",
                issue_owner._digest(issue),
                "--client-intent-id",
                "agent-composition-closeout",
                "--resolution",
                "Synthetic implementation completed",
                "--verified-by",
                "test:production-mount",
                "--publication-receipt-ref",
                publication["publication_receipt_ref"],
            ]
        )
        == 0
    )
    closeout = json.loads(capsys.readouterr().out)
    assert closeout["closeout_publication_receipt_ref"].startswith("git:")
    assert "- Status: Closed" in issue.read_text()
    assert target.read_text() == "after\n"


@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize("method", ["commit_workspace", "close_issue"])
def test_real_issue_publication_late_failure_is_not_retried(
    tmp_path,
    monkeypatch,
    capsys,
    format_name,
    method,
):
    # Reuse the accepted owner's full real-publication regression and fixture.
    # Its invoker alone changes to the production family mount.
    monkeypatch.setattr(
        issue_owner, "invoke_mounted", lambda argv: main(["issue", *argv])
    )
    issue_owner.test_mounted_real_publication_then_invalid_return_preserves_effects(
        tmp_path,
        monkeypatch,
        capsys,
        format_name,
        "foreign",
        method,
    )


@pytest.mark.parametrize("mode", ["filesystem", "service_api"])
def test_protocol_admission_stream_and_authority_refusal_parity(selected, mode, capsys):
    base, _ = selected
    argv = ["admit", "--repository-root", str(base), "--authority-mode", mode]
    original = importlib.import_module("aware_protocol_cli.main")
    before = read_owner.bodies(base)
    expected_exit = original.main(argv)
    expected = capsys.readouterr()
    assert (
        main(["protocol", *argv]) == expected_exit == (0 if mode == "filesystem" else 2)
    )
    assert capsys.readouterr() == expected
    assert read_owner.bodies(base) == before
