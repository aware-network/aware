from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from aware_protocol_cli.main import main
from aware_protocol_fs_adapter import FilesystemProtocolSdkProvider
from aware_protocol_runtime import ProtocolAuthorityMode
from aware_protocol_sdk import ProtocolSdkClient, ProtocolTargetAdmissionRequest


def test_module_help_does_not_emit_runpy_warning() -> None:
    environment = os.environ.copy()
    package_root = Path(__file__).parents[1]
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(package_root), environment.get("PYTHONPATH")))
    )

    result = subprocess.run(
        [sys.executable, "-m", "aware_protocol_cli.main", "--help"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0
    assert "RuntimeWarning" not in result.stderr


def _manifest() -> str:
    return """aware = 1

[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1

[target]
kind = "repository"
authority_mode = "filesystem"

[bootstrap]
agent_contract = "AGENTS.md"

[records.goal]
profile = "aware.goal.markdown.v1"
root = "docs/goals"
role = "authority"
path_template = "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md"

[records.issue]
profile = "aware.issue.markdown.v1"
root = "docs/issues"
role = "authority"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"

[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"

[records.specification]
profile = "specification_fs_v1"
root = "docs/specs"
role = "authority"
path_template = "<spec-key>/aware.spec.toml"

[records.evidence]
profile = "aware.protocol.evidence.v1"
root = "docs/coordination/evidence"
role = "authority"
path_template = "<kind>/<stable-id>.json"
"""


def test_cli_projects_canonical_sdk_operation(
    tmp_path: Path,
    capsys,
) -> None:
    (tmp_path / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")

    assert main(["admit", "--repository-root", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["operation_ref"] == "protocol_sdk.admit_target"
    assert payload["provider_ref"] == "aware_protocol_fs_adapter.filesystem.v1"
    assert payload["admission"]["outcome"] == "canonical_v1"
    assert payload["interface"]["kind"] == "cli"


def test_cli_returns_refusal_without_fallback(
    tmp_path: Path,
    capsys,
) -> None:
    assert (
        main(
            [
                "admit",
                "--repository-root",
                str(tmp_path),
                "--authority-mode",
                "service_api",
            ]
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["admission"]["outcome"] == "authority_unavailable"
    assert payload["admission"]["source_sha256"] is None


def test_cli_version_reports_operation_and_distribution_identity(capsys) -> None:
    assert main(["version"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["operation_ref"] == "protocol_sdk.admit_target"
    assert payload["authority_modes"] == ["filesystem"]
    assert set(payload["distributions"]) == {
        "aware-protocol-cli",
        "aware-protocol-sdk",
        "aware-protocol-fs-adapter",
        "aware-protocol-runtime",
    }


def test_cli_preserves_existing_invalid_prefix_provider_outcome(
    tmp_path: Path,
    capsys,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")
    (tmp_path / "file").write_text("not a directory", encoding="utf-8")
    target_ref = f"{tmp_path}/file/../repo"

    direct = _admit_direct(target_ref)
    expected_exit = 0 if direct["outcome"] == "canonical_v1" else 2
    assert main(["admit", "--repository-root", target_ref]) == expected_exit
    cli = json.loads(capsys.readouterr().out)

    assert cli["admission"] == direct


def test_cli_preserves_missing_prefix_for_provider_refusal(
    tmp_path: Path,
    capsys,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")
    target_ref = f"{tmp_path}/missing/../repo"

    direct = _admit_direct(target_ref)
    assert main(["admit", "--repository-root", target_ref]) == 2
    cli = json.loads(capsys.readouterr().out)

    assert cli["admission"] == direct
    assert cli["admission"]["outcome"] == "source_unavailable"
    assert cli["admission"]["diagnostics"] == [
        "repository_root_unavailable:FileNotFoundError"
    ]


def test_cli_rejects_empty_explicit_target_without_using_current_directory(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    (tmp_path / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["admit", "--repository-root", ""]) == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.err)

    assert captured.out == ""
    assert payload["status"] == "error"
    assert payload["error_type"] == "ProtocolContractError"
    assert payload["message"] == "target_ref must be non-empty trimmed text"


def test_cli_resolution_failure_matches_filesystem_provider_refusal(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    target_ref = str(tmp_path)

    def deny_resolution(self: Path, *, strict: bool = False) -> Path:
        raise PermissionError("denied by parity probe")

    monkeypatch.setattr(Path, "resolve", deny_resolution)
    direct = _admit_direct(target_ref)
    assert main(["admit", "--repository-root", target_ref]) == 2
    cli = json.loads(capsys.readouterr().out)

    assert cli["admission"] == direct
    assert cli["admission"]["outcome"] == "source_unavailable"
    assert cli["admission"]["diagnostics"] == [
        "repository_root_unavailable:PermissionError"
    ]


def test_cli_service_selection_precedes_filesystem_resolution(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    def deny_resolution(self: Path, *, strict: bool = False) -> Path:
        raise AssertionError("service selection must not resolve a filesystem path")

    monkeypatch.setattr(Path, "resolve", deny_resolution)

    assert (
        main(
            [
                "admit",
                "--repository-root",
                str(tmp_path),
                "--authority-mode",
                "service_api",
            ]
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["admission"]["outcome"] == "authority_unavailable"
    assert payload["admission"]["source_sha256"] is None
    assert payload["admission"]["diagnostics"] == [
        "filesystem_provider_requires_filesystem_authority"
    ]


def _admit_direct(target_ref: str) -> dict[str, object]:
    result = ProtocolSdkClient(provider=FilesystemProtocolSdkProvider()).admit_target(
        ProtocolTargetAdmissionRequest(
            authority_mode=ProtocolAuthorityMode.FILESYSTEM,
            target_ref=target_ref,
            source_ref="aware.protocol.toml",
        )
    )
    return result.admission.to_wire()
