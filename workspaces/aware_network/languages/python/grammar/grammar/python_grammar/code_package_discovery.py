"""Python-specific code package discovery implementation."""

import re
from pathlib import Path

from typing_extensions import override

from aware_code.package.manifest_loader import load_pyproject_package_manager_metadata
from aware_code.package.discovery import CodePackageDiscovery
from python_grammar.code_module_discovery import PythonCodeModuleDiscovery


class PythonCodePackageDiscovery(CodePackageDiscovery):
    """Discover Python packages from explicit packaging manifests only."""

    _SETUP_NAME_RX: re.Pattern[str] = re.compile(r'setup\s*\([^)]*name\s*=\s*["\']([^"\']+)["\']', re.DOTALL)
    _POETRY_NAME_RX: re.Pattern[str] = re.compile(r'\[tool\.poetry\].*?name\s*=\s*["\']([^"\']+)["\']', re.DOTALL)
    _PROJECT_NAME_RX: re.Pattern[str] = re.compile(r'\[project\].*?name\s*=\s*["\']([^"\']+)["\']', re.DOTALL)

    def __init__(self) -> None:
        self._module_discovery: PythonCodeModuleDiscovery = PythonCodeModuleDiscovery()

    @override
    def is_package_root(self, path: Path, workspace_root: Path) -> bool:
        abs_path = workspace_root / path
        if not abs_path.is_dir():
            return False
        return (abs_path / "pyproject.toml").exists() or (abs_path / "setup.py").exists()

    @override
    def get_package_name(self, package_path: Path, workspace_root: Path) -> str:
        abs_path = workspace_root / package_path

        pyproject_path = abs_path / "pyproject.toml"
        if pyproject_path.exists():
            package_name = self._extract_name_from_pyproject(pyproject_path)
            if package_name:
                return package_name

        setup_path = abs_path / "setup.py"
        if setup_path.exists():
            package_name = self._extract_name_from_setup_py(setup_path)
            if package_name:
                return package_name

        if not self.is_package_root(package_path, workspace_root):
            raise ValueError(f"Not a Python package root: {package_path}")

        return package_path.name

    @override
    def get_manifest_path(self, package_path: Path, workspace_root: Path) -> Path:
        abs_path = workspace_root / package_path
        if (abs_path / "pyproject.toml").exists():
            return package_path / "pyproject.toml"
        if (abs_path / "setup.py").exists():
            return package_path / "setup.py"
        raise ValueError(f"No Python package manifest found at {package_path}")

    @override
    def get_metadata(self, package_path: Path, workspace_root: Path) -> dict[str, object]:
        manifest_path = self.get_manifest_path(package_path, workspace_root)
        metadata = self._module_discovery.get_metadata(package_path, workspace_root)
        metadata["manifest_kind"] = "pyproject_toml" if manifest_path.name == "pyproject.toml" else "setup_py"
        metadata["code_package_surface"] = "runtime"
        if manifest_path.name == "pyproject.toml":
            try:
                metadata.update(
                    load_pyproject_package_manager_metadata(
                        toml_path=workspace_root / manifest_path,
                        package_name=self.get_package_name(package_path, workspace_root),
                    )
                )
            except Exception:
                pass
        return metadata

    def _extract_name_from_pyproject(self, pyproject_path: Path) -> str | None:
        try:
            content = pyproject_path.read_text(encoding="utf-8")
        except Exception:
            return None

        poetry_match = self._POETRY_NAME_RX.search(content)
        if poetry_match:
            return poetry_match.group(1)

        project_match = self._PROJECT_NAME_RX.search(content)
        if project_match:
            return project_match.group(1)

        return None

    def _extract_name_from_setup_py(self, setup_path: Path) -> str | None:
        try:
            content = setup_path.read_text(encoding="utf-8")
        except Exception:
            return None

        name_match = self._SETUP_NAME_RX.search(content)
        if name_match:
            return name_match.group(1)

        return None
