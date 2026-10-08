from __future__ import annotations

import ast
import tomllib
from pathlib import Path


def test_adapter_does_not_import_sdk_cli_service_or_experience() -> None:
    package_root = Path(__file__).parents[1] / "aware_protocol_fs_adapter"
    forbidden = (
        "aware_sdk",
        "aware_cli",
        "aware_service",
        "aware_environment",
        "aware_experience",
    )
    imported: set[str] = set()
    for path in package_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    assert not tuple(
        name for name in sorted(imported) if name.startswith(forbidden)
    )


def test_neutral_runtime_declares_no_runtime_dependencies() -> None:
    pyproject = Path(__file__).parents[3] / "runtime" / "python" / "pyproject.toml"
    source = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert source["project"]["dependencies"] == []
