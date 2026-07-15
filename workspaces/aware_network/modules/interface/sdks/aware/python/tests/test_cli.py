from __future__ import annotations

from contextlib import ExitStack
import json
import os
import sys
from pathlib import Path

import aware_sdk
import pytest
from aware_sdk import cli
from aware_sdk import validate as validate_module
from aware_sdk.validate import ValidationRunResult
from aware_sdk.workspace_lifecycle import (
    WorkspaceLifecycleProofError,
    WorkspaceLifecycleProofResult,
    run_workspace_lifecycle_proof,
)


def test_version_string_present() -> None:
    assert isinstance(aware_sdk.__version__, str)
    assert aware_sdk.__version__


def test_run_workspace_lifecycle_proof_emits_summary_and_receipt(
    tmp_path: Path,
) -> None:
    aware_cli = _write_fake_workspace_lifecycle_aware_cli(
        tmp_path / "bin" / "aware-cli"
    )

    result = run_workspace_lifecycle_proof(
        aware_cli_executable=aware_cli,
        validation_root=tmp_path / "validation",
    )

    assert result.receipt_path.is_file()
    assert result.summary["initial_status"]["summary_kind"] == "bootstrap_required"
    assert result.summary["bootstrap"]["summary_kind"] == "ready_for_module_creation"
    assert (
        result.summary["post_bootstrap_status"]["summary_kind"]
        == "workspace_ready_no_history"
    )
    assert (
        result.summary["empty_workspace_compile"]["diagnostic_code"]
        == "workspace.compile.workspace_manifest_empty"
    )
    assert result.summary["module_create"]["status"] == "ok"
    assert result.summary["module_compile"]["scope_key"] == "sample"

    receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "verified"
    assert receipt["summary"]["command_order"] == [
        "initial_status",
        "bootstrap",
        "post_bootstrap_status",
        "empty_workspace_compile",
        "module_create",
        "module_compile",
    ]


def test_run_workspace_lifecycle_proof_fails_when_initial_status_omits_readiness(
    tmp_path: Path,
) -> None:
    aware_cli = _write_fake_workspace_lifecycle_aware_cli(
        tmp_path / "bin" / "aware-cli",
        missing_readiness=True,
    )
    receipt_path = tmp_path / "validation" / "receipts" / "workspace-lifecycle.json"

    with pytest.raises(WorkspaceLifecycleProofError, match="initial_status.readiness"):
        _ = run_workspace_lifecycle_proof(
            aware_cli_executable=aware_cli,
            validation_root=tmp_path / "validation",
            receipt_path=receipt_path,
        )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "contract_failed"


def test_run_workspace_lifecycle_proof_rejects_module_create_outside_fresh_root(
    tmp_path: Path,
) -> None:
    aware_cli = _write_fake_workspace_lifecycle_aware_cli(
        tmp_path / "bin" / "aware-cli",
        module_root_outside_workspace=True,
    )
    receipt_path = tmp_path / "validation" / "receipts" / "workspace-lifecycle.json"

    with pytest.raises(
        WorkspaceLifecycleProofError, match="fresh workspace modules directory"
    ):
        _ = run_workspace_lifecycle_proof(
            aware_cli_executable=aware_cli,
            validation_root=tmp_path / "validation",
            receipt_path=receipt_path,
        )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "contract_failed"


def test_run_workspace_lifecycle_proof_rejects_missing_module_create_root(
    tmp_path: Path,
) -> None:
    aware_cli = _write_fake_workspace_lifecycle_aware_cli(
        tmp_path / "bin" / "aware-cli",
        skip_module_root_directory=True,
    )
    receipt_path = tmp_path / "validation" / "receipts" / "workspace-lifecycle.json"

    with pytest.raises(
        WorkspaceLifecycleProofError, match="reported a missing module root"
    ):
        _ = run_workspace_lifecycle_proof(
            aware_cli_executable=aware_cli,
            validation_root=tmp_path / "validation",
            receipt_path=receipt_path,
        )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "contract_failed"


def test_cli_info_outputs_json(capsys) -> None:
    exit_code = cli.info()
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    for key in ("aware_sdk", "aware_api", "aware_hub_service_api", "public_contract"):
        assert key in payload
    assert payload["public_contract"]["product_boundary"] == "interface-renderer"
    assert payload["public_contract"]["commands"] == [
        "app",
        "status",
        "render",
        "panes",
        "invoke",
        "act",
        "follow",
        "capabilities",
        "profile",
    ]
    assert payload["public_contract"]["planned_commands"] == ["local"]
    assert (
        payload["public_contract"]["canonical_rail"]
        == "aware-sdk -> interface-sdk -> Interface -> Experience -> API/Services"
    )
    assert payload["public_contract"]["transitional_diagnostics"] == {
        "commands": ["hub", "identity", "sdk", "actions", "run"],
        "status": "hidden-bootstrap-diagnostic-only",
    }
    assert payload["public_contract"]["operation_catalog_contract"] == {
        "status": "preview",
        "command": "sdk",
        "catalog_contract": "aware.sdk_operation_catalog.v0",
        "entry_point_group": "aware.sdk_operation_catalogs",
        "invariant": (
            "SDK CLI operations must be declared by explicit SDK "
            "operation catalog providers, not reflected from methods."
        ),
    }
    assert payload["public_contract"]["validation_command"] == "validate"
    assert payload["public_contract"]["install_commands"] == [
        "install",
        "activate",
        "rollback",
    ]
    assert payload["public_contract"]["launchers"] == ["aware", "aware-sdk"]
    assert payload["public_contract"]["legacy_bundle_launchers"] == [
        "aware-cli",
        "aware-sdk",
    ]
    assert payload["public_contract"]["capabilities"] == [
        "committed-app-session-entry",
        "interface-status-rendering",
        "interface-surface-rendering",
        "interface-pane-listing",
        "interface-pane-capability-invocation",
        "interface-pane-action-invocation",
        "interface-capability-rendering",
        "interface-profile-selection",
    ]
    assert payload["public_contract"]["legacy_kernel_proof"]["commands"] == [
        "compile",
        "workspace",
    ]
    assert payload["public_contract"]["legacy_kernel_proof"]["capabilities"] == [
        "compile",
        "runtime",
        "python",
        "sql",
        "sqlite",
    ]
    assert payload["public_contract"]["bundle_profile"].endswith(
        "graph_os_linux_cli_public.toml"
    )
    assert payload["public_contract"]["proof_profile"].endswith(
        "graph_os_home_story_compile.toml"
    )
    assert payload["public_contract"]["default_proof_rail"] == "compile-first"
    proof_rails = {
        entry["id"]: entry for entry in payload["public_contract"]["proof_rails"]
    }
    assert proof_rails["compile-first"]["status"] == "default"
    assert proof_rails["workspace-first"]["status"] == "preview"
    assert proof_rails["workspace-first"]["profile"].endswith(
        "graph_os_home_story_workspace.toml"
    )
    assert payload["public_contract"]["proof_repo_slug"] == "home-workspace"


def test_cli_validate_runs_public_proof_and_emits_validation_pack(
    tmp_path: Path, capsys
) -> None:
    workspace_root = tmp_path / "repo"
    profile_path = _write_proof_profile_fixture(workspace_root)
    aware_cli = _write_fake_aware_cli(
        tmp_path / "install" / "stable" / "0.8.0" / "bin" / "aware-cli"
    )
    install_receipt_path = tmp_path / "receipts" / "install.json"
    install_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    install_receipt_path.write_text(
        json.dumps(
            {
                "channel": "stable",
                "version": "0.8.0",
                "platform": "linux-x86_64",
                "install_root": str((tmp_path / "install").resolve()),
                "aware_cli_executable": str(aware_cli.resolve()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "validate",
            "--workspace-root",
            str(workspace_root),
            "--validation-root",
            str(tmp_path / "validation"),
            "--profile",
            str(profile_path),
            "--install-receipt-path",
            str(install_receipt_path),
            "--operator",
            "Luis",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["profile_id"] == "graph_os_home_story_compile"
    assert payload["public_repo_slug"] == "home-workspace"
    assert payload["status"] == "passed_with_repo_assist"
    index_path = Path(payload["index_path"])
    assert index_path.is_file()
    pack_index = json.loads(index_path.read_text(encoding="utf-8"))
    assert pack_index["producer"]["tool"] == "aware-sdk"
    assert pack_index["publication_id"] == "home-workspace"
    assert pack_index["consumer"] == "github-repo"
    assert pack_index["release_track"] == "compile-first"
    assert pack_index["honesty"]["used_installed_launcher"] is True
    assert pack_index["honesty"]["repo_assisted"] is True
    assert pack_index["receipts"]["proof_sync"] == "receipts/proof-sync.json"
    assert Path(payload["sync_receipt_path"]).is_file()
    assert Path(payload["target_repo_root"]).is_dir()


def test_run_validation_rejects_sdk_root_as_validation_root(tmp_path: Path) -> None:
    workspace_root = tmp_path / "repo"
    workspace_root.mkdir()
    sdk_root = tmp_path / "sdk"
    install_root = sdk_root / "install"
    aware_cli = _write_fake_aware_cli(
        install_root / "stable" / "0.8.0" / "bin" / "aware-cli"
    )
    install_receipt_path = sdk_root / "receipts" / "install.json"
    install_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    install_receipt_path.write_text(
        json.dumps(
            {
                "channel": "stable",
                "version": "0.8.0",
                "platform": "linux-x86_64",
                "install_root": str(install_root.resolve()),
                "aware_cli_executable": str(aware_cli.resolve()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        validate_module.ValidationError, match="must not contain the SDK install root"
    ):
        _ = validate_module.run_validation(
            workspace_root=workspace_root,
            validation_root=sdk_root,
            install_receipt_path=install_receipt_path,
        )


def test_run_validation_rejects_install_receipt_inside_validation_root(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "repo"
    workspace_root.mkdir()
    validation_root = tmp_path / "validation"
    install_root = tmp_path / "sdk" / "install"
    aware_cli = _write_fake_aware_cli(
        install_root / "stable" / "0.8.0" / "bin" / "aware-cli"
    )
    install_receipt_path = validation_root / "receipts" / "install.json"
    install_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    install_receipt_path.write_text(
        json.dumps(
            {
                "channel": "stable",
                "version": "0.8.0",
                "platform": "linux-x86_64",
                "install_root": str(install_root.resolve()),
                "aware_cli_executable": str(aware_cli.resolve()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        validate_module.ValidationError, match="must not contain the install receipt"
    ):
        _ = validate_module.run_validation(
            workspace_root=workspace_root,
            validation_root=validation_root,
            install_receipt_path=install_receipt_path,
        )


def test_cli_validate_forwards_named_proof_rail(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    observed: dict[str, object] = {}

    def fake_run_validation(**kwargs) -> ValidationRunResult:
        observed.update(kwargs)
        return ValidationRunResult(
            proof_rail=str(kwargs["proof_rail"]),
            profile_id="graph_os_home_story_workspace",
            public_repo_slug="home-workspace",
            workspace_root=Path(kwargs["workspace_root"]),
            validation_root=Path(kwargs["validation_root"]),
            install_receipt_path=tmp_path / "receipts" / "install.json",
            aware_cli_executable=tmp_path / "install" / "bin" / "aware-cli",
            staged_repo_root=tmp_path / "validation" / "stage" / "home-workspace",
            stage_receipt_path=tmp_path
            / "validation"
            / "receipts"
            / "proof-stage.json",
            verification_receipt_path=tmp_path
            / "validation"
            / "receipts"
            / "proof-verify.json",
            packaged_repo_root=tmp_path / "validation" / "package" / "home-workspace",
            package_receipt_path=tmp_path
            / "validation"
            / "receipts"
            / "proof-package.json",
            target_repo_root=None,
            sync_receipt_path=None,
            workspace_lifecycle_receipt_path=None,
            pack_root=tmp_path / "validation" / "pack",
            index_path=tmp_path / "validation" / "pack" / "index.json",
            status="passed_with_repo_assist",
            summary="workspace-first proof rail",
        )

    monkeypatch.setattr(validate_module, "run_validation", fake_run_validation)

    exit_code = cli.main(
        [
            "validate",
            "--workspace-root",
            str(tmp_path / "repo"),
            "--validation-root",
            str(tmp_path / "validation"),
            "--proof-rail",
            "workspace-first",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["proof_rail"] == "workspace-first"
    assert payload["profile_id"] == "graph_os_home_story_workspace"
    assert observed["proof_rail"] == "workspace-first"
    assert observed["profile_path"] is None


def test_cli_validate_workspace_first_emits_workspace_lifecycle_receipt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    workspace_root = tmp_path / "repo"
    profile_path = _write_workspace_proof_profile_fixture(workspace_root)
    aware_cli = _write_fake_aware_cli(
        tmp_path / "install" / "stable" / "0.8.0" / "bin" / "aware-cli"
    )
    install_receipt_path = tmp_path / "receipts" / "install.json"
    install_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    install_receipt_path.write_text(
        json.dumps(
            {
                "channel": "stable",
                "version": "0.8.0",
                "platform": "linux-x86_64",
                "install_root": str((tmp_path / "install").resolve()),
                "aware_cli_executable": str(aware_cli.resolve()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_run_workspace_lifecycle_proof(**kwargs) -> WorkspaceLifecycleProofResult:
        validation_root = Path(kwargs["validation_root"]).resolve()
        workspace_root = validation_root / "workspace-lifecycle" / "fresh-root"
        workspace_root.mkdir(parents=True, exist_ok=True)
        receipt_path = Path(kwargs["receipt_path"]).resolve()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        summary = {
            "workspace_root": str(workspace_root),
            "module_id": "sample",
            "command_order": [
                "initial_status",
                "bootstrap",
                "post_bootstrap_status",
                "empty_workspace_compile",
                "module_create",
                "module_compile",
            ],
            "initial_status": {
                "summary_kind": "bootstrap_required",
                "cta_action_id": "workspace_bootstrap",
            },
            "bootstrap": {
                "summary_kind": "ready_for_module_creation",
                "next_action_ids": ["module_create_explicit"],
            },
            "post_bootstrap_status": {
                "summary_kind": "workspace_ready_no_history",
            },
            "empty_workspace_compile": {
                "diagnostic_code": "workspace.compile.workspace_manifest_empty",
            },
            "module_create": {
                "status": "ok",
                "module_root": str(workspace_root / "modules" / "sample"),
            },
            "module_compile": {
                "scope_kind": "module",
                "scope_key": "sample",
            },
        }
        receipt_path.write_text(
            json.dumps(
                {
                    "receipt_version": 1,
                    "status": "verified",
                    "failure_message": None,
                    "workspace_root": str(workspace_root),
                    "module_id": "sample",
                    "summary": summary,
                    "command_results": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return WorkspaceLifecycleProofResult(
            receipt_path=receipt_path,
            workspace_root=workspace_root,
            module_id="sample",
            command_results=(),
            summary=summary,
        )

    monkeypatch.setattr(
        validate_module,
        "run_workspace_lifecycle_proof",
        fake_run_workspace_lifecycle_proof,
    )

    exit_code = cli.main(
        [
            "validate",
            "--workspace-root",
            str(workspace_root),
            "--validation-root",
            str(tmp_path / "validation"),
            "--profile",
            str(profile_path),
            "--install-receipt-path",
            str(install_receipt_path),
            "--operator",
            "Luis",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["profile_id"] == "graph_os_home_story_workspace"
    assert payload["workspace_lifecycle_receipt_path"] is not None
    receipt_path = Path(payload["workspace_lifecycle_receipt_path"])
    assert receipt_path.is_file()
    pack_index = json.loads(Path(payload["index_path"]).read_text(encoding="utf-8"))
    assert (
        pack_index["receipts"]["workspace_lifecycle"]
        == "receipts/workspace-lifecycle.json"
    )
    assert pack_index["workspace_lifecycle"]["fresh_root"]["initial_status"][
        "summary_kind"
    ] == ("bootstrap_required")
    assert pack_index["workspace_lifecycle"]["fresh_root"]["module_compile"] == {
        "scope_key": "sample",
        "scope_kind": "module",
    }


def test_resolve_profile_path_supports_workspace_first_public_rail() -> None:
    with ExitStack() as stack:
        resolved = validate_module._resolve_profile_path(
            profile_path=None,
            proof_rail="workspace-first",
            stack=stack,
        )

    assert resolved.name == "graph_os_home_story_workspace.toml"


def test_resolve_profile_path_rejects_profile_and_proof_rail(
    tmp_path: Path,
) -> None:
    explicit_profile = tmp_path / "proof.toml"
    explicit_profile.write_text("version = 1\n", encoding="utf-8")

    with ExitStack() as stack:
        try:
            validate_module._resolve_profile_path(
                profile_path=explicit_profile,
                proof_rail="workspace-first",
                stack=stack,
            )
        except validate_module.ValidationError as exc:
            assert "Cannot combine --profile with --proof-rail." in str(exc)
        else:
            raise AssertionError("expected ValidationError for mixed profile selectors")


def test_cli_install_resolves_entry_and_writes_receipt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    installer_payload = tmp_path / "aware-sdk-installer.pyz"
    installer_payload.write_bytes(b"installer-payload")
    archive_path = (
        tmp_path / "aware-cli-stable-0.8.0-public-cli-slim-linux-x86_64.tar.gz"
    )
    archive_path.write_bytes(b"bundle-archive")
    index_path = tmp_path / "aware-sdk-linux-x86_64.json"
    index_path.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "channel": "stable",
                        "version": "0.8.0-public-cli-slim",
                        "platform": "linux-x86_64",
                        "archive_url": archive_path.resolve().as_uri(),
                        "archive_sha256": _sha256(archive_path),
                        "installer_payload_url": installer_payload.resolve().as_uri(),
                        "installer_payload_sha256": _sha256(installer_payload),
                        "capabilities": [
                            "compile",
                            "runtime",
                            "python",
                            "sql",
                            "sqlite",
                        ],
                        "bootstrap_kind": "python_zipapp",
                        "published_at": "2026-04-17T08:44:00Z",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    install_root = tmp_path / "installs"
    receipt_path = tmp_path / "receipt.json"
    invoked: dict[str, object] = {}

    def fake_invoke_installer_payload(
        *,
        bootstrap_python: str,
        installer_path: Path,
        archive_path: Path,
        install_root: Path,
        receipt_path: Path,
        force: bool,
        python_executable: str,
    ) -> dict[str, object]:
        invoked.update(
            {
                "bootstrap_python": bootstrap_python,
                "installer_path": installer_path,
                "installer_bytes": installer_path.read_bytes(),
                "archive_path": archive_path,
                "archive_bytes": archive_path.read_bytes(),
                "install_root": install_root,
                "receipt_path": receipt_path,
                "force": force,
                "python_executable": python_executable,
            }
        )
        installed_dir = install_root / "stable" / "0.8.0-public-cli-slim"
        cli_launcher_path = installed_dir / "bin" / "aware-cli"
        sdk_launcher_path = installed_dir / "bin" / "aware-sdk"
        cli_launcher_path.parent.mkdir(parents=True, exist_ok=True)
        cli_launcher_path.write_text("#!/bin/sh\n", encoding="utf-8")
        sdk_launcher_path.write_text("#!/bin/sh\n", encoding="utf-8")
        return {
            "installed_dir": str(installed_dir),
            "aware_cli_executable": str(cli_launcher_path),
            "aware_sdk_executable": str(sdk_launcher_path),
            "manifest_path": str(installed_dir / "manifest.json"),
            "bundle_metadata_path": str(installed_dir / "bundle.json"),
            "python_runtime_executable": str(
                installed_dir / "runtime" / "bin" / "python"
            ),
            "channel": "stable",
            "version": "0.8.0-public-cli-slim",
            "platform": "linux-x86_64",
        }

    monkeypatch.setattr(cli, "_invoke_installer_payload", fake_invoke_installer_payload)

    exit_code = cli.main(
        [
            "install",
            "--index-url",
            index_path.resolve().as_uri(),
            "--channel",
            "stable",
            "--platform",
            "linux-x86_64",
            "--install-root",
            str(install_root),
            "--receipt-path",
            str(receipt_path),
            "--force",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["installed_dir"].endswith("stable/0.8.0-public-cli-slim")
    assert payload["receipt_path"] == str(receipt_path.resolve())
    assert payload["install_distribution"]["index_url"] == index_path.resolve().as_uri()
    assert (
        payload["install_distribution"]["resolved_entry"]["archive_url"]
        == archive_path.resolve().as_uri()
    )
    assert payload["activation"]["channel_current_link"].endswith(
        "channels/stable/current"
    )
    assert payload["activation"]["launcher_link"].endswith("bin/aware-cli")
    assert payload["activation"]["launchers"]["aware-sdk"]["launcher_link"].endswith(
        "bin/aware-sdk"
    )
    assert receipt_path.exists()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["aware_cli_executable"] == payload["aware_cli_executable"]
    assert receipt["aware_sdk_executable"] == payload["aware_sdk_executable"]
    assert invoked["bootstrap_python"] == sys.executable
    assert invoked["python_executable"] == sys.executable
    installer_path_invoked = invoked["installer_path"]
    archive_path_invoked = invoked["archive_path"]
    install_root_invoked = invoked["install_root"]
    receipt_path_invoked = invoked["receipt_path"]
    assert isinstance(installer_path_invoked, Path)
    assert isinstance(archive_path_invoked, Path)
    assert isinstance(install_root_invoked, Path)
    assert isinstance(receipt_path_invoked, Path)
    assert installer_path_invoked.name == installer_payload.name
    assert invoked["installer_bytes"] == installer_payload.read_bytes()
    assert archive_path_invoked.name == archive_path.name
    assert invoked["archive_bytes"] == archive_path.read_bytes()
    assert install_root_invoked == install_root.resolve()
    assert receipt_path_invoked == receipt_path.resolve()
    assert invoked["force"] is True
    current_link = tmp_path / "channels" / "stable" / "current"
    launcher_link = tmp_path / "bin" / "aware-cli"
    sdk_launcher_link = tmp_path / "bin" / "aware-sdk"
    assert current_link.is_symlink()
    assert launcher_link.is_symlink()
    assert sdk_launcher_link.is_symlink()
    assert current_link.resolve() == install_root / "stable" / "0.8.0-public-cli-slim"
    assert (
        launcher_link.resolve()
        == install_root / "stable" / "0.8.0-public-cli-slim" / "bin" / "aware-cli"
    )
    assert (
        sdk_launcher_link.resolve()
        == install_root / "stable" / "0.8.0-public-cli-slim" / "bin" / "aware-sdk"
    )


def test_cli_install_resolves_authority_head_without_mirror_entries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    installer_payload = tmp_path / "aware-sdk-installer.pyz"
    installer_payload.write_bytes(b"installer-payload")
    archive_path = (
        tmp_path / "aware-cli-stable-0.8.0-public-cli-slim-linux-x86_64.tar.gz"
    )
    archive_path.write_bytes(b"bundle-archive")
    index_path = tmp_path / "aware-sdk-linux-x86_64.json"
    revision_id = "bootstrap:linux-x86_64:0.8.0-public-cli-slim:abcd1234ef56"
    index_path.write_text(
        json.dumps(
            {
                "version": 2,
                "authority_kind": "bootstrap_distribution",
                "revisions": [
                    {
                        "revision_id": revision_id,
                        "version": "0.8.0-public-cli-slim",
                        "platform": "linux-x86_64",
                        "archive_url": archive_path.resolve().as_uri(),
                        "archive_sha256": _sha256(archive_path),
                        "installer_payload_url": installer_payload.resolve().as_uri(),
                        "installer_payload_sha256": _sha256(installer_payload),
                        "manifest_url": None,
                        "capabilities": [
                            "compile",
                            "runtime",
                            "python",
                            "sql",
                            "sqlite",
                        ],
                        "bootstrap_kind": "python_zipapp",
                        "published_at": "2026-04-18T00:00:00Z",
                    }
                ],
                "channel_heads": [
                    {
                        "channel": "stable",
                        "platform": "linux-x86_64",
                        "revision_id": revision_id,
                        "version": "0.8.0-public-cli-slim",
                        "updated_at": "2026-04-18T00:01:00Z",
                    }
                ],
                "entries": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    install_root = tmp_path / "installs"
    receipt_path = tmp_path / "receipt.json"

    def fake_invoke_installer_payload(
        *,
        bootstrap_python: str,
        installer_path: Path,
        archive_path: Path,
        install_root: Path,
        receipt_path: Path,
        force: bool,
        python_executable: str,
    ) -> dict[str, object]:
        _ = (
            bootstrap_python,
            installer_path,
            archive_path,
            receipt_path,
            force,
            python_executable,
        )
        installed_dir = install_root / "stable" / "0.8.0-public-cli-slim"
        cli_launcher_path = installed_dir / "bin" / "aware-cli"
        sdk_launcher_path = installed_dir / "bin" / "aware-sdk"
        cli_launcher_path.parent.mkdir(parents=True, exist_ok=True)
        cli_launcher_path.write_text("#!/bin/sh\n", encoding="utf-8")
        sdk_launcher_path.write_text("#!/bin/sh\n", encoding="utf-8")
        return {
            "installed_dir": str(installed_dir),
            "aware_cli_executable": str(cli_launcher_path),
            "aware_sdk_executable": str(sdk_launcher_path),
            "manifest_path": str(installed_dir / "manifest.json"),
            "bundle_metadata_path": str(installed_dir / "bundle.json"),
            "python_runtime_executable": str(
                installed_dir / "runtime" / "bin" / "python"
            ),
            "channel": "stable",
            "version": "0.8.0-public-cli-slim",
            "platform": "linux-x86_64",
        }

    monkeypatch.setattr(cli, "_invoke_installer_payload", fake_invoke_installer_payload)

    exit_code = cli.main(
        [
            "install",
            "--index-url",
            index_path.resolve().as_uri(),
            "--channel",
            "stable",
            "--platform",
            "linux-x86_64",
            "--install-root",
            str(install_root),
            "--receipt-path",
            str(receipt_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert (
        payload["install_distribution"]["resolved_entry"]["revision_id"] == revision_id
    )
    assert (
        payload["install_distribution"]["resolved_entry"]["archive_url"]
        == archive_path.resolve().as_uri()
    )


def test_cli_install_resolves_from_authority_base_url(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    installer_payload = tmp_path / "aware-sdk-installer.pyz"
    installer_payload.write_bytes(b"installer-payload")
    archive_path = (
        tmp_path / "aware-cli-stable-0.8.0-public-cli-slim-linux-x86_64.tar.gz"
    )
    archive_path.write_bytes(b"bundle-archive")
    authority_root = tmp_path / "authority"
    index_path = (
        authority_root / "bootstrap" / "aware-sdk" / "linux-x86_64" / "index.json"
    )
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(
            {
                "version": 2,
                "authority_kind": "bootstrap_distribution",
                "revisions": [
                    {
                        "revision_id": "bootstrap:linux-x86_64:0.8.0-public-cli-slim:abcd1234ef56",
                        "version": "0.8.0-public-cli-slim",
                        "platform": "linux-x86_64",
                        "archive_url": archive_path.resolve().as_uri(),
                        "archive_sha256": _sha256(archive_path),
                        "installer_payload_url": installer_payload.resolve().as_uri(),
                        "installer_payload_sha256": _sha256(installer_payload),
                        "manifest_url": None,
                        "capabilities": [
                            "compile",
                            "runtime",
                            "python",
                            "sql",
                            "sqlite",
                        ],
                        "bootstrap_kind": "python_zipapp",
                        "published_at": "2026-04-18T00:00:00Z",
                    }
                ],
                "channel_heads": [
                    {
                        "channel": "stable",
                        "platform": "linux-x86_64",
                        "revision_id": "bootstrap:linux-x86_64:0.8.0-public-cli-slim:abcd1234ef56",
                        "version": "0.8.0-public-cli-slim",
                        "updated_at": "2026-04-18T00:01:00Z",
                    }
                ],
                "entries": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    install_root = tmp_path / "installs"
    receipt_path = tmp_path / "receipt.json"

    def fake_invoke_installer_payload(
        *,
        bootstrap_python: str,
        installer_path: Path,
        archive_path: Path,
        install_root: Path,
        receipt_path: Path,
        force: bool,
        python_executable: str,
    ) -> dict[str, object]:
        _ = (
            bootstrap_python,
            installer_path,
            archive_path,
            receipt_path,
            force,
            python_executable,
        )
        installed_dir = install_root / "stable" / "0.8.0-public-cli-slim"
        cli_launcher_path = installed_dir / "bin" / "aware-cli"
        sdk_launcher_path = installed_dir / "bin" / "aware-sdk"
        cli_launcher_path.parent.mkdir(parents=True, exist_ok=True)
        cli_launcher_path.write_text("#!/bin/sh\n", encoding="utf-8")
        sdk_launcher_path.write_text("#!/bin/sh\n", encoding="utf-8")
        return {
            "installed_dir": str(installed_dir),
            "aware_cli_executable": str(cli_launcher_path),
            "aware_sdk_executable": str(sdk_launcher_path),
            "manifest_path": str(installed_dir / "manifest.json"),
            "bundle_metadata_path": str(installed_dir / "bundle.json"),
            "python_runtime_executable": str(
                installed_dir / "runtime" / "bin" / "python"
            ),
            "channel": "stable",
            "version": "0.8.0-public-cli-slim",
            "platform": "linux-x86_64",
        }

    monkeypatch.setattr(cli, "_invoke_installer_payload", fake_invoke_installer_payload)

    exit_code = cli.main(
        [
            "install",
            "--authority-base-url",
            authority_root.resolve().as_uri(),
            "--channel",
            "stable",
            "--platform",
            "linux-x86_64",
            "--install-root",
            str(install_root),
            "--receipt-path",
            str(receipt_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert (
        payload["install_distribution"]["authority_base_url"]
        == authority_root.resolve().as_uri()
    )
    assert payload["install_distribution"]["index_url"] == (
        authority_root.resolve().as_uri()
        + "/bootstrap/aware-sdk/linux-x86_64/index.json"
    )


def test_cli_activate_points_channel_and_launcher(tmp_path: Path, capsys) -> None:
    install_root = tmp_path / "installs"
    version_dir = _make_installed_version(
        install_root, "stable", "0.8.0-public-cli-slim"
    )
    receipt_path = tmp_path / "receipts" / "activate.json"

    exit_code = cli.main(
        [
            "activate",
            "--channel",
            "stable",
            "--version",
            "0.8.0-public-cli-slim",
            "--install-root",
            str(install_root),
            "--receipt-path",
            str(receipt_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["installed_dir"] == str(version_dir)
    assert receipt_path.exists()
    current_link = tmp_path / "channels" / "stable" / "current"
    launcher_link = tmp_path / "bin" / "aware-cli"
    sdk_launcher_link = tmp_path / "bin" / "aware-sdk"
    assert current_link.is_symlink()
    assert launcher_link.is_symlink()
    assert sdk_launcher_link.is_symlink()
    assert current_link.resolve() == version_dir
    assert launcher_link.resolve() == version_dir / "bin" / "aware-cli"
    assert sdk_launcher_link.resolve() == version_dir / "bin" / "aware-sdk"


def test_cli_rollback_selects_prior_installed_version(tmp_path: Path, capsys) -> None:
    install_root = tmp_path / "installs"
    previous_dir = _make_installed_version(
        install_root, "stable", "0.7.9-public-cli-slim"
    )
    current_dir = _make_installed_version(
        install_root, "stable", "0.8.0-public-cli-slim"
    )
    os.utime(previous_dir, (1, 1))
    os.utime(current_dir, (2, 2))
    activate_receipt = tmp_path / "receipts" / "activate.json"
    rollback_receipt = tmp_path / "receipts" / "rollback.json"

    assert (
        cli.main(
            [
                "activate",
                "--channel",
                "stable",
                "--version",
                "0.8.0-public-cli-slim",
                "--install-root",
                str(install_root),
                "--receipt-path",
                str(activate_receipt),
            ]
        )
        == 0
    )
    _ = capsys.readouterr()

    exit_code = cli.main(
        [
            "rollback",
            "--channel",
            "stable",
            "--install-root",
            str(install_root),
            "--receipt-path",
            str(rollback_receipt),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["rollback"]["from_version"] == "0.8.0-public-cli-slim"
    assert payload["rollback"]["to_version"] == "0.7.9-public-cli-slim"
    assert rollback_receipt.exists()
    current_link = tmp_path / "channels" / "stable" / "current"
    launcher_link = tmp_path / "bin" / "aware-cli"
    sdk_launcher_link = tmp_path / "bin" / "aware-sdk"
    assert current_link.resolve() == previous_dir
    assert launcher_link.resolve() == previous_dir / "bin" / "aware-cli"
    assert sdk_launcher_link.resolve() == previous_dir / "bin" / "aware-sdk"


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _make_installed_version(install_root: Path, channel: str, version: str) -> Path:
    version_dir = install_root / channel / version
    launcher_dir = version_dir / "bin"
    launcher_dir.mkdir(parents=True, exist_ok=True)
    (launcher_dir / "aware-cli").write_text("#!/bin/sh\n", encoding="utf-8")
    (launcher_dir / "aware-sdk").write_text("#!/bin/sh\n", encoding="utf-8")
    return version_dir


def _write_proof_profile_fixture(workspace_root: Path) -> Path:
    source_workspace_root = workspace_root / "workspaces" / "aware_home"
    source_workspace_root.mkdir(parents=True, exist_ok=True)
    (source_workspace_root / "aware.environment.toml").write_text(
        "aware = 1\n", encoding="utf-8"
    )
    (source_workspace_root / "README.md").write_text("proof\n", encoding="utf-8")

    publication_recipe = (
        workspace_root
        / "publications"
        / "home-workspace"
        / "recipes"
        / "github-repo.json"
    )
    publication_recipe.parent.mkdir(parents=True, exist_ok=True)
    publication_recipe.write_text(
        json.dumps(
            {
                "publication_id": "home-workspace",
                "consumer": "github-repo",
                "release_tracks": [
                    {
                        "id": "compile-first",
                        "root_contract": ["aware.environment.toml"],
                        "include_paths": ["README.md"],
                        "exclude_paths": [".aware/**", "_aware/**"],
                        "overlay_paths": [],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    publication_ref = (
        workspace_root
        / "publications"
        / "shared-digital-reality"
        / "narrative"
        / "canonical.md"
    )
    publication_ref.parent.mkdir(parents=True, exist_ok=True)
    publication_ref.write_text("# canonical\n", encoding="utf-8")

    bundle_profile = (
        workspace_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "sdks"
        / "aware"
        / "python"
        / "aware_sdk"
        / "configs"
        / "bundles"
        / "graph_os_linux_cli_public.toml"
    )
    bundle_profile.parent.mkdir(parents=True, exist_ok=True)
    bundle_profile.write_text(
        'version = 2\nid = "graph_os_linux_cli_public"\npackages = ["aware-cli", "aware-sdk"]\n',
        encoding="utf-8",
    )

    proof_profile_path = (
        workspace_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "sdks"
        / "aware"
        / "python"
        / "aware_sdk"
        / "configs"
        / "proofs"
        / "graph_os_home_story_compile.toml"
    )
    proof_profile_path.parent.mkdir(parents=True, exist_ok=True)
    proof_profile_path.write_text(
        "\n".join(
            [
                "version = 1",
                'id = "graph_os_home_story_compile"',
                'bundle_profile_path = "workspaces/aware_network/modules/interface/sdks/aware/python/aware_sdk/configs/bundles/graph_os_linux_cli_public.toml"',
                'source_workspace_root = "workspaces/aware_home"',
                'public_repo_slug = "home-workspace"',
                'publication_recipe_path = "publications/home-workspace/recipes/github-repo.json"',
                'publication_release_track_id = "compile-first"',
                "verification_commands = [",
                '  "aware-cli compile --repo-root . --materialization-mode runtime --lock-mode off module home",',
                (
                    '  "aware-cli compile --repo-root . --materialization-mode runtime '
                    '--lock-mode off --genesis --genesis-confirm environment home-story",'
                ),
                "]",
                (
                    'expected_outputs = [".aware/reports/latest_compile_success.json", '
                    '"_aware/environment/runtime/environment.manifest.json"]'
                ),
                "exclude_generated = true",
                "generated_globs = [",
                '  ".aware/**",',
                '  "_aware/**",',
                "]",
                "publication_refs = [",
                '  "publications/shared-digital-reality/narrative/canonical.md",',
                "]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return proof_profile_path


def _write_workspace_proof_profile_fixture(workspace_root: Path) -> Path:
    proof_profile_path = _write_proof_profile_fixture(workspace_root)
    publication_recipe = (
        workspace_root
        / "publications"
        / "home-workspace"
        / "recipes"
        / "github-repo.json"
    )
    compile_module_home = (
        '  "aware-cli compile --repo-root . '
        '--materialization-mode runtime --lock-mode off module home",\n'
    )
    compile_environment_home_story = (
        '  "aware-cli compile --repo-root . --materialization-mode runtime '
        '--lock-mode off --genesis --genesis-confirm environment home-story",\n'
    )
    publication_recipe.write_text(
        json.dumps(
            {
                "publication_id": "home-workspace",
                "consumer": "github-repo",
                "release_tracks": [
                    {
                        "id": "compile-first",
                        "root_contract": ["aware.environment.toml"],
                        "include_paths": ["README.md"],
                        "exclude_paths": [".aware/**", "_aware/**"],
                        "overlay_paths": [],
                    },
                    {
                        "id": "workspace-first",
                        "root_contract": [
                            "README.md",
                            "aware.environment.toml",
                            "aware.workspace.toml",
                        ],
                        "include_paths": [
                            "README.md",
                            "aware.environment.toml",
                            "aware.workspace.toml",
                        ],
                        "exclude_paths": [".aware/**", "_aware/**"],
                        "overlay_paths": [],
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    proof_profile_path.write_text(
        proof_profile_path.read_text(encoding="utf-8")
        .replace(
            'id = "graph_os_home_story_compile"', 'id = "graph_os_home_story_workspace"'
        )
        .replace(
            'publication_release_track_id = "compile-first"',
            'publication_release_track_id = "workspace-first"',
        )
        .replace(
            "verification_commands = [\n"
            + compile_module_home
            + compile_environment_home_story
            + "]",
            "verification_commands = [\n"
            + compile_module_home
            + compile_environment_home_story
            + '  "aware-cli workspace status --repo-root . --json",\n'
            + "]",
        ),
        encoding="utf-8",
    )
    return proof_profile_path


def _write_fake_aware_cli(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "import json",
                "from pathlib import Path",
                "import sys",
                "",
                "root = Path.cwd()",
                "args = sys.argv[1:]",
                'if len(args) >= 2 and args[0] == "workspace" and args[1] == "status":',
                "    payload = {",
                '        "workspace_root": str(root),',
                '        "status_version": "aware.workspace.status.v1",',
                '        "blocks": [',
                "            {",
                '                "name": "local_fs_view",',
                '                "available": True,',
                '                "payload": {',
                '                    "changed_packages": [],',
                '                    "unmapped_path_count": 0,',
                '                    "warnings": [],',
                "                },",
                "            },",
                "            {",
                '                "name": "commit_truth",',
                '                "available": False,',
                '                "unavailable_reason": "no_workspace_history_yet",',
                "            },",
                "        ],",
                "    }",
                "    print(json.dumps(payload))",
                "    raise SystemExit(0)",
                'if "--genesis" in args:',
                '    target = root / "_aware" / "environment" / "runtime" / "environment.manifest.json"',
                "else:",
                '    target = root / ".aware" / "reports" / "latest_compile_success.json"',
                "target.parent.mkdir(parents=True, exist_ok=True)",
                'target.write_text("{}", encoding="utf-8")',
                'print("ok")',
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _write_fake_workspace_lifecycle_aware_cli(
    path: Path,
    *,
    missing_readiness: bool = False,
    module_root_outside_workspace: bool = False,
    skip_module_root_directory: bool = False,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "import json",
                "from pathlib import Path",
                "import sys",
                "",
                f"MISSING_READINESS = {missing_readiness!r}",
                f"MODULE_ROOT_OUTSIDE_WORKSPACE = {module_root_outside_workspace!r}",
                f"SKIP_MODULE_ROOT_DIRECTORY = {skip_module_root_directory!r}",
                "args = sys.argv[1:]",
                "",
                "def _repo_root() -> Path:",
                '    index = args.index("--repo-root")',
                "    return Path(args[index + 1]).resolve()",
                "",
                "if len(args) >= 2 and args[0] == 'workspace' and args[1] == 'status':",
                "    repo_root = _repo_root()",
                "    repo_root.mkdir(parents=True, exist_ok=True)",
                "    ready = (repo_root / 'aware.workspace.toml').is_file()",
                "    payload = {",
                "        'workspace_root': str(repo_root),",
                "        'status_version': 'aware.workspace.status.v1',",
                "        'blocks': [",
                "            {",
                "                'name': 'local_fs_view',",
                "                'available': True,",
                "                'payload': {",
                "                    'changed_packages': [],",
                "                    'unmapped_path_count': 0,",
                "                    'warnings': [],",
                "                },",
                "            },",
                "            {",
                "                'name': 'commit_truth',",
                "                'available': False,",
                "                'unavailable_reason': (",
                "                    'no_workspace_history_yet'",
                "                    if ready",
                "                    else 'committed_workspace_unavailable'",
                "                ),",
                "            },",
                "        ],",
                "    }",
                "    if not MISSING_READINESS:",
                "        if ready:",
                "            payload['readiness'] = {",
                "                'summary_kind': 'workspace_ready_no_history',",
                "                'workspace_state': 'present',",
                "                'workspace_manifest_present': True,",
                "                'environment_manifest_present': False,",
                "                'history_state': 'no_history',",
                "                'call_to_action': None,",
                "            }",
                "        else:",
                "            payload['readiness'] = {",
                "                'summary_kind': 'bootstrap_required',",
                "                'workspace_state': 'missing',",
                "                'workspace_manifest_present': False,",
                "                'environment_manifest_present': False,",
                "                'history_state': 'unavailable',",
                "                'call_to_action': {",
                "                    'action_id': 'workspace_bootstrap',",
                "                    'command': f'aware-cli workspace bootstrap --repo-root {repo_root}',",
                "                },",
                "            }",
                "    print(json.dumps(payload))",
                "    raise SystemExit(0)",
                "",
                "if len(args) >= 2 and args[0] == 'workspace' and args[1] == 'bootstrap':",
                "    repo_root = _repo_root()",
                "    repo_root.mkdir(parents=True, exist_ok=True)",
                "    (repo_root / 'aware.workspace.toml').write_text(",
                "        '\\n'.join([",
                "            'aware = 1',",
                "            '',",
                "            '[workspace]',",
                "            'handle = \"demo\"',",
                "            'title = \"Demo Workspace\"',",
                "            'environments = []',",
                "            'apis = []',",
                "            'services = []',",
                "            'experiences = []',",
                "            'interfaces = []',",
                "            '',",
                "        ]),",
                "        encoding='utf-8',",
                "    )",
                "    payload = {",
                "        'status': 'ok',",
                "        'workspace_manifest': {",
                "            'path': str(repo_root / 'aware.workspace.toml'),",
                "            'created': True,",
                "            'exists': True,",
                "        },",
                "        'bootstrap_summary': {",
                "            'summary_kind': 'ready_for_module_creation',",
                "        },",
                "        'next_required_actions': [",
                "            {'code': 'module_create_explicit'},",
                "        ],",
                "    }",
                "    print(json.dumps(payload))",
                "    raise SystemExit(0)",
                "",
                "if len(args) >= 2 and args[0] == 'workspace' and args[1] == 'compile':",
                "    repo_root = _repo_root()",
                "    payload = {",
                "        'preflight_status': 'ok',",
                "        'target_scope': 'workspace',",
                "        'target_ref': f'workspace:{repo_root.name}',",
                "        'diagnostic': {",
                "            'code': 'workspace.compile.workspace_manifest_empty',",
                "            'next_required_actions': [",
                "                {'action_id': 'module_create_explicit'},",
                "            ],",
                "        },",
                "    }",
                "    print(json.dumps(payload))",
                "    raise SystemExit(0)",
                "",
                "if len(args) >= 3 and args[0] == 'module' and args[1] == 'create':",
                "    module_id = args[2]",
                "    repo_root = _repo_root()",
                "    if MODULE_ROOT_OUTSIDE_WORKSPACE:",
                "        module_root = repo_root.parent / 'outside-modules' / module_id",
                "    else:",
                "        module_root = repo_root / 'modules' / module_id",
                "    if not SKIP_MODULE_ROOT_DIRECTORY:",
                "        module_root.mkdir(parents=True, exist_ok=True)",
                "    payload = {",
                "        'status': 'ok',",
                "        'module_root': str(module_root),",
                "        'root_pyproject': {",
                "            'planned_action': 'create',",
                "        },",
                "        'next_steps': [",
                "            f'aware-cli compile --update-lock module {module_id}',",
                "        ],",
                "    }",
                "    print(json.dumps(payload))",
                "    raise SystemExit(0)",
                "",
                "if args and args[0] == 'compile':",
                "    repo_root = _repo_root()",
                "    module_id = args[-1]",
                "    latest_report_path = repo_root / '.aware' / 'reports' / 'latest_compile_success.json'",
                "    latest_report_path.parent.mkdir(parents=True, exist_ok=True)",
                "    latest_report_path.write_text(",
                "        json.dumps({",
                "            'scope_kind': 'module',",
                "            'scope_key': module_id,",
                "        }),",
                "        encoding='utf-8',",
                "    )",
                "    print(json.dumps({",
                "        'preflight_status': 'ok',",
                "        'target_scope': 'module',",
                "        'target_ref': f'module:{module_id}',",
                "    }))",
                "    raise SystemExit(0)",
                "",
                "raise SystemExit(2)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path
