from __future__ import annotations

from pathlib import Path

from aware_workspace_operator.models import WorkspaceBootstrapOptions
from aware_workspace_operator.pipeline.utils import resolve_repo_root
from aware_workspace_operator.pipeline.stages.preflight import run_preflight_stage


def test_full_local_preflight_accepts_workspace_package_manifest_layout(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"

    _write(
        repo_root / "modules/api/aware.module.toml",
        """
        aware = 1

        [[packages]]
        id = "ontology"
        kind = "ontology"
        manifest = "ontology/aware.ontology.toml"
        visibility = "module"

        [[packages]]
        id = "api_service_api"
        kind = "api"
        manifest = "apis/api/aware.api.toml"
        visibility = "module"

        [[packages]]
        id = "runtime"
        kind = "runtime"
        manifest = "ontology/runtime/python/pyproject.toml"
        visibility = "module"
        """,
    )
    _write(
        repo_root / "modules/api/ontology/aware.ontology.toml",
        """
        aware_ontology = 1

        [ontology]
        package_name = "api-ontology"

        [[dependencies]]
        package_name = "meta-ontology"

        [[dependencies]]
        package_name = "code-ontology"
        """,
    )
    _write(
        repo_root / "modules/api/apis/api/aware.api.toml",
        """
        aware_api = 1

        [api]
        package_name = "api-service-api"

        [[dependencies]]
        package_name = "api-service-dto"
        """,
    )
    _write(
        repo_root / "modules/api/apis/api/dto/aware.toml",
        """
        aware = 1

        [package]
        package_name = "api-service-dto"
        fqn_prefix = "aware_api_service_dto"
        kind = "ontology"
        """,
    )
    _write(
        repo_root / "modules/api/ontology/runtime/python/pyproject.toml",
        """
        [project]
        name = "aware-api-runtime"
        version = "0.0.0"
        """,
    )
    _write(
        repo_root / "modules/api/ontology/structure/aware.workflows.toml",
        """
        aware = 1

        [workflow]
        mode = "build"
        module_toml_path = "modules/api/aware.module.toml"
        """,
    )
    _write_package(
        repo_root / "modules/meta/ontology/aware.ontology.toml", "meta-ontology"
    )
    _write_package(
        repo_root / "modules/code/ontology/aware.ontology.toml", "code-ontology"
    )

    preflight = run_preflight_stage(
        request=WorkspaceBootstrapOptions(
            repo_root=repo_root,
            bootstrap_mode="full-local",
            requested_module_ids=("api",),
        ),
        repo_root=repo_root,
    )

    assert preflight.has_errors is False
    assert preflight.missing_dependencies == []
    assert preflight.module_ids == ["api"]
    assert preflight.modules[0].errors == []
    assert preflight.modules[0].package_names == [
        "api-ontology",
        "api-service-api",
    ]


def test_full_local_preflight_does_not_use_environment_artifacts_for_closure(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"

    _write(
        repo_root / "modules/sample/aware.module.toml",
        """
        aware = 1

        [[packages]]
        id = "ontology"
        kind = "ontology"
        manifest = "structure/ontology/aware.toml"
        visibility = "module"
        """,
    )
    _write(
        repo_root / "modules/sample/structure/ontology/aware.toml",
        """
        aware = 1

        [package]
        package_name = "sample-ontology"
        fqn_prefix = "aware_sample"
        kind = "ontology"

        [[dependencies]]
        package_name = "retired-artifact-only"
        """,
    )
    _write(
        repo_root / "modules/sample/structure/aware.workflows.toml",
        """
        aware = 1

        [workflow]
        mode = "build"
        module_toml_path = "modules/sample/aware.module.toml"
        """,
    )
    _write_package(
        repo_root / "targets/retired-artifact/sample/aware.toml",
        "retired-artifact-only",
    )

    preflight = run_preflight_stage(
        request=WorkspaceBootstrapOptions(
            repo_root=repo_root,
            bootstrap_mode="full-local",
            requested_module_ids=("sample",),
        ),
        repo_root=repo_root,
    )

    assert preflight.has_errors is False
    assert [
        item.dependency_package_name for item in preflight.missing_dependencies
    ] == ["retired-artifact-only"]


def test_resolve_repo_root_uses_explicit_env(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    monkeypatch.setenv("AWARE_WORKSPACE_OPERATOR_REPO_ROOT", str(repo_root))

    assert resolve_repo_root(raw_repo_root=None) == repo_root.resolve()
    assert repo_root.is_dir()


def test_resolve_repo_root_uses_aware_repo_anchor(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    nested = repo_root / "workspaces" / "aware_kernel" / "modules" / "storage"
    nested.mkdir(parents=True)
    _write_repo_anchor(repo_root)
    monkeypatch.chdir(nested)
    for env_name in (
        "AWARE_WORKSPACE_OPERATOR_REPO_ROOT",
        "AWARE_WORKSPACE_REPO_ROOT",
        "AWARE_REPO_ROOT",
        "AWARE_REPOSITORY_ROOT",
    ):
        monkeypatch.delenv(env_name, raising=False)

    assert resolve_repo_root(raw_repo_root=None, create_if_missing=False) == (
        repo_root.resolve()
    )


def test_resolve_repo_root_requires_explicit_input_or_anchor(
    monkeypatch,
    tmp_path: Path,
) -> None:
    for env_name in (
        "AWARE_WORKSPACE_OPERATOR_REPO_ROOT",
        "AWARE_WORKSPACE_REPO_ROOT",
        "AWARE_REPO_ROOT",
        "AWARE_REPOSITORY_ROOT",
    ):
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.chdir(tmp_path)

    try:
        resolve_repo_root(raw_repo_root=None)
    except RuntimeError as exc:
        assert "Workspace Operator repo root is required" in str(exc)
    else:
        raise AssertionError("resolve_repo_root should require an explicit root")


def _write_package(path: Path, package_name: str) -> None:
    _write(
        path,
        f"""
        aware_ontology = 1

        [ontology]
        package_name = "{package_name}"
        """,
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_strip_indent(text), encoding="utf-8")


def _write_repo_anchor(repo_root: Path) -> None:
    (repo_root / "workspaces").mkdir(parents=True, exist_ok=True)
    (repo_root / "aware.repo.toml").write_text(
        'aware_repo = 1\n\n[repo]\nhandle = "aware"\nworkspaces_dir = "workspaces"\n',
        encoding="utf-8",
    )


def _strip_indent(text: str) -> str:
    lines = text.strip().splitlines()
    return (
        "\n".join(line[8:] if line.startswith("        ") else line for line in lines)
        + "\n"
    )
