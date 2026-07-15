"""Tests for Python package discovery functionality."""

from pathlib import Path

import pytest

from python_grammar.code_language_plugin import PYTHON_CODE_PLUGIN
from python_grammar.code_package_discovery import PythonCodePackageDiscovery


class TestPythonCodePackageDiscovery:
    """Test cases for PythonCodePackageDiscovery."""

    @pytest.fixture
    def discovery(self) -> PythonCodePackageDiscovery:
        return PythonCodePackageDiscovery()

    def create_file(self, workspace: Path, file_path: str, content: str) -> None:
        full_path = workspace / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        _ = full_path.write_text(content, encoding="utf-8")

    def test_pyproject_package_detection(self, discovery: PythonCodePackageDiscovery, tmp_path: Path) -> None:
        pyproject_content = """
[tool.poetry]
name = "my-awesome-package"
version = "1.0.0"
description = "An awesome Python package"
author = "Test Author"
"""
        self.create_file(tmp_path, "my_package/pyproject.toml", pyproject_content)
        self.create_file(tmp_path, "my_package/__init__.py", "# Package init")

        package_path = Path("my_package")
        assert discovery.is_package_root(package_path, tmp_path) is True
        assert discovery.get_package_name(package_path, tmp_path) == "my-awesome-package"
        assert discovery.get_manifest_path(package_path, tmp_path) == Path("my_package/pyproject.toml")

        metadata = discovery.get_metadata(package_path, tmp_path)
        assert metadata["package_type"] == "pyproject"
        assert metadata["manifest_kind"] == "pyproject_toml"
        assert metadata["code_package_surface"] == "runtime"
        assert metadata["version"] == "1.0.0"

    def test_setup_py_package_detection(self, discovery: PythonCodePackageDiscovery, tmp_path: Path) -> None:
        setup_content = """
from setuptools import setup

setup(
    name="legacy-package",
    version="2.1.0",
)
"""
        self.create_file(tmp_path, "legacy_pkg/setup.py", setup_content)
        self.create_file(tmp_path, "legacy_pkg/__init__.py", "# Legacy package")

        package_path = Path("legacy_pkg")
        assert discovery.is_package_root(package_path, tmp_path) is True
        assert discovery.get_package_name(package_path, tmp_path) == "legacy-package"
        assert discovery.get_manifest_path(package_path, tmp_path) == Path("legacy_pkg/setup.py")

        metadata = discovery.get_metadata(package_path, tmp_path)
        assert metadata["package_type"] == "setuptools"
        assert metadata["manifest_kind"] == "setup_py"
        assert metadata["code_package_surface"] == "runtime"

    def test_init_py_only_is_not_canonical_package_root(
        self,
        discovery: PythonCodePackageDiscovery,
        tmp_path: Path,
    ) -> None:
        self.create_file(tmp_path, "simple_package/__init__.py", "# Simple package")

        package_path = Path("simple_package")
        assert discovery.is_package_root(package_path, tmp_path) is False

    def test_plugin_discovers_root_package_from_manifest_file_tree(self, tmp_path: Path) -> None:
        pyproject_content = """
[project]
name = "workspace-root-package"
version = "0.1.0"
"""
        self.create_file(tmp_path, "pyproject.toml", pyproject_content)
        self.create_file(tmp_path, "src/demo/__init__.py", "# Demo")

        packages = PYTHON_CODE_PLUGIN.discover_packages(
            file_tree={
                "pyproject.toml": pyproject_content,
                "src/demo/__init__.py": "# Demo",
            },
            workspace_root=tmp_path,
        )

        assert len(packages) == 1
        package = packages[0]
        assert package.name == "workspace-root-package"
        assert package.root_path == Path(".")
        assert package.manifest_path == Path("pyproject.toml")
        assert package.metadata["manifest_kind"] == "pyproject_toml"
        assert package.metadata["code_package_surface"] == "runtime"
