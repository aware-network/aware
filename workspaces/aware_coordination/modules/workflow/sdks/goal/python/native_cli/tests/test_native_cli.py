from __future__ import annotations

import json
import os
import subprocess
from importlib import import_module
from pathlib import Path

import pytest
from test_native_provider import (
    CUSTOMER_EXTERNAL_PATH,
    CUSTOMER_PATH,
    EXTERNAL_GOAL,
    GOAL,
    _git,
    _native_capability,
    _publish_external_source,
    _source,
)


@pytest.mark.parametrize("v3", [False, True])
def test_native_cli_phase_direction_and_currentness_are_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], v3: bool,
) -> None:
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH, v3=v3)
    _native_capability(root, monkeypatch)
    cli = import_module("aware_goal_native_cli.main")
    common = [
        "--repository-root", str(root),
        "--manifest-path", str(root / "aware.protocol.toml"),
        "--goal-path", CUSTOMER_PATH,
    ]
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain=v1"))
    assert cli.main([
        "observe_phase_direction", *common,
        "--goal-tag", GOAL, "--lane-key", "runtime", "--phase-key", "first",
    ]) == 0
    receipt = json.loads(capsys.readouterr().out)
    receipt_file = tmp_path / "receipt.json"
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
    assert cli.main([
        "verify_phase_direction_currentness", *common,
        "--receipt-file", str(receipt_file),
    ]) == 0
    currentness = json.loads(capsys.readouterr().out)
    assert currentness["status"] == "current"
    assert currentness["replay_disposition"] == "exact"
    assert (_git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain=v1")) == before


def test_native_cli_phase_receipt_rejects_duplicate_json_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH)
    _native_capability(root, monkeypatch)
    receipt_file = tmp_path / "duplicate.json"
    receipt_file.write_text('{"schema_id":"one","schema_id":"two"}', encoding="utf-8")
    cli = import_module("aware_goal_native_cli.main")
    assert cli.main([
        "verify_phase_direction_currentness",
        "--repository-root", str(root),
        "--manifest-path", str(root / "aware.protocol.toml"),
        "--goal-path", CUSTOMER_PATH,
        "--receipt-file", str(receipt_file),
    ]) == 2
    assert "duplicate_phase_direction_json_key" in capsys.readouterr().err


def _command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, v3: bool = False):
    root, request = _source(tmp_path, goal_path=CUSTOMER_PATH, v3=v3)
    _native_capability(root, monkeypatch)
    request_file = tmp_path / "request.json"
    request_file.write_text(json.dumps(request.to_wire()), encoding="utf-8")
    cli = import_module("aware_goal_native_cli.main")
    args = [
        "--repository-root", str(root),
        "--manifest-path", str(root / "aware.protocol.toml"),
        "--request-file", str(request_file),
    ]
    return root, request_file, cli, args


@pytest.mark.parametrize("v3", [False, True])
def test_native_cli_observes_customer_goal_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], v3: bool,
) -> None:
    root, _, cli, args = _command(tmp_path, monkeypatch, v3=v3)
    before_head = _git(root, "rev-parse", "HEAD")
    before_status = _git(root, "status", "--porcelain=v1")

    assert cli.main(args) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "observed"
    assert result["eligibility"] == "eligible"
    assert result["event_effect"] == result["dispatch_effect"] == "none"
    assert _git(root, "rev-parse", "HEAD") == before_head
    assert _git(root, "status", "--porcelain=v1") == before_status

@pytest.mark.parametrize("v3", [False, True])
def test_native_cli_discovers_request_then_observes_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], v3: bool,
) -> None:
    root, request_file, cli, args = _command(tmp_path, monkeypatch, v3=v3)
    before_head = _git(root, "rev-parse", "HEAD")
    before_status = _git(root, "status", "--porcelain=v1")
    discovery_args = [
        *args[:4], "--discover-goal-path", CUSTOMER_PATH,
        "--lane-key", "runtime", "--phase-key", "first",
    ]

    assert cli.main(discovery_args) == 0
    discovered = json.loads(capsys.readouterr().out)
    assert discovered["schema_id"] == "aware.goal.phase-operation-request.v1"
    assert discovered["source_locator_ref"] == "repository-path:" + CUSTOMER_PATH
    request_file.write_text(json.dumps(discovered), encoding="utf-8")
    assert cli.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "observed"
    assert result["event_effect"] == result["dispatch_effect"] == "none"
    assert _git(root, "rev-parse", "HEAD") == before_head
    assert _git(root, "status", "--porcelain=v1") == before_status

    goal = root / CUSTOMER_PATH
    goal.write_bytes(goal.read_bytes().replace(b"Eligibility proof", b"Changed proof"))
    _git(root, "add", "--", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Advance customer Goal after discovery")
    stale_head = _git(root, "rev-parse", "HEAD")
    stale_status = _git(root, "status", "--porcelain=v1")
    assert cli.main(args) == 2
    assert json.loads(capsys.readouterr().out)["reasons"] == ["goal_source_stale"]
    assert _git(root, "rev-parse", "HEAD") == stale_head
    assert _git(root, "status", "--porcelain=v1") == stale_status


def test_native_cli_discovery_rejects_missing_coordinates_and_hints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, _, cli, args = _command(tmp_path, monkeypatch)
    discovery = [*args[:4], "--discover-goal-path", CUSTOMER_PATH]
    assert cli.main(discovery) == 2
    assert "discovery_requires_lane_and_phase_keys" in capsys.readouterr().err
    discovery.extend(("--lane-key", "runtime", "--phase-key", "first"))
    discovery.extend(("--prerequisite-goal", f"{EXTERNAL_GOAL}={CUSTOMER_EXTERNAL_PATH}"))
    assert cli.main(discovery) == 2
    assert "discovery_does_not_use_prerequisite_hints" in capsys.readouterr().err


def test_native_cli_rejects_legacy_manifest_without_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _, cli, args = _command(tmp_path, monkeypatch)
    manifest = root / "aware.protocol.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "aware.collaboration.fs_v2", "aware.collaboration.fs_v1"
        ),
        encoding="utf-8",
    )

    assert cli.main(args) == 2
    assert "observed" not in capsys.readouterr().out
    discovery = [
        *args[:4], "--discover-goal-path", CUSTOMER_PATH,
        "--lane-key", "runtime", "--phase-key", "first",
    ]
    assert cli.main(discovery) == 2
    assert not capsys.readouterr().out


def test_native_cli_rejects_malformed_request_before_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, request_file, cli, args = _command(tmp_path, monkeypatch)
    request_file.write_text('{"source_locator_ref":"repository-path:other"}', encoding="utf-8")

    assert cli.main(args) == 2
    assert "eligibility request fields differ" in capsys.readouterr().err


def test_native_cli_rejects_duplicate_prerequisite_hints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, _, cli, args = _command(tmp_path, monkeypatch)
    args.extend(("--prerequisite-goal", "goal/2026-09-26/other=customer/objectives/other.md"))
    args.extend(("--prerequisite-goal", "goal/2026-09-26/other=customer/objectives/other.md"))

    assert cli.main(args) == 2
    assert "invalid_or_duplicate_prerequisite_goal" in capsys.readouterr().err


def test_native_cli_qualifies_cross_goal_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH,
        dependency=True, external_dependency=True,
    )
    _publish_external_source(root, goal_path=CUSTOMER_EXTERNAL_PATH)
    _native_capability(root, monkeypatch)
    request_file = tmp_path / "request.json"
    request_file.write_text(json.dumps(request.to_wire()), encoding="utf-8")
    cli = import_module("aware_goal_native_cli.main")
    args = [
        "--repository-root", str(root),
        "--manifest-path", str(root / "aware.protocol.toml"),
        "--request-file", str(request_file),
        "--prerequisite-goal", f"{EXTERNAL_GOAL}={CUSTOMER_EXTERNAL_PATH}",
    ]

    discovery_args = [
        *args[:4], "--discover-goal-path", CUSTOMER_PATH,
        "--lane-key", "runtime", "--phase-key", "first",
    ]
    assert cli.main(discovery_args) == 0
    request_file.write_text(capsys.readouterr().out, encoding="utf-8")
    assert cli.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "observed"
    assert result["dependency_gate"]["stale"] == ["first-requires-later"]


def test_native_cli_refuses_stale_source_without_compatibility_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _, cli, args = _command(tmp_path, monkeypatch)
    target = root / CUSTOMER_PATH
    target.write_bytes(target.read_bytes().replace(b"Eligibility proof", b"Changed proof"))
    _git(root, "add", "--", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Advance customer Goal")

    assert cli.main(args) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "refused"
    assert result["reasons"] == ["goal_source_stale"]


@pytest.mark.parametrize("v3", [False, True])
def test_noneditable_installed_cli_outside_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, v3: bool,
) -> None:
    installed = os.environ.get("AWARE_GOAL_NATIVE_INSTALLED_CLI")
    if installed is None:
        pytest.skip("set AWARE_GOAL_NATIVE_INSTALLED_CLI for installed proof")
    root, _, _, args = _command(tmp_path, monkeypatch, v3=v3)
    before_head = _git(root, "rev-parse", "HEAD")
    before_status = _git(root, "status", "--porcelain=v1")
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        (installed, *args), cwd=tmp_path, env=environment,
        capture_output=True, text=True, check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "observed"
    assert result["event_effect"] == result["dispatch_effect"] == "none"
    assert _git(root, "rev-parse", "HEAD") == before_head
    assert _git(root, "status", "--porcelain=v1") == before_status

    manifest = root / "aware.protocol.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "aware.collaboration.fs_v2", "aware.collaboration.fs_v1"
        ), encoding="utf-8",
    )
    refused = subprocess.run(
        (installed, *args), cwd=tmp_path, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert refused.returncode == 2
    assert not refused.stdout
    assert json.loads(refused.stderr)["status"] == "error"
    assert _git(root, "rev-parse", "HEAD") == before_head
    assert _git(root, "status", "--porcelain=v1") == before_status

    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "aware.collaboration.fs_v1", "aware.collaboration.fs_v2"
        ), encoding="utf-8",
    )
    goal = root / CUSTOMER_PATH
    goal.write_bytes(goal.read_bytes().replace(b"Eligibility proof", b"Changed proof"))
    _git(root, "add", "--", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Advance customer Goal")
    stale_head = _git(root, "rev-parse", "HEAD")
    stale_status = _git(root, "status", "--porcelain=v1")
    stale = subprocess.run(
        (installed, *args), cwd=tmp_path, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert stale.returncode == 2
    assert json.loads(stale.stdout)["reasons"] == ["goal_source_stale"]
    assert _git(root, "rev-parse", "HEAD") == stale_head
    assert _git(root, "status", "--porcelain=v1") == stale_status


@pytest.mark.parametrize("v3", [False, True])
def test_installed_discovery_then_observation_outside_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, v3: bool,
) -> None:
    installed = os.environ.get("AWARE_GOAL_NATIVE_INSTALLED_CLI")
    if installed is None:
        pytest.skip("set AWARE_GOAL_NATIVE_INSTALLED_CLI for installed proof")
    root, request_file, _, args = _command(tmp_path, monkeypatch, v3=v3)
    before_head = _git(root, "rev-parse", "HEAD")
    before_status = _git(root, "status", "--porcelain=v1")
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    discovery = subprocess.run(
        (
            installed, *args[:4], "--discover-goal-path", CUSTOMER_PATH,
            "--lane-key", "runtime", "--phase-key", "first",
        ), cwd=tmp_path, env=environment, capture_output=True, text=True, check=False,
    )
    assert discovery.returncode == 0, discovery.stderr
    discovered = json.loads(discovery.stdout)
    assert discovered["schema_id"] == "aware.goal.phase-operation-request.v1"
    request_file.write_text(discovery.stdout, encoding="utf-8")
    observation = subprocess.run(
        (installed, *args), cwd=tmp_path, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert observation.returncode == 0, observation.stderr
    assert json.loads(observation.stdout)["status"] == "observed"
    assert _git(root, "rev-parse", "HEAD") == before_head
    assert _git(root, "status", "--porcelain=v1") == before_status
