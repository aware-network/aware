"""Dart-specific code package discovery implementation."""

import re
from pathlib import Path

from typing_extensions import override

from aware_code.package.discovery import CodePackageDiscovery


class DartCodePackageDiscovery(CodePackageDiscovery):
    """Discover Dart packages from `pubspec.yaml` manifests."""

    _NAME_RX: re.Pattern[str] = re.compile(r"^name:\s*([^\s#\n]+)", re.MULTILINE)
    _VERSION_RX: re.Pattern[str] = re.compile(r"^version:\s*([^\s#\n]+)", re.MULTILINE)
    _DESCRIPTION_RX: re.Pattern[str] = re.compile(r"^description:\s*([^\n]+)", re.MULTILINE)
    _AUTHOR_RX: re.Pattern[str] = re.compile(r"^author:\s*([^\n]+)", re.MULTILINE)

    @override
    def is_package_root(self, path: Path, workspace_root: Path) -> bool:
        abs_path = workspace_root / path
        if not abs_path.is_dir():
            return False
        return (abs_path / "pubspec.yaml").exists()

    @override
    def get_package_name(self, package_path: Path, workspace_root: Path) -> str:
        if not self.is_package_root(package_path, workspace_root):
            raise ValueError(f"Not a Dart package root: {package_path}")

        pubspec_path = workspace_root / package_path / "pubspec.yaml"
        try:
            content = pubspec_path.read_text(encoding="utf-8")
        except Exception:
            return package_path.name

        name_match = self._NAME_RX.search(content)
        if name_match:
            return name_match.group(1).strip()
        return package_path.name

    @override
    def get_manifest_path(self, package_path: Path, workspace_root: Path) -> Path:
        abs_path = workspace_root / package_path
        if (abs_path / "pubspec.yaml").exists():
            return package_path / "pubspec.yaml"
        raise ValueError(f"No pubspec.yaml found at {package_path}")

    @override
    def get_metadata(self, package_path: Path, workspace_root: Path) -> dict[str, object]:
        pubspec_path = workspace_root / self.get_manifest_path(package_path, workspace_root)
        metadata: dict[str, object] = {
            "package_type": "dart_package",
            "manifest_kind": "pubspec_yaml",
            "code_package_surface": "runtime",
        }

        try:
            content = pubspec_path.read_text(encoding="utf-8")
        except Exception:
            return metadata

        version_match = self._VERSION_RX.search(content)
        if version_match:
            metadata["version"] = version_match.group(1).strip()

        description_match = self._DESCRIPTION_RX.search(content)
        if description_match:
            metadata["description"] = description_match.group(1).strip()

        author_match = self._AUTHOR_RX.search(content)
        if author_match:
            metadata["author"] = author_match.group(1).strip()

        if "flutter:" in content:
            metadata["flutter_package"] = "true"

        metadata["manifest_kind"] = "pubspec_yaml"
        metadata["code_package_surface"] = "runtime"
        return metadata
