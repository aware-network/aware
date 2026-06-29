from __future__ import annotations

from pathlib import Path

# Aware Content
from aware_content.builder import get_text

# Code Runtime
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter

# Aware ORM
from aware_orm.session.autobind import disable_autobind

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.class_.class_config import ClassConfig

# Aware Meta
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

# Dart Grammar
from dart_grammar.renderer import DartRenderer, _DiscriminatedUnion, _DiscriminatedUnionVariant
from dart_grammar_test_support import make_class


class _TestDartLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return self.base_dir / f"{class_config.name}.dart"

    def get_enum_file_path(self, enum_config) -> Path:
        return self.base_dir / "enums.dart"

    def get_function_file_path(self, function_config) -> Path:
        return self.base_dir / "functions.dart"

    def get_file_extension(self) -> str:
        return ".dart"

    def get_module_import_path(self, file_path: Path) -> str:
        return f"package:test/{file_path.name}"


def test_dart_renderer_emits_export_stub_for_variant_only_files(tmp_path: Path) -> None:
    """
    When a discriminated-union variant is placed in its own file by the layout strategy,
    the Dart renderer must not emit an empty file.

    Freezed requires variants to be declared alongside the union base, so the variant-only
    file should export the base module to preserve stable import paths.
    """
    layout = _TestDartLayoutStrategy(base_dir=tmp_path)
    renderer = DartRenderer(layout_strategy=layout)

    with disable_autobind():
        base_cls = make_class(name="EnvironmentServiceOperation")
        variant_cls = make_class(
            name="InferenceServiceOperation",
            parent_class=base_cls,
            parent_class_id=base_cls.id,
        )

    renderer._discriminated_unions_by_base_id = {  # type: ignore[attr-defined]
        base_cls.id: _DiscriminatedUnion(
            base_class=base_cls,
            discriminator="service",
            variants=[_DiscriminatedUnionVariant(class_config=variant_cls, tag_value="inference")],
        )
    }
    renderer._discriminated_union_base_id_by_variant_id = {variant_cls.id: base_cls.id}  # type: ignore[attr-defined]

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file([variant_cls], writer)

    dart_source = get_text(code.content_part_text)
    assert "export 'package:test/EnvironmentServiceOperation.dart';" in dart_source
    assert "@freezed" not in dart_source
