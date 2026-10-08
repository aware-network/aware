from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_declares_zero_dependencies() -> None:
    manifest = tomllib.loads((_PACKAGE_ROOT / "pyproject.toml").read_text())
    assert manifest["project"]["dependencies"] == []


def test_runtime_imports_only_standard_library_and_itself() -> None:
    import_roots: set[str] = set()
    for path in (_PACKAGE_ROOT / "aware_specification_runtime").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                import_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                import_roots.add(node.module.split(".")[0])
    assert import_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "enum",
        "hashlib",
        "json",
        "typing",
        "unicodedata",
    }


def test_clean_import_loads_no_parser_orm_or_graph_runtime() -> None:
    script = f"""
import sys
sys.path.insert(0, {_PACKAGE_ROOT.as_posix()!r})
import aware_specification_runtime
for forbidden in ('tree_sitter', 'sqlalchemy', 'aware_orm', 'aware_ontology'):
    assert not any(name == forbidden or name.startswith(forbidden + '.') for name in sys.modules)
"""
    subprocess.run([sys.executable, "-I", "-c", script], check=True)
