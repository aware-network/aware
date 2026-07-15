from __future__ import annotations

import ast
from pathlib import Path


EVALUATOR_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "aware_reactivity"
    / "condition"
    / "evaluator.py"
)
REACTIVITY_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_reactivity_package_has_no_deprecated_runtime_dependency() -> None:
    assert "aware-" + "runtime" not in REACTIVITY_PYPROJECT.read_text(encoding="utf-8")


def test_condition_evaluator_has_no_direct_deprecated_runtime_imports() -> None:
    source = EVALUATOR_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

    assert "aware_meta.runtime.handler_executor.contracts" in imports
    assert all(module.split(".", 1)[0] != "aware_" + "runtime" for module in imports)
    assert "aware_" + "runtime" not in source
