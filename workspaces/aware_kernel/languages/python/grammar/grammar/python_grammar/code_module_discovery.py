"""Python-specific code module discovery implementation."""

import re
from pathlib import Path

from aware_code.module.discovery import CodeModuleDiscovery
from aware_utils.logging import logger
from typing_extensions import override


class PythonCodeModuleDiscovery(CodeModuleDiscovery):
    """
    Python-specific module discovery implementation.

    Detects Python packages and modules based on:
    - pyproject.toml files (modern Python packaging)
    - setup.py files (legacy Python packaging)
    - __init__.py files (Python packages)
    """

    @override
    def is_module_root(self, path: Path, workspace_root: Path) -> bool:
        """
        Check if a directory is a Python module root.

        A directory is considered a Python module root if it contains:
        1. pyproject.toml (modern Python packaging)
        2. setup.py (legacy Python packaging)
        3. __init__.py (Python package) AND is not nested inside another module

        Args:
            path: Directory path to check (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            True if this directory is a Python module root
        """
        abs_path = workspace_root / path

        if not abs_path.is_dir():
            return False

        # Check for explicit packaging files
        if (abs_path / "pyproject.toml").exists():
            return True

        if (abs_path / "setup.py").exists():
            return True

        # Check for __init__.py (Python package)
        if (abs_path / "__init__.py").exists():
            # Make sure it's not nested inside another module
            return not self._is_inside_other_module(path, workspace_root)

        return False

    @override
    def get_module_name(self, module_path: Path, workspace_root: Path) -> str:
        """
        Extract the canonical module name from a Python module root.

        Priority order:
        1. name from pyproject.toml [tool.poetry.name] or [project.name]
        2. name from setup.py
        3. directory name (fallback)

        CRITICAL: Normalizes to Python import conventions (underscores) for consistency.

        Args:
            module_path: Path to the module root directory (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            Canonical module name with Python import conventions (underscores)
        """
        abs_path = workspace_root / module_path

        # Try pyproject.toml first
        pyproject_path = abs_path / "pyproject.toml"
        if pyproject_path.exists():
            module_name = self._extract_name_from_pyproject(pyproject_path)
            if module_name:
                # CRITICAL FIX: Normalize to Python import conventions
                return self._normalize_module_name(module_name)

        # Try setup.py
        setup_path = abs_path / "setup.py"
        if setup_path.exists():
            module_name = self._extract_name_from_setup_py(setup_path)
            if module_name:
                # CRITICAL FIX: Normalize to Python import conventions
                return self._normalize_module_name(module_name)

        # Fallback to directory name
        # CRITICAL FIX: Normalize directory name too
        return self._normalize_module_name(module_path.name)

    @override
    def get_entry_points(self, module_path: Path, workspace_root: Path) -> list[Path]:
        """
        Identify entry point files for a Python module.

        For Python, entry points are typically __init__.py files.

        Args:
            module_path: Path to the module root directory (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            List of entry point file paths relative to workspace root
        """
        entry_points: list[Path] = []

        # Check for __init__.py in the module root
        init_path = module_path / "__init__.py"
        abs_init_path = workspace_root / init_path
        if abs_init_path.exists():
            entry_points.append(init_path)

        return entry_points

    @override
    def get_metadata(self, module_path: Path, workspace_root: Path) -> dict[str, object]:
        """
        Extract metadata about the Python module.

        Args:
            module_path: Path to the module root directory (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            Dictionary of metadata key-value pairs
        """
        metadata: dict[str, object] = {}
        abs_path = workspace_root / module_path

        # Extract metadata from pyproject.toml
        pyproject_path = abs_path / "pyproject.toml"
        if pyproject_path.exists():
            pyproject_metadata = self._extract_metadata_from_pyproject(pyproject_path)
            metadata.update(pyproject_metadata)

        # Extract metadata from setup.py
        setup_path = abs_path / "setup.py"
        if setup_path.exists():
            setup_metadata = self._extract_metadata_from_setup_py(setup_path)
            metadata.update(setup_metadata)

        # Add module type information
        if pyproject_path.exists():
            metadata["package_type"] = "pyproject"
        elif setup_path.exists():
            metadata["package_type"] = "setuptools"
        else:
            metadata["package_type"] = "package"

        return metadata

    def _normalize_module_name(self, name: str) -> str:
        """
        Normalize module name to Python import conventions.

        Converts hyphens to underscores for consistency with Python import system.

        Args:
            name: Original module name (may contain hyphens)

        Returns:
            Normalized module name with underscores
        """
        return name.replace("-", "_")

    def _is_inside_other_module(self, path: Path, workspace_root: Path) -> bool:
        """
        Check if a path is inside another Python module root.

        This prevents nested packages from being detected as separate modules
        unless they have their own pyproject.toml or setup.py.

        Args:
            path: Path to check (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            True if this path is inside another module root
        """
        # Check all parent directories
        for parent in path.parents:
            if parent == Path("."):
                break

            parent_abs = workspace_root / parent

            # If parent has pyproject.toml or setup.py, it's a module root
            if (parent_abs / "pyproject.toml").exists() or (parent_abs / "setup.py").exists():
                return True

        return False

    def _extract_name_from_pyproject(self, pyproject_path: Path) -> str | None:
        """
        Extract module name from pyproject.toml file.

        Looks for [tool.poetry.name] or [project.name].

        Args:
            pyproject_path: Path to pyproject.toml file

        Returns:
            Module name if found, None otherwise
        """
        try:
            content = pyproject_path.read_text(encoding="utf-8")

            # Look for [tool.poetry] section
            poetry_match = re.search(r'\[tool\.poetry\].*?name\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
            if poetry_match:
                return poetry_match.group(1)

            # Look for [project] section
            project_match = re.search(r'\[project\].*?name\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
            if project_match:
                return project_match.group(1)

        except Exception as e:
            logger.warning(f"Failed to parse pyproject.toml at {pyproject_path}: {e}")

        return None

    def _extract_name_from_setup_py(self, setup_path: Path) -> str | None:
        """
        Extract module name from setup.py file.

        Looks for name= parameter in setup() call.

        Args:
            setup_path: Path to setup.py file

        Returns:
            Module name if found, None otherwise
        """
        try:
            content = setup_path.read_text(encoding="utf-8")

            # Look for setup(name="...") or setup(name='...')
            name_match = re.search(r'setup\s*\([^)]*name\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
            if name_match:
                return name_match.group(1)

        except Exception as e:
            logger.warning(f"Failed to parse setup.py at {setup_path}: {e}")

        return None

    def _extract_metadata_from_pyproject(self, pyproject_path: Path) -> dict[str, object]:
        """
        Extract metadata from pyproject.toml file.

        Args:
            pyproject_path: Path to pyproject.toml file

        Returns:
            Dictionary of metadata
        """
        metadata: dict[str, object] = {}

        try:
            content = pyproject_path.read_text(encoding="utf-8")

            # Extract version
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                metadata["version"] = version_match.group(1)

            # Extract description
            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if desc_match:
                metadata["description"] = desc_match.group(1)

            # Extract author
            author_match = re.search(r'author\s*=\s*["\']([^"\']+)["\']', content)
            if author_match:
                metadata["author"] = author_match.group(1)

        except Exception as e:
            logger.warning(f"Failed to extract metadata from pyproject.toml at {pyproject_path}: {e}")

        return metadata

    def _extract_metadata_from_setup_py(self, setup_path: Path) -> dict[str, object]:
        """
        Extract metadata from setup.py file.

        Args:
            setup_path: Path to setup.py file

        Returns:
            Dictionary of metadata
        """
        metadata: dict[str, object] = {}

        try:
            content = setup_path.read_text(encoding="utf-8")

            # Extract version
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                metadata["version"] = version_match.group(1)

            # Extract description
            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if desc_match:
                metadata["description"] = desc_match.group(1)

            # Extract author
            author_match = re.search(r'author\s*=\s*["\']([^"\']+)["\']', content)
            if author_match:
                metadata["author"] = author_match.group(1)

        except Exception as e:
            logger.warning(f"Failed to extract metadata from setup.py at {setup_path}: {e}")

        return metadata
