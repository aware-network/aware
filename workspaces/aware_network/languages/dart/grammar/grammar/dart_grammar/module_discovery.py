"""Dart-specific code module discovery (canonical, aware_code-based)."""

import re
from pathlib import Path
from typing_extensions import override

from aware_code.module.discovery import CodeModuleDiscovery


class DartCodeModuleDiscovery(CodeModuleDiscovery):
    """Detect Dart packages by locating `pubspec.yaml` roots."""

    _NAME_RX: re.Pattern[str] = re.compile(r"^\s*name\s*:\s*([A-Za-z0-9_\-]+)\s*$")

    @override
    def is_module_root(self, path: Path, workspace_root: Path) -> bool:
        abs_path = workspace_root / path
        if not abs_path.is_dir():
            return False
        return (abs_path / "pubspec.yaml").exists()

    @override
    def get_module_name(self, module_path: Path, workspace_root: Path) -> str:
        abs_path = workspace_root / module_path
        pubspec = abs_path / "pubspec.yaml"
        if pubspec.exists():
            try:
                for line in pubspec.read_text(encoding="utf-8").splitlines():
                    m = self._NAME_RX.match(line)
                    if m:
                        return m.group(1).strip()
            except Exception:
                pass
        return module_path.name
