from __future__ import annotations

import json
from pathlib import Path

import pytest

from aware_code.language.operational_workspace import (
    CodeLanguageOperationalPackageRef,
    CodeLanguageOperationalWorkspaceRequest,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from python_grammar.operational_workspace import PythonOperationalWorkspaceBuilder


def test_python_operational_workspace_renders_uv_workspace_manifest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "checkout"
    hub_sdk = root / "workspaces" / "aware_kernel" / "sdks" / "hub" / "python"
    hub_sdk.mkdir(parents=True)
    (hub_sdk / "pyproject.toml").write_text(
        '[project]\nname = "aware-hub-sdk"\n',
        encoding="utf-8",
    )
    identity_sdk = (
        root / "workspaces" / "aware_kernel" / "sdks" / "identity" / "python"
    )
    identity_sdk.mkdir(parents=True)
    (identity_sdk / "pyproject.toml").write_text(
        '[project]\nname = "aware-identity-sdk"\n',
        encoding="utf-8",
    )

    result = PythonOperationalWorkspaceBuilder().materialize_operational_workspace(
        CodeLanguageOperationalWorkspaceRequest(
            workspace_key="aware-kernel",
            language=CodeLanguage.python,
            output_root=root,
            packages=(
                CodeLanguageOperationalPackageRef(
                    package_name="aware-hub-sdk",
                    language=CodeLanguage.python,
                    role="workspace_revision",
                    source_root=hub_sdk,
                    manifest_path=hub_sdk / "pyproject.toml",
                ),
                CodeLanguageOperationalPackageRef(
                    package_name="aware-identity-sdk",
                    language=CodeLanguage.python,
                    role="workspace_revision",
                    source_root=identity_sdk,
                    manifest_path=identity_sdk / "pyproject.toml",
                ),
            ),
        )
    )

    pyproject_text = result.project_path.read_text(encoding="utf-8")
    assert '[tool.uv.workspace]\nmembers = [' in pyproject_text
    assert '"workspaces/aware_kernel/sdks/hub/python",' in pyproject_text
    assert '"workspaces/aware_kernel/sdks/identity/python",' in pyproject_text
    assert '"aware-hub-sdk" = { workspace = true }' in pyproject_text
    assert '"aware-identity-sdk" = { workspace = true }' in pyproject_text
    assert tmp_path.as_posix() not in pyproject_text

    payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert payload["manifest_version"] == (
        "aware.code.language.operational_workspace.python.v0"
    )
    assert payload["status"] == "ready"
    assert payload["project_path"] == "pyproject.toml"
    assert payload["packages"][0]["source_root"].startswith("workspaces/")
    assert tmp_path.as_posix() not in result.manifest_path.read_text(encoding="utf-8")
    assert result.command_prefix == ("uv", "run", "--project", ".")


def test_python_operational_workspace_rejects_external_package_roots(
    tmp_path: Path,
) -> None:
    root = tmp_path / "checkout"
    external = tmp_path / "external" / "aware-hub-sdk"
    external.mkdir(parents=True)
    (external / "pyproject.toml").write_text(
        '[project]\nname = "aware-hub-sdk"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="package roots must be under"):
        PythonOperationalWorkspaceBuilder().materialize_operational_workspace(
            CodeLanguageOperationalWorkspaceRequest(
                workspace_key="aware-kernel",
                language=CodeLanguage.python,
                output_root=root,
                packages=(
                    CodeLanguageOperationalPackageRef(
                        package_name="aware-hub-sdk",
                        language=CodeLanguage.python,
                        role="workspace_revision",
                        source_root=external,
                        manifest_path=external / "pyproject.toml",
                    ),
                ),
            )
        )
