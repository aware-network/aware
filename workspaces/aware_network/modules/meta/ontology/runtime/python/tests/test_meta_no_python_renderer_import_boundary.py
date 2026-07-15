from __future__ import annotations

import ast
from pathlib import Path


def test_aware_meta_production_modules_do_not_import_python_grammar() -> None:
    aware_meta_root = Path(__file__).resolve().parents[1] / "aware_meta"
    violations: list[str] = []

    for path in sorted(aware_meta_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_python_grammar_import(alias.name):
                        violations.append(_violation(path, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None and _is_python_grammar_import(node.module):
                    violations.append(_violation(path, node.module))

    assert violations == []


def test_core_provider_generated_materialization_renderers_are_not_owned_by_meta() -> (
    None
):
    aware_meta_root = Path(__file__).resolve().parents[1] / "aware_meta"
    forbidden_renderer_modules = (
        aware_meta_root
        / "attribute"
        / "config"
        / "deltas"
        / "generated_materialization.py",
        aware_meta_root
        / "class_"
        / "config"
        / "deltas"
        / "generated_materialization.py",
        aware_meta_root
        / "class_"
        / "config"
        / "relationship"
        / "deltas"
        / "generated_materialization.py",
    )

    assert [path for path in forbidden_renderer_modules if path.exists()] == []


def _is_python_grammar_import(module: str) -> bool:
    return module == "python_grammar" or module.startswith("python_grammar.")


def _violation(path: Path, module: str) -> str:
    return f"{path.relative_to(Path.cwd()).as_posix()} imports {module}"
