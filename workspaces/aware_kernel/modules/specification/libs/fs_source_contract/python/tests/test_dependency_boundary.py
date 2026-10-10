from __future__ import annotations

import ast
from pathlib import Path


def test_package_has_only_standard_library_imports() -> None:
    package = Path(__file__).parents[1] / "aware_specification_fs_source_contract"
    allowed = {
        "__future__",
        "dataclasses",
        "enum",
        "hashlib",
        "json",
        "re",
        "typing",
        "unicodedata",
    }
    imported: set[str] = set()
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])
    assert imported <= allowed


def test_distribution_declares_zero_runtime_dependencies() -> None:
    manifest = (Path(__file__).parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert "dependencies = []" in manifest
