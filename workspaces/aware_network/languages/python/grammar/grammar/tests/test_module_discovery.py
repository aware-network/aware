"""Tests for Python module discovery functionality."""

import tempfile
import pytest
from pathlib import Path

from python_grammar.code_module_discovery import PythonCodeModuleDiscovery


class TestPythonCodeModuleDiscovery:
    """Test cases for PythonCodeModuleDiscovery."""

    @pytest.fixture
    def discovery(self):
        """Create a PythonCodeModuleDiscovery instance."""
        return PythonCodeModuleDiscovery()

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def create_file(self, workspace: Path, file_path: str, content: str):
        """Helper to create a file with content in the workspace."""
        full_path = workspace / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    def test_pyproject_toml_module_detection(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test module detection via pyproject.toml file."""
        # Create a module with pyproject.toml
        pyproject_content = """
[tool.poetry]
name = "my-awesome-package"
version = "1.0.0"
description = "An awesome Python package"
author = "Test Author"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
        self.create_file(temp_workspace, "my_package/pyproject.toml", pyproject_content)
        self.create_file(temp_workspace, "my_package/__init__.py", "# Package init")

        # Test detection
        module_path = Path("my_package")
        assert discovery.is_module_root(module_path, temp_workspace)

        # Test name extraction
        assert discovery.get_module_name(module_path, temp_workspace) == "my_awesome_package"

        # Test metadata extraction
        metadata = discovery.get_metadata(module_path, temp_workspace)
        assert metadata["version"] == "1.0.0"
        assert metadata["description"] == "An awesome Python package"
        assert metadata["author"] == "Test Author"
        assert metadata["package_type"] == "pyproject"

    def test_setup_py_module_detection(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test module detection via setup.py file."""
        # Create a module with setup.py
        setup_content = """
from setuptools import setup, find_packages

setup(
    name="legacy-package",
    version="2.1.0",
    description="A legacy Python package",
    author="Legacy Author",
    packages=find_packages(),
)
"""
        self.create_file(temp_workspace, "legacy_pkg/setup.py", setup_content)
        self.create_file(temp_workspace, "legacy_pkg/__init__.py", "# Legacy package")

        # Test detection
        module_path = Path("legacy_pkg")
        assert discovery.is_module_root(module_path, temp_workspace)

        # Test name extraction
        assert discovery.get_module_name(module_path, temp_workspace) == "legacy_package"

        # Test metadata extraction
        metadata = discovery.get_metadata(module_path, temp_workspace)
        assert metadata["version"] == "2.1.0"
        assert metadata["description"] == "A legacy Python package"
        assert metadata["author"] == "Legacy Author"
        assert metadata["package_type"] == "setuptools"

    def test_init_py_module_detection(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test module detection via __init__.py file (without explicit packaging)."""
        # Create a simple Python package
        self.create_file(temp_workspace, "simple_package/__init__.py", "# Simple package")
        self.create_file(temp_workspace, "simple_package/module.py", "def hello(): pass")

        # Test detection
        module_path = Path("simple_package")
        assert discovery.is_module_root(module_path, temp_workspace)

        # Test name fallback to directory name
        assert discovery.get_module_name(module_path, temp_workspace) == "simple_package"

        # Test metadata
        metadata = discovery.get_metadata(module_path, temp_workspace)
        assert metadata["package_type"] == "package"

    def test_nested_module_prevention(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test that nested packages inside explicit modules are not detected separately."""
        # Create parent module with pyproject.toml
        pyproject_content = """
[tool.poetry]
name = "parent-package"
version = "1.0.0"
"""
        self.create_file(temp_workspace, "parent/pyproject.toml", pyproject_content)
        self.create_file(temp_workspace, "parent/__init__.py", "# Parent package")

        # Create nested package (should not be detected as separate module)
        self.create_file(temp_workspace, "parent/subpackage/__init__.py", "# Sub package")

        # Parent should be detected
        parent_path = Path("parent")
        assert discovery.is_module_root(parent_path, temp_workspace)

        # Nested package should NOT be detected as separate module
        nested_path = Path("parent/subpackage")
        assert not discovery.is_module_root(nested_path, temp_workspace)

    def test_nested_module_with_explicit_packaging(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test that nested packages with their own pyproject.toml ARE detected."""
        # Create parent module
        parent_pyproject = """
[tool.poetry]
name = "parent-package"
version = "1.0.0"
"""
        self.create_file(temp_workspace, "parent/pyproject.toml", parent_pyproject)
        self.create_file(temp_workspace, "parent/__init__.py", "# Parent")

        # Create nested module with its own pyproject.toml
        nested_pyproject = """
[tool.poetry]
name = "nested-package"
version = "2.0.0"
"""
        self.create_file(temp_workspace, "parent/nested/pyproject.toml", nested_pyproject)
        self.create_file(temp_workspace, "parent/nested/__init__.py", "# Nested")

        # Both should be detected
        parent_path = Path("parent")
        nested_path = Path("parent/nested")

        assert discovery.is_module_root(parent_path, temp_workspace)
        assert discovery.is_module_root(nested_path, temp_workspace)

        assert discovery.get_module_name(parent_path, temp_workspace) == "parent_package"
        assert discovery.get_module_name(nested_path, temp_workspace) == "nested_package"

    def test_entry_points_detection(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test entry points detection for Python modules."""
        # Create module with __init__.py
        self.create_file(temp_workspace, "test_pkg/__init__.py", "# Package init")
        self.create_file(temp_workspace, "test_pkg/module.py", "def test(): pass")

        module_path = Path("test_pkg")
        entry_points = discovery.get_entry_points(module_path, temp_workspace)

        assert len(entry_points) == 1
        assert entry_points[0] == Path("test_pkg/__init__.py")

    def test_project_section_pyproject_toml(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test pyproject.toml with [project] section instead of [tool.poetry]."""
        pyproject_content = """
[project]
name = "modern-package"
version = "3.0.0"
description = "A modern Python package using PEP 621"
authors = ["Modern Author <author@example.com>"]

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
"""
        self.create_file(temp_workspace, "modern_pkg/pyproject.toml", pyproject_content)
        self.create_file(temp_workspace, "modern_pkg/__init__.py", "# Modern package")

        module_path = Path("modern_pkg")
        assert discovery.is_module_root(module_path, temp_workspace)
        assert discovery.get_module_name(module_path, temp_workspace) == "modern_package"

        metadata = discovery.get_metadata(module_path, temp_workspace)
        assert metadata["version"] == "3.0.0"
        assert metadata["description"] == "A modern Python package using PEP 621"

    def test_no_module_detection(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test that directories without module markers are not detected."""
        # Create just a regular directory with Python files
        self.create_file(temp_workspace, "regular_dir/script.py", "print('hello')")
        self.create_file(temp_workspace, "regular_dir/utils.py", "def util(): pass")

        module_path = Path("regular_dir")
        assert not discovery.is_module_root(module_path, temp_workspace)

    def test_priority_order_pyproject_over_setup(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test that pyproject.toml takes priority over setup.py for name extraction."""
        # Create both pyproject.toml and setup.py
        pyproject_content = """
[tool.poetry]
name = "pyproject-name"
version = "1.0.0"
"""
        setup_content = """
setup(
    name="setup-name",
    version="2.0.0",
)
"""
        self.create_file(temp_workspace, "dual_pkg/pyproject.toml", pyproject_content)
        self.create_file(temp_workspace, "dual_pkg/setup.py", setup_content)
        self.create_file(temp_workspace, "dual_pkg/__init__.py", "# Dual package")

        module_path = Path("dual_pkg")

        # Should prioritize pyproject.toml name
        assert discovery.get_module_name(module_path, temp_workspace) == "pyproject_name"

        # Metadata should merge from both sources
        metadata = discovery.get_metadata(module_path, temp_workspace)
        assert metadata["package_type"] == "pyproject"  # pyproject takes precedence

    def test_malformed_files_fallback(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test graceful handling of malformed pyproject.toml/setup.py files."""
        # Create malformed pyproject.toml
        malformed_content = """
[tool.poetry
name = "broken-toml"  # Missing closing bracket
version = "1.0.0"
"""
        self.create_file(temp_workspace, "broken_pkg/pyproject.toml", malformed_content)
        self.create_file(temp_workspace, "broken_pkg/__init__.py", "# Broken package")

        module_path = Path("broken_pkg")

        # Should still detect as module
        assert discovery.is_module_root(module_path, temp_workspace)

        # Should fallback to directory name
        assert discovery.get_module_name(module_path, temp_workspace) == "broken_pkg"

    def test_edge_case_empty_init_py(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test detection with empty __init__.py file."""
        # Create empty __init__.py
        self.create_file(temp_workspace, "empty_init/__init__.py", "")

        module_path = Path("empty_init")
        assert discovery.is_module_root(module_path, temp_workspace)
        assert discovery.get_module_name(module_path, temp_workspace) == "empty_init"

    def test_file_instead_of_directory(self, discovery: PythonCodeModuleDiscovery, temp_workspace: Path):
        """Test that files are not detected as module roots."""
        # Create a Python file (not directory)
        self.create_file(temp_workspace, "script.py", "print('hello')")

        file_path = Path("script.py")
        assert not discovery.is_module_root(file_path, temp_workspace)


class TestPythonModuleDiscoveryIntegration:
    """Integration tests that simulate real-world scenarios."""

    @pytest.fixture
    def complex_workspace(self):
        """Create a complex workspace with multiple module types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Main application package
            self.create_file(
                workspace,
                "myapp/pyproject.toml",
                """
[tool.poetry]
name = "myapp"
version = "1.0.0"
description = "Main application"
""",
            )
            self.create_file(workspace, "myapp/__init__.py", "# Main app")
            self.create_file(workspace, "myapp/core.py", "# Core module")

            # Legacy utility package
            self.create_file(
                workspace,
                "utils/setup.py",
                """
setup(
    name="utils",
    version="0.1.0",
)
""",
            )
            self.create_file(workspace, "utils/__init__.py", "# Utils")

            # Simple package without explicit packaging
            self.create_file(workspace, "helpers/__init__.py", "# Helpers")
            self.create_file(workspace, "helpers/string_utils.py", "# String utilities")

            # Nested package within myapp (should not be detected separately)
            self.create_file(workspace, "myapp/submodule/__init__.py", "# Submodule")

            # Regular scripts directory (should not be detected)
            self.create_file(workspace, "scripts/deploy.py", "# Deployment script")

            yield workspace

    def create_file(self, workspace: Path, file_path: str, content: str):
        """Helper to create a file with content."""
        full_path = workspace / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    def test_complex_workspace_discovery(self, complex_workspace: Path):
        """Test module discovery in a complex workspace."""
        discovery = PythonCodeModuleDiscovery()

        # Test each expected module
        expected_modules = [
            ("myapp", "myapp", "pyproject"),
            ("utils", "utils", "setuptools"),
            ("helpers", "helpers", "package"),
        ]

        for module_dir, expected_name, expected_type in expected_modules:
            module_path = Path(module_dir)

            # Should be detected as module
            assert discovery.is_module_root(module_path, complex_workspace), f"{module_dir} should be detected"

            # Should have correct name
            name = discovery.get_module_name(module_path, complex_workspace)
            assert name == expected_name, f"Expected {expected_name}, got {name}"

            # Should have correct metadata
            metadata = discovery.get_metadata(module_path, complex_workspace)
            assert metadata["package_type"] == expected_type

        # Test that non-modules are not detected
        non_modules = ["scripts", "myapp/submodule"]
        for non_module in non_modules:
            assert not discovery.is_module_root(
                Path(non_module), complex_workspace
            ), f"{non_module} should not be detected"

    def test_workspace_with_no_modules(self):
        """Test workspace with no Python modules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create some non-module files
            self.create_file(workspace, "README.md", "# Project")
            self.create_file(workspace, "config.yaml", "setting: value")
            self.create_file(workspace, "data/sample.json", '{"key": "value"}')

            discovery = PythonCodeModuleDiscovery()

            # No directories should be detected as modules
            for path in ["README.md", "config.yaml", "data"]:
                assert not discovery.is_module_root(Path(path), workspace)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
