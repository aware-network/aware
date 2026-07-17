from __future__ import annotations

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[8]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_INTERFACE_RUNTIME_ROOT_STR = str(
    _REPO_ROOT
    / "workspaces"
    / "aware_network"
    / "modules"
    / "interface"
    / "ontology"
    / "runtime"
    / "python"
)
if _INTERFACE_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _INTERFACE_RUNTIME_ROOT_STR)

from aware_interface.semantic_scope import load_interface_semantic_scope  # noqa: E402


def _write_experience_package(root: Path) -> Path:
    package_root = root / "experiences" / "home_story"
    package_root.mkdir(parents=True, exist_ok=True)
    manifest_path = package_root / "aware.experience.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "home-story"',
                'fqn_prefix = "home_story"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                'environment_handle = "demo"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "story.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "    observable security {",
                "        view door default api_view home_devices.security_door {}",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest_path


def _write_pane_package(root: Path) -> Path:
    package_root = root / "panes" / "door_control"
    package_root.mkdir(parents=True, exist_ok=True)
    manifest_path = package_root / "aware.pane.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware_pane = 1",
                "",
                "[pane]",
                'package_name = "door-control-pane"',
                'fqn_prefix = "aware_door_control_pane"',
                'pane_name = "door_control"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                "[[dependencies]]",
                'package_name = "home-story"',
                'kind = "experience_package"',
                "",
                "[python]",
                'package_path = "python/aware_door_control_pane"',
                'import_root = "aware_door_control_pane"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "door_control.aware").write_text(
        "\n".join(
            [
                "pane door_control {",
                "    kind door",
                "    view home_story.security.door default {}",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest_path


def _write_interface_package(root: Path) -> Path:
    package_root = root / "interfaces" / "aware_app"
    package_root.mkdir(parents=True, exist_ok=True)
    manifest_path = package_root / "aware.interface.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware_interface = 1",
                "",
                "[interface]",
                'package_name = "aware-app-interface"',
                'fqn_prefix = "aware_app_interface"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
                'config_bundle_path = "bundles/interface.config.bundle.json"',
                "",
                "[[dependencies]]",
                'package_name = "home-story"',
                'kind = "experience_package"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "app.aware").write_text(
        "\n".join(
            [
                "interface aware_app {",
                "    window main {",
                "        layout scene {",
                "            section body",
                "        }",
                "    }",
                "    pane door_control {",
                "        mount main.scene.body",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest_path


def _write_workspace_manifest(root: Path) -> Path:
    manifest_path = root / "aware.workspace.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "demo"',
                "environments = []",
                "services = []",
                'experiences = ["experiences/home_story/aware.experience.toml"]',
                'apis = ["apis/home_devices/aware.api.toml"]',
                'panes = ["panes/door_control/aware.pane.toml"]',
                'interfaces = ["interfaces/aware_app/aware.interface.toml"]',
                "nodes = []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_load_interface_semantic_scope_for_interface_manifest(tmp_path: Path) -> None:
    _write_workspace_manifest(tmp_path)
    _write_experience_package(tmp_path)
    _write_pane_package(tmp_path)
    interface_manifest = _write_interface_package(tmp_path)

    scope = load_interface_semantic_scope(manifest_path=interface_manifest)

    assert scope.package_kind == "interface"
    assert scope.manifest_path == interface_manifest.resolve()
    assert scope.interface_dependency_scope is not None
    assert (
        scope.interface_dependency_scope.interface_package_name == "aware-app-interface"
    )
    assert scope.interface_dependency_scope.declared_experience_package_names == (
        "home-story",
    )
    assert "home_story" in scope.interface_dependency_scope.experience_catalog
    assert scope.pane_catalog_resolution is not None
    assert scope.pane_catalog_resolution.declared_workspace is False
    pane_entry = scope.pane_catalog_entry(pane_name="door_control")
    assert pane_entry is not None
    assert pane_entry.view_refs == ("home_story.security.door",)
    assert scope.pane_consumer_scopes(pane_name="door_control") == ()


def test_load_interface_semantic_scope_for_pane_manifest(tmp_path: Path) -> None:
    _write_workspace_manifest(tmp_path)
    _write_experience_package(tmp_path)
    pane_manifest = _write_pane_package(tmp_path)
    _write_interface_package(tmp_path)

    scope = load_interface_semantic_scope(manifest_path=pane_manifest)

    assert scope.package_kind == "pane"
    assert scope.manifest_path == pane_manifest.resolve()
    assert scope.interface_dependency_scope is None
    assert scope.pane_catalog_resolution is None
    consumer_scopes = scope.pane_consumer_scopes(pane_name="door_control")
    assert len(consumer_scopes) == 1
    consumer_scope = consumer_scopes[0]
    assert consumer_scope.interface_name == "aware_app"
    assert consumer_scope.interface_package_name == "aware-app-interface"
    assert consumer_scope.declared_experience_package_names == ("home-story",)
    assert "home_story" in consumer_scope.experience_catalog
