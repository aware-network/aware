from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "aware_goal_operational_runtime"
ALLOWED_TOP_LEVEL_IMPORTS = {
    "__future__",
    "collections",
    "dataclasses",
    "enum",
    "hashlib",
    "json",
    "re",
    "threading",
    "typing",
}


def test_runtime_has_no_non_stdlib_imports() -> None:
    violations: list[str] = []
    for path in sorted(SOURCE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".", 1)[0]]
            else:
                continue
            for name in names:
                if name not in ALLOWED_TOP_LEVEL_IMPORTS:
                    violations.append(f"{path.name}:{node.lineno}:{name}")
    assert violations == []


def test_package_imports_without_site_packages() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            (
                "import sys; "
                f"sys.path.insert(0, {str(PACKAGE_ROOT)!r}); "
                "import aware_goal_operational_runtime as runtime; "
                "assert runtime.CODEC_VERSION == 1"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_package_manifest_declares_no_runtime_dependencies() -> None:
    manifest = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "dependencies = []" in manifest
    for forbidden in (
        "aware-goal-service",
        "aware-meta",
        "aware-service",
        "aware-dev",
        "aware-workspace",
        "pydantic",
        "sqlalchemy",
    ):
        assert forbidden not in manifest.casefold()
