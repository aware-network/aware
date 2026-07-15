from __future__ import annotations

import ast
from pathlib import Path


_PYTHON_ROOT = Path(__file__).resolve().parents[2]
_META_RUNTIME_ROOT = _PYTHON_ROOT / "aware_meta"
_SHARED_SPAN_HELPER = (
    _META_RUNTIME_ROOT
    / "materialization"
    / "deltas"
    / "generated_materialization_spans.py"
)
_DIRECT_RENDER_DTO_CONSTRUCTORS = frozenset(
    {
        "CodeGrammarAnchorRenderReplacement",
        "CodeGrammarAnchorRenderSource",
        "CodeGrammarAnchorRenderSpanTarget",
    }
)
_DIRECT_SOURCE_SPAN_IMPORTS = frozenset(
    {
        "CodeGrammarAnchorRenderSource",
        "CodeGrammarAnchorRenderSpanTarget",
    }
)


def test_meta_generated_materialization_text_span_dto_construction_is_shared() -> None:
    offenders: list[str] = []
    for source_path in _generated_materialization_sources():
        if source_path == _SHARED_SPAN_HELPER:
            continue
        module = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if _imports_direct_source_span_dto(node):
                offenders.append(_location(source_path=source_path, node=node))
            constructor_name = _constructor_call_name(node)
            if constructor_name in _DIRECT_RENDER_DTO_CONSTRUCTORS:
                offenders.append(
                    f"{_location(source_path=source_path, node=node)} "
                    f"calls {constructor_name}"
                )

    assert offenders == []


def _generated_materialization_sources() -> tuple[Path, ...]:
    return tuple(
        sorted(
            source_path
            for source_path in _META_RUNTIME_ROOT.rglob("*generated_materialization*.py")
            if "__pycache__" not in source_path.parts
        )
    )


def _imports_direct_source_span_dto(node: ast.AST) -> bool:
    if not isinstance(node, ast.ImportFrom):
        return False
    return any(
        alias.name in _DIRECT_SOURCE_SPAN_IMPORTS
        for alias in node.names
    )


def _constructor_call_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


def _location(*, source_path: Path, node: ast.AST) -> str:
    relative_path = source_path.relative_to(_PYTHON_ROOT)
    return f"{relative_path}:{getattr(node, 'lineno', 0)}"
