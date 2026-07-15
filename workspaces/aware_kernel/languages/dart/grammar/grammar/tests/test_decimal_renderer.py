from __future__ import annotations

from pathlib import Path

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_content.builder import get_text
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from dart_grammar.renderer import DartRenderer
from dart_grammar.renderer_materialization import DartMaterializationRenderer
from dart_grammar_test_support import class_attr_link, make_attribute, make_class


class _Layout(ObjectConfigGraphRenderLayoutStrategy):
    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return self.base_dir / f"{class_config.name}.dart"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return self.base_dir / f"{enum_config.name}.dart"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return self.base_dir / "functions.dart"

    def get_file_extension(self) -> str:
        return ".dart"


def _decimal_attribute(
    *,
    name: str,
    owner_key: str,
    default_value: str | None = None,
) -> AttributeConfig:
    primitive = build_code_primitive_type(base_type=CodePrimitiveBaseType.decimal)
    primitive_config = PrimitiveConfig(
        primitive_type=primitive,
        primitive_type_id=primitive.id,
    )
    descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
    )
    return make_attribute(
        name=name,
        owner_key=owner_key,
        is_required=True,
        default_value=default_value,
        type_descriptor=descriptor,
    )


def test_dart_renderer_emits_exact_decimal_type_wire_and_default(
    tmp_path: Path,
) -> None:
    account = make_class(name="Account")
    balance = _decimal_attribute(
        name="opening_balance",
        owner_key=account.class_fqn,
        default_value='"1.23"',
    )
    account.class_config_attribute_configs = [
        class_attr_link(account, balance, position=0)
    ]

    renderer = DartRenderer(layout_strategy=_Layout(base_dir=tmp_path))
    code = renderer.create_empty_code()
    with CodeSectionWriter(
        code,
        CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    ) as writer:
        renderer.emit_file([account], writer)

    source = get_text(code.content_part_text)
    assert "package:aware_model_helpers/converters.dart" in source
    assert "@AwareDecimalConverter() required AwareDecimal openingBalance" in source
    assert "AwareDecimal? openingBalance" in source
    assert "openingBalance: openingBalance ?? AwareDecimal.parse('1.23')" in source
    assert (
        "if (!json.containsKey('opening_balance')) 'opening_balance': '1.23'" in source
    )
    assert "double openingBalance" not in source


def test_dart_oig_materialization_preserves_decimal_wire_text(
    tmp_path: Path,
) -> None:
    balance = _decimal_attribute(
        name="balance",
        owner_key="aware_test.account",
    )
    renderer = DartMaterializationRenderer(layout_strategy=_Layout(base_dir=tmp_path))

    assert renderer._leaf_decoder_name(balance, optional=False) == "decodeString"
    assert renderer._leaf_decoder_name(balance, optional=True) == "decodeStringOrNull"
