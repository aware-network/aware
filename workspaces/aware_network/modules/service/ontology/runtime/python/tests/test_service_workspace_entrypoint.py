from __future__ import annotations

from pathlib import Path

import pytest
from aware_service_runtime.workspace import ServiceWorkspace


def _write_service_toml(root: Path) -> Path:
    toml_path = root / "aware.service.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "home-story-service"',
                'fqn_prefix = "aware_home_story_service"',
                "",
                "[build]",
                'sources_dir = "services/bindings"',
                'include_paths = ["**/*.aware"]',
                'exclude_paths = ["ignore/*.aware"]',
                "",
                "[[dependencies]]",
                'package_name = "home-story-api"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_service_sources(root: Path) -> None:
    bindings = root / "services" / "bindings"
    (bindings / "ignore").mkdir(parents=True, exist_ok=True)
    _ = (bindings / "home.services.aware").write_text(
        "\n".join(
            [
                "service home_story {",
                "    api home_story_api;",
                "",
                "    operation open_door {",
                "        endpoint home_story_api.door.open;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (bindings / "ignore" / "scratch.services.aware").write_text(
        "service ignored {}\n",
        encoding="utf-8",
    )
    _ = (bindings / "README.txt").write_text("not-aware\n", encoding="utf-8")


def test_service_workspace_builds_snapshot(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_service_toml(root)
    _write_service_sources(root)

    snapshot = ServiceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()

    assert snapshot.spec.service.package_name == "home-story-service"
    assert snapshot.spec.service.fqn_prefix == "aware_home_story_service"
    assert snapshot.spec.dependencies[0].package_name == "home-story-api"
    assert snapshot.source_files == (Path("services/bindings/home.services.aware"),)


def test_service_workspace_prefers_nested_workspace_root_over_legacy_environment_root(
    tmp_path: Path,
) -> None:
    checkout_root = tmp_path / "checkout"
    workspace_root = checkout_root / "workspaces" / "aware_network"
    service_root = workspace_root / "modules" / "hub" / "services" / "hub"
    checkout_root.mkdir(parents=True)
    workspace_root.mkdir(parents=True)
    (checkout_root / "aware.environment.toml").write_text(
        "aware_environment = 1\n",
        encoding="utf-8",
    )
    (workspace_root / "aware.workspace.toml").write_text(
        "aware_workspace = 1\n",
        encoding="utf-8",
    )
    service_root.mkdir(parents=True)
    toml_path = _write_service_toml(service_root)
    _write_service_sources(service_root)

    snapshot = ServiceWorkspace.from_toml(toml_path=toml_path).build_snapshot()

    assert snapshot.repo_root == workspace_root.resolve()
    assert snapshot.package_root == service_root.resolve()
    assert snapshot.source_files == (Path("services/bindings/home.services.aware"),)


def test_service_workspace_requires_existing_sources_dir(tmp_path: Path) -> None:
    toml_path = _write_service_toml(tmp_path)

    with pytest.raises(FileNotFoundError, match="Service sources_dir does not exist"):
        _ = ServiceWorkspace.from_toml(
            toml_path=toml_path, repo_root=tmp_path
        ).build_snapshot()
