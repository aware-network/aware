"""Tests for Dart package discovery functionality."""

from pathlib import Path

from dart_grammar.code_language_plugin import DART_CODE_PLUGIN
from dart_grammar.code_package_discovery import DartCodePackageDiscovery


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(content, encoding="utf-8")


def test_dart_package_discovery_from_pubspec(tmp_path: Path) -> None:
    discovery = DartCodePackageDiscovery()
    _write(
        tmp_path / "demo_app" / "pubspec.yaml",
        "\n".join(
            [
                "name: demo_app",
                "version: 1.2.3",
                "description: Demo package",
                "",
            ]
        ),
    )
    _write(tmp_path / "demo_app" / "lib" / "demo_app.dart", "library demo_app;\n")

    package_path = Path("demo_app")
    assert discovery.is_package_root(package_path, tmp_path) is True
    assert discovery.get_package_name(package_path, tmp_path) == "demo_app"
    assert discovery.get_manifest_path(package_path, tmp_path) == Path("demo_app/pubspec.yaml")

    metadata = discovery.get_metadata(package_path, tmp_path)
    assert metadata["package_type"] == "dart_package"
    assert metadata["manifest_kind"] == "pubspec_yaml"
    assert metadata["code_package_surface"] == "runtime"
    assert metadata["version"] == "1.2.3"


def test_dart_plugin_discovers_root_package_from_manifest_file_tree(tmp_path: Path) -> None:
    pubspec_content = "\n".join(
        [
            "name: workspace_demo",
            "version: 0.0.1",
            "description: Workspace root package",
            "",
        ]
    )
    _write(tmp_path / "pubspec.yaml", pubspec_content)
    _write(tmp_path / "lib" / "workspace_demo.dart", "library workspace_demo;\n")

    packages = DART_CODE_PLUGIN.discover_packages(
        file_tree={
            "pubspec.yaml": pubspec_content,
            "lib/workspace_demo.dart": "library workspace_demo;\n",
        },
        workspace_root=tmp_path,
    )

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "workspace_demo"
    assert package.root_path == Path(".")
    assert package.manifest_path == Path("pubspec.yaml")
    assert package.metadata["manifest_kind"] == "pubspec_yaml"
    assert package.metadata["code_package_surface"] == "runtime"
