"""Command projection plus real owner integration; not installed release proof."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest
import test_specification_setup_integration as owning_fixture
from aware_protocol_cli import specification_setup as composition
from aware_protocol_cli.main import main
from aware_protocol_sdk import (
    ProtocolSpecificationSetupEffect,
    ProtocolSpecificationSetupError,
)
from test_specification_setup_integration import (
    digest,
    observe,
)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    tree = owning_fixture.canonical_tree.__wrapped__(tmp_path)
    return owning_fixture.setup.__wrapped__(tree, monkeypatch)


def arguments(request):
    values = [
        "setup-specification",
        "--repository-root",
        request.repository_root,
        "--manifest-path",
        request.manifest_path,
        "--expected-manifest-sha256",
        request.expected_manifest_sha256,
        "--issue-ref",
        request.issue_ref,
        "--expected-issue-sha256",
        request.expected_issue_sha256,
        "--specification-root",
        request.specification_root,
        "--client-intent-id",
        request.client_intent_id,
    ]
    for path in request.directory_paths:
        values += ["--directory-path", path]
    return values


@pytest.mark.parametrize("explicit", [False, True])
def test_preview_is_default_and_non_authorizing(setup, capsys, explicit):
    root, manifest, issue, request = setup
    before = manifest.read_bytes(), issue.read_bytes()
    assert main(arguments(request) + (["--dry-run"] if explicit else [])) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["status"] == "planned" and value["effect"] == "none"
    assert value["effects"] == [] and value["execution_ref"] is None
    assert value["authority_grade"] is None
    assert value["operation_ref"] == "protocol_sdk.setup_specification"
    assert value["interface"]["distribution"] == "aware-protocol-cli"
    assert (manifest.read_bytes(), issue.read_bytes()) == before
    assert (root / "dirty.txt").read_text() == "Foreign work\n"


def test_real_apply_receipt_then_fresh_spec_reader(setup, capsys):
    root, manifest, issue, request = setup
    issue_before = issue.read_bytes()
    assert main(arguments(request) + ["--apply"]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["status"] == "completed" and value["effect"] == "applied"
    assert value["manifest_postimage_sha256"] == digest(manifest.read_bytes())
    assert value["ordered_effect_paths"] == ["contracts", "aware.protocol.toml"]
    assert [e["path"] for e in value["effects"]] == value["ordered_effect_paths"]
    assert value["authority_grade"] == "filesystem_harness_observed_v1"
    assert value["execution_ref"] == "codex-setup-integration"
    assert manifest.stat().st_mode & 0o7777 == 0o664
    assert issue.read_bytes() == issue_before
    assert (root / "dirty.txt").read_text() == "Foreign work\n"
    assert len(observe(root, manifest).snapshot.definitions) == 1


@pytest.mark.parametrize("unknown", [False, True])
def test_real_post_write_refusal_is_not_success_or_rollback(
    setup, capsys, monkeypatch, unknown
):
    _, manifest, issue, request = setup
    native_replace = os.replace

    def changed_after_replacement(*args, **kwargs):
        result = native_replace(*args, **kwargs)
        if unknown:
            raise OSError("replacement completion unknown")
        issue.write_text(issue.read_text() + "\nConcurrent authority change\n")
        return result

    monkeypatch.setattr(os, "replace", changed_after_replacement)
    assert main(arguments(request) + ["--apply"]) == 2
    value = json.loads(capsys.readouterr().out)
    assert value["status"] == "refused"
    assert value["effect"] == ("unknown" if unknown else "applied")
    assert value["effects"][-1]["path"] == "aware.protocol.toml"
    assert value["effects"][-1]["state"] in {"applied", "unknown"}
    assert manifest.read_bytes() != owning_fixture._source_fixture.protocol_source()
    assert b"authority" in manifest.read_bytes()


def test_real_directory_effect_order_and_no_implicit_ancestor(setup, capsys):
    root, manifest, issue, request = setup
    issue.write_text(issue.read_text().replace("`contracts`", "`agreements`"))
    missing = replace(
        request,
        expected_issue_sha256=digest(issue.read_bytes()),
        specification_root="agreements/specs",
        directory_paths=("agreements/specs",),
    )
    original = manifest.read_bytes()
    assert main(arguments(missing) + ["--apply"]) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["effect"] == "none" and not (root / "agreements").exists()
    assert manifest.read_bytes() == original
    explicit = replace(missing, directory_paths=("agreements", "agreements/specs"))
    assert main(arguments(explicit) + ["--apply"]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["ordered_effect_paths"] == [
        "agreements",
        "agreements/specs",
        "aware.protocol.toml",
    ]
    assert [e["state"] for e in value["effects"]] == ["applied", "applied", "applied"]
    assert not (root / "agreements/specs/aware.spec.toml").exists()


def test_command_preserves_foreign_git_index_and_bootstrap(setup, capsys):
    root, _, _, request = setup
    bootstrap = (root / "AGENTS.md").read_bytes()
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "add", "dirty.txt"], cwd=root, check=True, capture_output=True
    )
    before = subprocess.check_output(["git", "ls-files", "--stage"], cwd=root)
    assert main(arguments(request) + ["--apply"]) == 0
    capsys.readouterr()
    assert subprocess.check_output(["git", "ls-files", "--stage"], cwd=root) == before
    assert (root / "AGENTS.md").read_bytes() == bootstrap


@pytest.mark.parametrize(
    "kind",
    [
        "owner",
        "lifecycle",
        "scope",
        "issue_digest",
        "manifest_digest",
        "ambiguous_execution",
    ],
)
def test_real_refusals_preserve_sources(setup, capsys, monkeypatch, kind):
    _, manifest, issue, request = setup
    if kind == "owner":
        issue.write_text(
            issue.read_text().replace("codex-setup-integration", "codex-foreign")
        )
    elif kind == "lifecycle":
        issue.write_text(issue.read_text().replace("In Progress", "Closed"))
    elif kind == "scope":
        issue.write_text(
            issue.read_text().replace("`aware.protocol.toml`", "`elsewhere.txt`")
        )
    elif kind == "issue_digest":
        issue.write_text(issue.read_text() + "\nChanged\n")
    elif kind == "manifest_digest":
        manifest.write_bytes(manifest.read_bytes() + b"\n# changed\n")
    else:
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "different-execution")
    args = arguments(request)
    if kind in {"owner", "lifecycle", "scope"}:
        args[args.index("--expected-issue-sha256") + 1] = digest(issue.read_bytes())
    before = manifest.read_bytes(), issue.read_bytes()
    assert main(args + ["--apply"]) == 2
    captured = capsys.readouterr()
    value = json.loads(captured.out)
    assert value["status"] == "refused" and value["effect"] == "none"
    assert value["code"] and captured.err == ""
    assert (manifest.read_bytes(), issue.read_bytes()) == before


@pytest.mark.parametrize(
    "flag",
    [
        "--expected-manifest-sha256",
        "--expected-issue-sha256",
        "--issue-ref",
        "--specification-root",
        "--client-intent-id",
        "--repository-root",
    ],
)
def test_missing_explicit_coordinates_refuse_before_invocation(
    setup, monkeypatch, flag
):
    _, manifest, _, request = setup
    before = manifest.read_bytes()
    args = arguments(request)
    index = args.index(flag)
    del args[index : index + 2]
    monkeypatch.setattr(
        composition.IssueGovernedSpecificationSetupProvider,
        "setup_specification",
        lambda *_: pytest.fail("must not invoke"),
    )
    with pytest.raises(SystemExit) as result:
        main(args + ["--apply"])
    assert result.value.code == 2 and manifest.read_bytes() == before


def test_apply_and_preview_flags_are_mutually_exclusive(setup):
    _, manifest, _, request = setup
    before = manifest.read_bytes()
    with pytest.raises(SystemExit) as result:
        main(arguments(request) + ["--apply", "--dry-run"])
    assert result.value.code == 2 and manifest.read_bytes() == before


@pytest.mark.parametrize(
    "flag", ["--actor-ref", "--authority-mode", "--capability-json"]
)
def test_caller_authority_or_service_override_is_not_an_entrance(setup, flag):
    _, manifest, _, request = setup
    before = manifest.read_bytes()
    with pytest.raises(SystemExit) as result:
        main(arguments(request) + [flag, "caller-selected", "--apply"])
    assert result.value.code == 2 and manifest.read_bytes() == before


@pytest.mark.parametrize(
    "digest_flag", ["--expected-manifest-sha256", "--expected-issue-sha256"]
)
def test_bare_digest_is_not_silently_converted(setup, capsys, digest_flag):
    _, manifest, _, request = setup
    before = manifest.read_bytes()
    args = arguments(request)
    index = args.index(digest_flag) + 1
    args[index] = args[index][7:]
    assert main(args + ["--apply"]) == 2
    value = json.loads(capsys.readouterr().out)
    assert value["code"] == "setup_request_invalid" and value["effect"] == "none"
    assert manifest.read_bytes() == before


def test_missing_optional_integration_refuses_without_fallback(
    setup, capsys, monkeypatch
):
    _, manifest, _, request = setup
    before = manifest.read_bytes()
    original = composition.import_module

    def unavailable(name):
        if name.startswith("aware_issue"):
            raise ImportError("selected extra is missing")
        return original(name)

    monkeypatch.setattr(composition, "import_module", unavailable)
    assert main(arguments(request) + ["--apply"]) == 2
    value = json.loads(capsys.readouterr().out)
    assert value["code"] == "setup_issue_integration_unavailable"
    assert value["effect"] == "none" and manifest.read_bytes() == before


@pytest.mark.parametrize(
    "state,unknown,scratch",
    [
        ("applied", False, ()),
        ("unknown", False, ()),
        ("applied", True, ()),
        ("applied", False, ("leftover",)),
    ],
)
def test_typed_failure_preserves_all_effect_evidence(
    setup, capsys, monkeypatch, state, unknown, scratch
):
    _, _, _, request = setup
    effect = ProtocolSpecificationSetupEffect(
        "aware.protocol.toml",
        "manifest",
        state,
        False,
        0o664,
        request.expected_manifest_sha256,
        None,
        (1, 2),
    )

    def refuse(*_):
        raise ProtocolSpecificationSetupError(
            "owner_refused_after_effect", (effect,), scratch, effect_unknown=unknown
        )

    monkeypatch.setattr(
        composition.IssueGovernedSpecificationSetupProvider,
        "setup_specification",
        refuse,
    )
    assert main(arguments(request) + ["--apply"]) == 2
    value = json.loads(capsys.readouterr().out)
    assert value["code"] == "owner_refused_after_effect"
    assert value["effects"][0]["state"] == state
    assert value["effects"][0]["mode"] == 0o664
    assert value["effects"][0]["after_identity"] == [1, 2]
    assert value["residual_scratch_paths"] == list(scratch)
    assert value["effect"] == (
        "unknown" if unknown or scratch or state == "unknown" else "applied"
    )


def test_unexpected_invocation_failure_does_not_claim_no_effects(
    setup, capsys, monkeypatch
):
    _, _, _, request = setup

    def fail(*_):
        raise OSError("injected transport failure")

    monkeypatch.setattr(
        composition.IssueGovernedSpecificationSetupProvider, "setup_specification", fail
    )
    assert main(arguments(request) + ["--apply"]) == 1
    value = json.loads(capsys.readouterr().out)
    assert value["effect"] == "unknown" and value["code"] == "setup_invocation_failed"


def test_separate_command_process_applies_over_real_owner(setup):
    root, manifest, _, request = setup
    environment = os.environ.copy()
    # Source diagnostic only. Installed candidate proof must not inherit these roots.
    environment["PYTHONPATH"] = os.pathsep.join(str(p) for p in sys.path if p)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "aware_protocol_cli.main",
            *arguments(request),
            "--apply",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["status"] == "completed" and value["effect"] == "applied"
    assert "RuntimeWarning" not in result.stderr
    assert len(observe(root, manifest).snapshot.definitions) == 1


def test_preview_receipt_does_not_authorize_stale_apply(setup, capsys):
    _, manifest, _, request = setup
    assert main(arguments(request)) == 0
    capsys.readouterr()
    manifest.write_bytes(manifest.read_bytes() + b"\n# concurrent change\n")
    before = manifest.read_bytes()
    assert main(arguments(request) + ["--apply"]) == 2
    value = json.loads(capsys.readouterr().out)
    assert value["code"] == "setup_manifest_preimage_changed"
    assert value["effect"] == "none" and manifest.read_bytes() == before
