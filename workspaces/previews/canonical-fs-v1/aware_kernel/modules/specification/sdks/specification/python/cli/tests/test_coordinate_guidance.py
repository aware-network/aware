"""Coordinate guidance over real owners, not a replacement admission path."""

import errno
import importlib.util
import json
import os
from pathlib import Path

import pytest
from aware_specification_cli import draft_commands
from aware_specification_cli.main import main


def _fixture_module(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).with_name(filename)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def draft_inputs(tmp_path, monkeypatch):
    fixture = _fixture_module("coordinate_draft_fixture", "test_draft_commands.py")
    source = fixture.inputs.__wrapped__(tmp_path, monkeypatch)
    yield next(source)
    with pytest.raises(StopIteration):
        next(source)


def _capture(args, capsys, expected):
    assert main(args) == expected
    streams = capsys.readouterr()
    assert streams.err == ""
    return json.loads(streams.out)


def _bodies(root):
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize("command", ["observe", "iteration-identity", "create-draft"])
def test_help_labels_bases_and_protocol_guard_without_supplier_io(
    command, capsys, monkeypatch
):
    def forbidden(*args, **kwargs):
        pytest.fail("help invoked an owner or opened a source")

    monkeypatch.setattr(os, "open", forbidden)
    monkeypatch.setattr(draft_commands, "_suppliers", forbidden)
    with pytest.raises(SystemExit) as result:
        main([command, "--help"])
    assert result.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split()).replace("- ", "-")
    assert "invocation directory" in help_text
    assert "canonical repository-relative" in help_text
    assert "exact Protocol manifest bytes" in help_text
    assert "not aware.spec.toml" in help_text
    if command == "create-draft":
        assert "exact Issue document bytes" in help_text
        assert "exact snapshot input bytes" in help_text
        assert "No automatic refresh or retry" in help_text
    else:
        assert "SPEC source closure" in help_text


def test_missing_relative_input_has_safe_actionable_refusal(
    draft_inputs, tmp_path, capsys, monkeypatch
):
    root, _, _, source, args = draft_inputs
    before = _bodies(root)
    descriptors = set(os.listdir("/proc/self/fd"))
    monkeypatch.chdir(root.parent)
    args[args.index("--snapshot-json") + 1] = source.name
    result = _capture(args, capsys, 2)
    assert result["error"] == "draft_input_open_failed"
    assert "draft_input_reason:not_found" in result["primary_diagnostics"]
    assert result["input_guidance"]["argument"] == "--snapshot-json"
    assert result["input_guidance"]["path_base"] == "invocation_directory_or_absolute"
    assert "absolute" in result["input_guidance"]["next_action"]
    assert result["effect"] == "none"
    assert result["cleanup_evidence"] is None
    assert str(tmp_path) not in json.dumps(result)
    assert _bodies(root) == before
    assert set(os.listdir("/proc/self/fd")) == descriptors


@pytest.mark.parametrize("absolute", [False, True])
def test_valid_input_bases_keep_real_preview_and_descriptors(
    draft_inputs, tmp_path, capsys, monkeypatch, absolute
):
    root, _, _, source, args = draft_inputs
    before = _bodies(root)
    descriptors = set(os.listdir("/proc/self/fd"))
    monkeypatch.chdir(root.parent if absolute else root)
    args[args.index("--snapshot-json") + 1] = str(source) if absolute else source.name
    result = _capture(args, capsys, 0)
    assert result["effect"] == "none"
    assert result["consumer_completion_verified"] is True
    assert "input_guidance" not in result
    assert _bodies(root) == before
    assert set(os.listdir("/proc/self/fd")) == descriptors


@pytest.mark.parametrize(
    "number,reason",
    [
        (errno.EACCES, "permission_denied"),
        (errno.ELOOP, "symlink_or_loop"),
        (None, "unavailable"),
    ],
)
def test_input_open_failure_retains_reason_not_raw_exception_path(
    draft_inputs, capsys, monkeypatch, number, reason
):
    root, _, _, source, args = draft_inputs
    before = _bodies(root)
    original = os.open

    def fail(path, *positional, **keywords):
        if Path(path) == source:
            raise OSError(number, "private exception body", "/private/not-disclosable")
        return original(path, *positional, **keywords)

    monkeypatch.setattr(os, "open", fail)
    result = _capture(args, capsys, 2)
    assert result["error"] == "draft_input_open_failed"
    assert "draft_input_reason:" + reason in result["primary_diagnostics"]
    assert "private" not in json.dumps(result)
    assert result["effect"] == "none"
    assert _bodies(root) == before


def test_real_selected_manifest_refusal_keeps_owner_diagnostics(draft_inputs, capsys):
    root, _, _, _, _ = draft_inputs
    before = _bodies(root)
    result = _capture(
        [
            "observe",
            "--repository-root",
            str(root),
            "--protocol-manifest",
            "configuration/team/aware.protocol.toml",
            "--spec-manifest",
            str(root / "customer/specs/widget/aware.spec.toml"),
        ],
        capsys,
        2,
    )
    assert result["error"] == "specification_selection_paths_invalid"
    assert result["diagnostics"][0] == result["error"]
    assert result["effect"] == "none"
    assert _bodies(root) == before


def test_wrong_manifest_guard_is_not_refreshed_or_retried(
    draft_inputs, capsys, monkeypatch
):
    from aware_specification_sdk import SpecificationSdkClient

    def forbidden(*args, **kwargs):
        pytest.fail("refused Protocol selection reached SDK draft execution")

    monkeypatch.setattr(SpecificationSdkClient, "create_draft", forbidden)
    root, _, _, _, args = draft_inputs
    before = _bodies(root)
    descriptors = set(os.listdir("/proc/self/fd"))
    args[args.index("--expected-manifest-sha256") + 1] = "sha256:" + "a" * 64
    result = _capture(args + ["--apply"], capsys, 2)
    assert result["error"] == "specification_draft_admission_failed"
    assert result["consumer_completion_verified"] is False
    assert result["effect"] == "none"
    assert _bodies(root) == before
    # The original Protocol owner supplies the cause; CLI does not reconstruct it.
    assert "specification_selection_manifest_changed" in result["primary_diagnostics"]
    assert "source_detail:SpecificationSelectionError" in result["primary_diagnostics"]
    assert set(os.listdir("/proc/self/fd")) == descriptors


@pytest.mark.parametrize("mode", ["symlink", "missing-digest", "changed-input"])
def test_existing_input_controls_keep_typed_reason_and_review_action(
    draft_inputs, capsys, mode
):
    root, _, _, source, args = draft_inputs
    if mode == "symlink":
        link = root / "input-link"
        link.symlink_to(source)
        args[args.index("--snapshot-json") + 1] = str(link)
        expected = "draft_input_open_failed"
        action = "absolute"
    elif mode == "missing-digest":
        args = args[: args.index("--expected-input-sha256")] + ["--apply"]
        expected = "draft_apply_input_digest_required"
        action = "--expected-input-sha256"
    else:
        args[args.index("--expected-input-sha256") + 1] = "sha256:" + "a" * 64
        args += ["--apply"]
        expected = "draft_input_sha256_mismatch"
        action = "do not silently replace"
    before = _bodies(root)
    descriptors = set(os.listdir("/proc/self/fd"))
    result = _capture(args, capsys, 2)
    assert result["error"] == expected
    assert result["input_guidance"]["reason"] == expected
    assert action in result["input_guidance"]["next_action"]
    assert result["effect"] == "none"
    assert result["cleanup_evidence"] is None
    assert _bodies(root) == before
    assert set(os.listdir("/proc/self/fd")) == descriptors
