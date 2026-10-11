"""Real read-only owner composition followed by separately requested effects."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest
from aware_agent_cli import draft_preparation as preparation
from aware_agent_cli.main import main
from aware_issue_fs_adapter import FilesystemIssueOperationProvider

ROOT = Path(__file__).resolve().parents[8]
SPEC = ROOT / "workspaces/aware_kernel/modules/specification/sdks/specification/python"
loader = importlib.util.spec_from_file_location(
    "agent_guard_preparation_fixture", SPEC / "cli/tests/test_draft_commands.py"
)
fixture = importlib.util.module_from_spec(loader)
loader.loader.exec_module(fixture)
inputs = fixture.inputs


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def bodies(root):
    return {
        str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mode)
        for path in root.rglob("*")
        if path.is_file()
    }


def fds():
    return set(os.listdir("/proc/self/fd"))


def arguments(original, *, format="json"):
    result = ["spec", "prepare-draft", "--format", format]
    for flag in (
        "--repository-root",
        "--protocol-manifest",
        "--spec-manifest",
        "--snapshot-json",
        "--issue-ref",
        "--author-ref",
        "--authoring-intent-ref",
        "--client-intent-id",
    ):
        result.extend((flag, original[original.index(flag) + 1]))
    return result


def prepare(original, capsys):
    assert main(arguments(original)) == 0
    return json.loads(capsys.readouterr().out)


def test_original_guard_sources_and_no_write_admission(inputs, capsys, monkeypatch):
    from aware_file_system import retained_package as physical
    from aware_protocol_fs_adapter import specification_draft_target as target

    root, manifest, issue, source, original = inputs
    before = bodies(root)
    descriptors = fds()

    def forbidden(*args, **kwargs):
        pytest.fail(
            "read-only preparation invoked retained publication or write custody"
        )

    monkeypatch.setattr(physical, "retain_package_publication", forbidden)
    monkeypatch.setattr(target, "admit_specification_draft_target", forbidden)
    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "retain_draft_inputs", forbidden
    )
    result = prepare(original, capsys)
    assert result["effect"] == "none"
    assert result["write_admission_issued"] is result["apply_invoked"] is False
    assert result["observations_atomic"] is False
    assert result["guards"] == {
        "issue_source_bytes": digest(issue.read_bytes()),
        "protocol_manifest_bytes": digest(manifest.read_bytes()),
        "snapshot_input_bytes": digest(source.read_bytes()),
    }
    assert len(result["members"]) == 6
    assert bodies(root) == before
    assert fds() == descriptors


@pytest.mark.parametrize("apply", [False, True])
def test_reviewed_original_command_runs_without_digest_copy(inputs, capsys, apply):
    root, _, issue, source, original = inputs
    before = bodies(root)
    request = prepare(original, capsys)
    argv = request["apply_argv" if apply else "preview_argv"]
    assert argv[:3] == ["aware", "spec", "create-draft"]
    assert ("--apply" in argv) is apply
    assert main(argv[1:]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["effect"] == ("published" if apply else "none")
    assert result["consumer_completion_verified"] is True
    assert result["input_sha256"] == request["guards"]["snapshot_input_bytes"]
    assert issue.read_bytes() == before[str(issue.relative_to(root))][0]
    assert source.read_bytes() == before[str(source.relative_to(root))][0]
    assert bodies(root).items() >= before.items()


@pytest.mark.parametrize("changed", ["issue", "manifest", "input"])
def test_stale_review_refuses_without_repreparation(inputs, capsys, changed):
    root, manifest, issue, source, original = inputs
    reviewed = prepare(original, capsys)
    selected = {"issue": issue, "manifest": manifest, "input": source}[changed]
    selected.write_bytes(selected.read_bytes() + b"\n")
    before = bodies(root)
    descriptors = fds()
    assert main(reviewed["apply_argv"][1:]) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["error"]
    assert not (root / "customer/specs/widget").exists()
    assert reviewed["guards"] == {
        "issue_source_bytes": original[original.index("--expected-issue-sha256") + 1],
        "protocol_manifest_bytes": original[
            original.index("--expected-manifest-sha256") + 1
        ],
        "snapshot_input_bytes": original[original.index("--expected-input-sha256") + 1],
    }
    assert bodies(root) == before
    assert fds() == descriptors


def test_relative_input_is_bound_to_observed_absolute_coordinate(
    inputs, monkeypatch, capsys
):
    root, _, _, source, original = inputs
    original = list(original)
    original[original.index("--snapshot-json") + 1] = source.name
    monkeypatch.chdir(root)
    result = prepare(original, capsys)
    assert result["preview_argv"][
        result["preview_argv"].index("--snapshot-json") + 1
    ] == str(source)
    monkeypatch.chdir("/")
    assert main(result["apply_argv"][1:]) == 0
    assert json.loads(capsys.readouterr().out)["consumer_completion_verified"] is True


def test_summary_is_readable_and_json_remains_available(inputs, capsys):
    _, _, _, _, original = inputs
    assert main(arguments(original, format="summary")) == 0
    summary = capsys.readouterr().out
    assert "no write admission" in summary
    assert "Explicit apply only after review:" in summary
    assert "no atomic snapshot" in summary
    assert (
        len(summary.encode()) < 8192
    )  # Ordinary fixture measurement, not a truncation rule.


def test_missing_input_supplier_refuses_before_any_owner_observation(
    inputs, monkeypatch, capsys
):
    root, _, _, _, original = inputs
    before = bodies(root)
    importer = preparation.importlib.import_module

    def unavailable(name):
        if name == "aware_specification_sdk":
            raise ImportError("input port unavailable")
        return importer(name)

    monkeypatch.setattr(preparation.importlib, "import_module", unavailable)
    assert main(arguments(original)) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["owner_observations"] == {}
    assert output["effect"] == "none"
    assert "apply_argv" not in output
    assert bodies(root) == before


def test_unknown_input_cleanup_is_preserved_and_yields_no_apply_command(
    inputs, monkeypatch, capsys
):
    from aware_specification_fs_sdk_adapter import input_observation as owner

    root, _, _, source, original = inputs
    close = owner.os.close
    before = bodies(root)
    descriptors = fds()

    def interrupted(fd):
        close(fd)
        raise KeyboardInterrupt("close observation unavailable")

    monkeypatch.setattr(owner.os, "close", interrupted)
    assert main(arguments(original)) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["effect"] == "unknown"
    error = result["owner_error"]["value"]
    assert error["cleanup"] == "unknown"
    assert error["observed_body_hex"] == source.read_bytes().hex()
    assert "apply_argv" not in result
    assert bodies(root) == before
    assert fds() == descriptors


@pytest.mark.parametrize("kind", ["issue", "input"])
def test_missing_selected_source_has_no_apply_command(inputs, capsys, kind):
    root, _, _, _, original = inputs
    original = list(original)
    flag = "--issue-ref" if kind == "issue" else "--snapshot-json"
    original[original.index(flag) + 1] = (
        "fb/2026-10-06/absent" if kind == "issue" else str(root / "absent.json")
    )
    before = bodies(root)
    assert main(arguments(original)) == 2
    result = json.loads(capsys.readouterr().out)
    assert "apply_argv" not in result
    assert bodies(root) == before


def test_prepare_rejects_apply_flag_before_effects(inputs, capsys):
    root, _, _, _, original = inputs
    before = bodies(root)
    with pytest.raises(SystemExit) as caught:
        main([*arguments(original), "--apply"])
    assert caught.value.code == 2
    capsys.readouterr()
    assert bodies(root) == before


def test_observed_wrong_owner_does_not_grant_write_authority(inputs, capsys):
    root, _, issue, _, original = inputs
    issue.write_text(
        issue.read_text().replace(
            "codex-spec-governed-real-source-proof", "codex-other-execution"
        )
    )
    reviewed = prepare(original, capsys)
    assert reviewed["write_admission_issued"] is False
    before = bodies(root)
    assert main(reviewed["apply_argv"][1:]) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["error"]
    assert not (root / "customer/specs/widget").exists()
    assert bodies(root) == before


def test_protocol_refusal_retains_original_diagnostics_and_stops(inputs, capsys):
    root, manifest, _, _, original = inputs
    manifest.write_text("broken [TOML")
    before = bodies(root)
    assert main(arguments(original)) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["error"] == "protocol_observation_not_canonical"
    assert refused["owner_observations"]["protocol"]["admission"]["diagnostics"]
    assert "issue" not in refused["owner_observations"]
    assert "apply_argv" not in refused
    assert bodies(root) == before
