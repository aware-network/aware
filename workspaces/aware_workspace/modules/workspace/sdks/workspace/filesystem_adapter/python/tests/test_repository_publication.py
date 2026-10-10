"""Bootstrap catalog/metadata proofs, not publication authority qualification."""

import ast
import tomllib
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
MODULE = PACKAGE.parents[3]
REPOSITORY = MODULE.parents[3]


def test_bootstrap_declares_its_exact_current_owner_closure():
    project = tomllib.loads((PACKAGE / "pyproject.toml").read_text())["project"]
    assert project["name"] == "aware-workspace-fs-adapter"
    assert project["version"] == "0.0.1"
    assert project["dependencies"] == [
        "aware-workspace-runtime>=0.1.1,<0.2.0",
        "aware-workspace-sdk>=0.1.0,<0.2.0",
    ]


def test_module_registers_one_canonical_source_package():
    packages = tomllib.loads((MODULE / "aware.module.toml").read_text())["packages"]
    selected = [p for p in packages if p["id"] == "workspace_fs_adapter_python"]
    assert selected == [
        {
            "id": "workspace_fs_adapter_python",
            "kind": "code",
            "manifest": "sdks/workspace/filesystem_adapter/python/pyproject.toml",
            "visibility": "module",
        }
    ]


@pytest.mark.parametrize("name", ["LICENSE", "NOTICE"])
def test_canonical_legal_files_are_preserved(name):
    assert (PACKAGE / name).read_bytes() == (REPOSITORY / name).read_bytes()


def test_wheel_selects_only_its_own_typed_import_root():
    manifest = tomllib.loads((PACKAGE / "pyproject.toml").read_text())
    wheel = manifest["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel["packages"] == ["aware_workspace_fs_adapter"]
    assert "force-include" not in wheel
    assert (PACKAGE / "aware_workspace_fs_adapter/py.typed").is_file()


@pytest.mark.parametrize(
    "name", ["__init__.py", "repository_publication.py", "git_writer.py", "models.py"]
)
def test_physical_sources_do_not_import_foreign_domain_implementations(name):
    tree = ast.parse((PACKAGE / "aware_workspace_fs_adapter" / name).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for imported in names:
            if imported.startswith("aware_"):
                assert imported.startswith(
                    ("aware_workspace_runtime", "aware_workspace_fs_adapter")
                )


def test_bootstrap_readme_distinguishes_source_from_installed_publication():
    readme = (PACKAGE / "README.md").read_text()
    assert "Source tests do not qualify installed publication" in readme
    assert "not the frozen neutral 0.1.0 successor" in readme


def test_operator_alias_resolves_to_the_one_original_writer_and_models():
    import aware_workspace_operator.commit as compatibility
    import aware_workspace_operator.models as compatibility_models
    from aware_workspace_fs_adapter import git_writer, models

    assert compatibility is git_writer
    assert compatibility.run_workspace_commit is git_writer.run_workspace_commit
    for name in (
        "WorkspaceCommitReport",
        "WorkspaceCommitOptions",
        "WorkspaceCommitOutcome",
        "WorkspaceContentCommitOptions",
        "WorkspaceAuthorizedCommitOptions",
    ):
        assert getattr(compatibility_models, name) is getattr(models, name)
    tree = ast.parse(
        (
            REPOSITORY
            / "workspaces/aware_workspace/modules/workspace/libs/workspace_operator/python/aware_workspace_operator/commit.py"
        ).read_text()
    )
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        for node in ast.walk(tree)
    )
