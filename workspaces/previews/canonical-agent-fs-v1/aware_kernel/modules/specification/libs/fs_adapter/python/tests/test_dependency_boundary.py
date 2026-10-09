from __future__ import annotations

import ast
from pathlib import Path


def test_runtime_dependency_boundary() -> None:
    package = Path(__file__).parents[1] / "aware_specification_fs_adapter"
    allowed = {
        "aware_specification_fs_source_contract",
        "aware_specification_runtime",
        "jsonschema",
    }
    standard = {
        "__future__",
        "dataclasses",
        "enum",
        "fcntl",
        "hashlib",
        "json",
        "os",
        "re",
        "stat",
        "threading",
        "tomllib",
        "types",
        "typing",
        "unicodedata",
    }
    foreign: set[str] = set()
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                foreign.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                foreign.add(node.module.split(".")[0])
    assert foreign <= allowed | standard
