from __future__ import annotations

import ast
from pathlib import Path

from aware_workspace_operator.models import WorkspaceModuleCreateOptions
from aware_workspace_operator.module_create import run_workspace_module_create
from aware_workspace_operator.renderers import render_module_proof_test_scaffold


def _init_repo_root(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    _ = (repo_root / "aware.environment.toml").write_text(
        "aware = 1\n", encoding="utf-8"
    )
    return repo_root


def test_workspace_module_create_syncs_root_pyproject(tmp_path: Path) -> None:
    repo_root = _init_repo_root(tmp_path)

    outcome = run_workspace_module_create(
        options=WorkspaceModuleCreateOptions(
            repo_root=repo_root,
            module_id="sample",
        )
    )

    assert outcome.exit_code == 0
    report = outcome.report
    assert report.root_pyproject.planned_action == "create"
    assert (
        "modules/sample/ontology/runtime/python"
        in report.root_pyproject.workspace_members
    )
    assert (
        "modules/sample/services/environment" in report.root_pyproject.workspace_members
    )
    assert "aware-sample" in report.root_pyproject.workspace_sources
    assert "aware-sample-environment-service" in report.root_pyproject.workspace_sources

    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.uv.workspace]" in pyproject_text
    assert '"modules/sample/ontology/runtime/python"' in pyproject_text
    assert '"modules/sample/services/environment"' in pyproject_text
    assert "aware-sample = { workspace = true }" in pyproject_text
    assert "aware-sample-environment-service = { workspace = true }" in pyproject_text
    assert "aware-environment-artifacts" not in pyproject_text
    assert "meta_contract: bodyless Meta index" in pyproject_text
    assert "meta_runtime: committed Meta runtime proofs" in pyproject_text
    assert "meta_materialization: explicitly leased Meta" in pyproject_text


def test_workspace_module_create_merges_existing_workspace_members(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo_root(tmp_path)
    _ = (repo_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "workspace"',
                'version = "0.1.0"',
                'description = "Aware external workspace scaffold."',
                'requires-python = ">=3.12"',
                "dependencies = []",
                "",
                "[tool.uv]",
                "package = false",
                "",
                "[tool.uv.workspace]",
                "members = [",
                '  "modules/existing/runtime",',
                "]",
                "",
                "[tool.uv.sources]",
                "aware-existing = { workspace = true }",
                "",
                "[tool.flake8]",
                "max-line-length = 120",
                'extend-ignore = "E266"',
                "",
                "[tool.mypy]",
                'python_version = "3.12"',
                'disable_error_code = ["import-untyped"]',
                "",
                "[tool.basedpyright]",
                'pythonVersion = "3.12"',
                'typeCheckingMode = "standard"',
                "",
                "[tool.pytest.ini_options]",
                "markers = []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    outcome = run_workspace_module_create(
        options=WorkspaceModuleCreateOptions(
            repo_root=repo_root,
            module_id="sample",
        )
    )

    report = outcome.report
    assert report.root_pyproject.planned_action == "overwrite"
    assert "modules/existing/runtime" in report.root_pyproject.workspace_members
    assert (
        "modules/sample/ontology/runtime/python"
        in report.root_pyproject.workspace_members
    )
    assert "aware-existing" in report.root_pyproject.workspace_sources
    assert "aware-sample" in report.root_pyproject.workspace_sources


def test_module_proof_scaffold_uses_file_anchored_repo_root() -> None:
    rendered = render_module_proof_test_scaffold(
        module_id="sample",
        module_snake="sample",
    )

    ast.parse(rendered)
    assert "aware_utils." + "find_aware_root" not in rendered
    assert "find_aware_" + "repo_root" not in rendered
    assert "Path(__file__).resolve().parents[4]" in rendered


def test_module_proof_scaffold_starts_as_bodyless_meta_contract() -> None:
    rendered = render_module_proof_test_scaffold(
        module_id="sample",
        module_snake="sample",
    )

    assert "aware_" + "runtime" not in rendered
    assert "RuntimeHarness" not in rendered
    assert "resolve_module_runtime_manifest" not in rendered
    assert "from aware_meta.runtime import" not in rendered
    assert "build_meta_graph_runtime_for_aware_package_manifests" not in rendered
    assert "IsolatedMetaAwareRoot" not in rendered
    assert "@pytest.mark.meta_contract" in rendered
    assert "@pytest.mark.asyncio" not in rendered
