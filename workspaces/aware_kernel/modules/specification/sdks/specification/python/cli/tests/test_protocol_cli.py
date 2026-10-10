"""Consumer command uses actual Protocol -> SPEC composition, not raw roots."""

import importlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest
from aware_specification_cli.main import main

_spec = importlib.util.spec_from_file_location(
    "spec_cli_protocol_fixture",
    Path(__file__).parents[2] / "fs_adapter/tests/test_protocol_selection.py",
)
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
canonical_tree = _fixtures.canonical_tree
selected = _fixtures.selected


def arguments(base):
    return [
        "--repository-root",
        str(base),
        "--spec-manifest",
        _fixtures.ROOT + "/aware.spec.toml",
    ]


@pytest.mark.parametrize("command", ["observe", "iteration-identity"])
def test_real_consumer_reads_and_cleans_owned_selection(selected, capsys, command):
    base, _ = selected
    before = _fixtures.bodies(base)
    fds = set(os.listdir("/proc/self/fd"))
    args = [command, *arguments(base)]
    if command == "iteration-identity":
        args += ["--iteration-ref", _fixtures.ITERATION]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["work_authority"] is result["phase_acceptance"] is False
    assert result["retained_capability_exported"] is False
    assert result["snapshot"]["definitions"][0]["key"] == "example.spec"
    if command == "iteration-identity":
        assert result["selected_iteration_ref"] == _fixtures.ITERATION
    assert _fixtures.bodies(base) == before
    assert set(os.listdir("/proc/self/fd")) == fds


@pytest.mark.parametrize("command", ["observe", "iteration-identity"])
@pytest.mark.parametrize("manifest_form", ["default", "relative", "absolute"])
def test_relative_repository_manifest_forms_match_absolute_observation(
    selected, capsys, monkeypatch, command, manifest_form
):
    base, _ = selected
    before = _fixtures.bodies(base)
    fds = set(os.listdir("/proc/self/fd"))
    suffix = (
        ["--iteration-ref", _fixtures.ITERATION]
        if command == "iteration-identity"
        else []
    )
    assert main([command, *arguments(base), *suffix]) == 0
    expected = json.loads(capsys.readouterr().out)

    monkeypatch.chdir(base.parent)
    args = [command, *arguments(Path(base.name)), *suffix]
    if manifest_form != "default":
        manifest = (
            str(base / "aware.protocol.toml")
            if manifest_form == "absolute"
            else "aware.protocol.toml"
        )
        args += ["--protocol-manifest", manifest]
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out) == expected
    assert _fixtures.bodies(base) == before
    assert set(os.listdir("/proc/self/fd")) == fds


def test_expected_manifest_drift_is_real_protocol_refusal(selected, capsys):
    base, _ = selected
    assert (
        main(
            [
                "observe",
                *arguments(base),
                "--expected-manifest-sha256",
                "sha256:" + "a" * 64,
            ]
        )
        == 2
    )
    result = json.loads(capsys.readouterr().out)
    assert result == {
        "error": "specification_selection_manifest_changed",
        "effect": "none",
        "diagnostics": ["specification_selection_manifest_changed"],
    }


@pytest.mark.parametrize("role", ["unavailable", "projection"])
def test_unsupported_spec_authority_has_no_raw_fallback(selected, capsys, role):
    base, _ = selected
    (base / "aware.protocol.toml").write_bytes(_fixtures.protocol_bytes(role))
    assert main(["observe", *arguments(base)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["effect"] == "none"
    assert "specification_selection" in result["error"]


def test_protocol_guard_runs_after_iteration_identity_resolution(
    selected, capsys, monkeypatch
):
    base, _ = selected
    module = importlib.import_module("aware_specification_cli.read_commands")
    original = module.resolve_iteration_identity

    def resolve(*args):
        result = original(*args)
        with (base / "aware.protocol.toml").open("ab") as stream:
            stream.write(b"# changed while resolving identity\n")
        return result

    monkeypatch.setattr(module, "resolve_iteration_identity", resolve)
    assert (
        main(
            [
                "iteration-identity",
                *arguments(base),
                "--iteration-ref",
                _fixtures.ITERATION,
            ]
        )
        == 2
    )
    result = json.loads(capsys.readouterr().out)
    assert result["error"] == "specification_selection_manifest_changed"
    assert result["effect"] == "none"


@pytest.mark.parametrize(
    "args",
    [
        ["create-draft"],
        ["observe", "--source-base", "/raw", "--root", "specs/example"],
    ],
)
def test_consumer_cli_does_not_advertise_writer_or_raw_source(args):
    with pytest.raises(SystemExit) as caught:
        main(args)
    assert caught.value.code == 2


def test_read_preserves_real_unborn_git_index_and_foreign_staging(selected, capsys):
    base, _ = selected
    subprocess.run(
        ["git", "init", "-b", "main", str(base)], check=True, capture_output=True
    )
    subprocess.run(["git", "-C", str(base), "add", "--", "foreign.txt"], check=True)
    before = _fixtures.bodies(base)
    status = subprocess.check_output(["git", "-C", str(base), "status", "--porcelain"])
    assert main(["observe", *arguments(base)]) == 0
    assert json.loads(capsys.readouterr().out)["work_authority"] is False
    assert (
        subprocess.check_output(["git", "-C", str(base), "status", "--porcelain"])
        == status
    )
    assert _fixtures.bodies(base) == before


@pytest.mark.parametrize("stale", [False, True])
def test_cleanup_fault_has_one_typed_result_and_preserves_primary_refusal(
    selected, capsys, monkeypatch, stale
):
    base, _ = selected
    provider_type = _fixtures.SpecificationFsSdkProvider
    original_close = provider_type.close
    before = set(os.listdir("/proc/self/fd"))

    def close(provider):
        original_close(provider)
        raise OSError("injected after actual resource closure")

    monkeypatch.setattr(provider_type, "close", close)
    args = ["observe", *arguments(base)]
    if stale:
        args += ["--expected-source-digest", "sha256:" + "b" * 64]
    assert main(args) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["effect"] == "none"
    assert output["error"] == ("source_changed" if stale else "source_cleanup_failed")
    assert output["cleanup_diagnostics"] == ["source_provider_cleanup_failed:OSError"]
    assert "snapshot" not in output
    assert set(os.listdir("/proc/self/fd")) == before
