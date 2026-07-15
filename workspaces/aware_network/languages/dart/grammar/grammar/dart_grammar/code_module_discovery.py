"""Dart-specific code module discovery implementation."""

import re
from pathlib import Path
from typing_extensions import override

from aware_code.module.discovery import CodeModuleDiscovery
from aware_utils.logging import logger


class DartCodeModuleDiscovery(CodeModuleDiscovery):
    """
    Dart-specific module discovery implementation.

    Detects Dart packages based on:
    - pubspec.yaml files (Dart/Flutter packages)
    """

    @override
    def is_module_root(self, path: Path, workspace_root: Path) -> bool:
        """
        Check if a directory is a Dart module root.

        A directory is considered a Dart module root if it contains a pubspec.yaml file.

        Args:
            path: Directory path to check (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            True if this directory is a Dart module root
        """
        abs_path = workspace_root / path

        if not abs_path.is_dir():
            return False

        # Check for pubspec.yaml (Dart package marker)
        return (abs_path / "pubspec.yaml").exists()

    @override
    def get_module_name(self, module_path: Path, workspace_root: Path) -> str:
        """
        Extract the canonical module name from a Dart module root.

        Reads the name field from pubspec.yaml, falls back to directory name.

        Args:
            module_path: Path to the module root directory (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            Canonical module name
        """
        abs_path = workspace_root / module_path

        # Try pubspec.yaml
        pubspec_path = abs_path / "pubspec.yaml"
        if pubspec_path.exists():
            module_name = self._extract_name_from_pubspec(pubspec_path)
            if module_name:
                return module_name

        # Fallback to directory name
        return module_path.name

    @override
    def get_entry_points(self, module_path: Path, workspace_root: Path) -> list[Path]:
        """
        Identify entry point files for a Dart module.

        For Dart packages, common entry points are:
        - lib/main.dart (main library)
        - lib/{package_name}.dart (library export file)

        Args:
            module_path: Path to the module root directory (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            List of entry point file paths relative to workspace root
        """
        entry_points: list[Path] = []

        # Check for lib/main.dart
        main_dart_path = module_path / "lib" / "main.dart"
        abs_main_dart = workspace_root / main_dart_path
        if abs_main_dart.exists():
            entry_points.append(main_dart_path)

        # Check for lib/{package_name}.dart
        package_name = self.get_module_name(module_path, workspace_root)
        package_dart_path = module_path / "lib" / f"{package_name}.dart"
        abs_package_dart = workspace_root / package_dart_path
        if abs_package_dart.exists():
            entry_points.append(package_dart_path)

        return entry_points

    @override
    def get_metadata(self, module_path: Path, workspace_root: Path) -> dict[str, object]:
        """
        Extract metadata about the Dart module.

        Args:
            module_path: Path to the module root directory (relative to workspace_root)
            workspace_root: Root path of the workspace

        Returns:
            Dictionary of metadata key-value pairs
        """
        metadata: dict[str, object] = {}
        abs_path = workspace_root / module_path

        # Extract metadata from pubspec.yaml
        pubspec_path = abs_path / "pubspec.yaml"
        if pubspec_path.exists():
            pubspec_metadata = self._extract_metadata_from_pubspec(pubspec_path)
            metadata.update(pubspec_metadata)

        # Add module type information
        metadata["package_type"] = "dart_package"

        return metadata

    def _extract_name_from_pubspec(self, pubspec_path: Path) -> str | None:
        """
        Extract package name from pubspec.yaml file.

        Args:
            pubspec_path: Path to pubspec.yaml file

        Returns:
            Package name if found, None otherwise
        """
        try:
            content = pubspec_path.read_text(encoding="utf-8")

            # Look for name: field (YAML format)
            name_match = re.search(r"^name:\s*([^\s#\n]+)", content, re.MULTILINE)
            if name_match:
                return name_match.group(1).strip()

        except Exception as e:
            logger.warning(f"Failed to parse pubspec.yaml at {pubspec_path}: {e}")

        return None

    def _extract_metadata_from_pubspec(self, pubspec_path: Path) -> dict[str, object]:
        """
        Extract metadata from pubspec.yaml file.

        Args:
            pubspec_path: Path to pubspec.yaml file

        Returns:
            Dictionary of metadata
        """
        metadata: dict[str, object] = {}

        try:
            content = pubspec_path.read_text(encoding="utf-8")

            # Extract version
            version_match = re.search(r"^version:\s*([^\s#\n]+)", content, re.MULTILINE)
            if version_match:
                metadata["version"] = version_match.group(1).strip()

            # Extract description
            desc_match = re.search(r"^description:\s*([^\n]+)", content, re.MULTILINE)
            if desc_match:
                metadata["description"] = desc_match.group(1).strip()

            # Extract author
            author_match = re.search(r"^author:\s*([^\n]+)", content, re.MULTILINE)
            if author_match:
                metadata["author"] = author_match.group(1).strip()

            # Check if it's a Flutter package
            if "flutter:" in content:
                metadata["flutter_package"] = "true"
                uses_material_design_match = re.search(
                    r"^\s*uses-material-design:\s*(true|false)\s*$",
                    content,
                    re.MULTILINE | re.IGNORECASE,
                )
                if uses_material_design_match:
                    metadata["uses_material_design"] = (
                        uses_material_design_match.group(1).strip().lower()
                    )

        except Exception as e:
            logger.warning(
                f"Failed to extract metadata from pubspec.yaml at {pubspec_path}: {e}"
            )

        return metadata
