from __future__ import annotations

import re
from pathlib import Path

from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from python_grammar.renderer import PythonRenderer
from python_grammar_test_support import function_owner_key, make_class, make_function


class _TestLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("default") / "models.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        return ".".join(p for p in parts if p).strip(".")


def test_python_renderer_emits_multiline_function_docstring_as_triple_quotes() -> None:
    cls = make_class(name="Thing", is_base=True)
    fn = make_function(
        name="do",
        owner_key=function_owner_key(cls),
        description="Line1\nLine2",
        is_async=True,
        kind=FunctionKind.instance,
    )
    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=fn,
            function_config_id=fn.id,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file([cls, fn], writer, schema="default", class_to_class_config_map={cls.id: cls})

    out = writer.code.content_part_text.inline_text or ""
    compile(out, "generated.py", "exec")  # ensure render output is syntactically valid

    # Multiline descriptions should be readable docstrings, not escaped "\n" string literals.
    assert not re.search(r'\s+async def do\(self\) -> None:\n\s+"Line1\\nLine2"\n', out)
    assert re.search(r'\s+async def do\(self\) -> None:\n\s+"""\n\s+Line1\n\s+Line2\n\s+"""\n', out)


def test_python_renderer_wraps_long_function_docstring_lines() -> None:
    cls = make_class(name="Thing", is_base=True)
    fn = make_function(
        name="do",
        owner_key=function_owner_key(cls),
        description=(
            "Validates a settlement and materializes a deterministic smart-contract settlement receipt, "
            "without finalizing reservation."
        ),
        is_async=True,
        kind=FunctionKind.instance,
    )
    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=fn,
            function_config_id=fn.id,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file([cls, fn], writer, schema="default", class_to_class_config_map={cls.id: cls})

    out = writer.code.content_part_text.inline_text or ""
    compile(out, "generated.py", "exec")

    assert (
        '"""Validates a settlement and materializes a deterministic smart-contract settlement receipt, '
        'without finalizing reservation."""'
    ) not in out
    assert re.search(
        r'async def do\(self\) -> None:\n'
        r'\s+"""\n'
        r'\s+Validates a settlement and materializes a deterministic smart-contract settlement receipt, without\n'
        r'\s+finalizing reservation\.\n'
        r'\s+"""',
        out,
    )
