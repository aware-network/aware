from __future__ import annotations

from pathlib import Path

import pytest

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
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from dart_grammar.renderer import DartRenderer
from dart_grammar_test_support import (
    class_attr_link,
    make_attribute,
    make_class,
    make_enum,
)


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


def _primitive_attribute(
    *,
    name: str,
    owner_key: str,
    base_type: CodePrimitiveBaseType,
    default_value: str,
) -> AttributeConfig:
    primitive = build_code_primitive_type(base_type=base_type)
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


def _enum_attribute(
    *,
    name: str,
    owner_key: str,
    enum_config: EnumConfig,
    default_value: str,
) -> AttributeConfig:
    descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.enum,
        enum_config=enum_config,
        enum_config_id=enum_config.id,
    )
    return make_attribute(
        name=name,
        owner_key=owner_key,
        is_required=True,
        default_value=default_value,
        type_descriptor=descriptor,
    )


def _render(*, tmp_path: Path, default_status: str = '"unresolved"') -> str:
    status = make_enum(name="ResolutionStatus")
    status.enum_options = [
        EnumOption(enum_config_id=status.id, value="unresolved", position=0),
        EnumOption(enum_config_id=status.id, value="resolved", position=1),
    ]
    request = make_class(name="Request")
    attributes = [
        _primitive_attribute(
            name="operation",
            owner_key=request.class_fqn,
            base_type=CodePrimitiveBaseType.string,
            default_value='"enter_app_screen"',
        ),
        _primitive_attribute(
            name="protocol_version",
            owner_key=request.class_fqn,
            base_type=CodePrimitiveBaseType.integer,
            default_value="1",
        ),
        _primitive_attribute(
            name="ratio",
            owner_key=request.class_fqn,
            base_type=CodePrimitiveBaseType.float,
            default_value="1.5",
        ),
        _primitive_attribute(
            name="accepted",
            owner_key=request.class_fqn,
            base_type=CodePrimitiveBaseType.boolean,
            default_value="true",
        ),
        _primitive_attribute(
            name="evidence",
            owner_key=request.class_fqn,
            base_type=CodePrimitiveBaseType.json,
            default_value="{}",
        ),
        _primitive_attribute(
            name="amount",
            owner_key=request.class_fqn,
            base_type=CodePrimitiveBaseType.decimal,
            default_value='"1.23"',
        ),
        _enum_attribute(
            name="status",
            owner_key=request.class_fqn,
            enum_config=status,
            default_value=default_status,
        ),
    ]
    request.class_config_attribute_configs = [
        class_attr_link(request, attribute, position=position) for position, attribute in enumerate(attributes)
    ]

    renderer = DartRenderer(layout_strategy=_Layout(base_dir=tmp_path))
    code = renderer.create_empty_code()
    with CodeSectionWriter(
        code,
        CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    ) as writer:
        renderer.emit_file([status, request], writer)
    return get_text(code.content_part_text)


def test_dart_renderer_forwards_authored_defaults_into_required_factory(
    tmp_path: Path,
) -> None:
    source = _render(tmp_path=tmp_path)

    assert "String? operation" in source
    assert "int? protocolVersion" in source
    assert "double? ratio" in source
    assert "bool? accepted" in source
    assert "Map<String, dynamic>? evidence" in source
    assert "AwareDecimal? amount" in source
    assert "ResolutionStatus? status" in source
    assert "operation: operation ?? 'enter_app_screen'" in source
    assert "protocolVersion: protocolVersion ?? 1" in source
    assert "ratio: ratio ?? 1.5" in source
    assert "accepted: accepted ?? true" in source
    assert "evidence: evidence ?? {}" in source
    assert "amount: amount ?? AwareDecimal.parse('1.23')" in source
    assert "status: status ?? ResolutionStatus.unresolved" in source


def test_dart_renderer_applies_wire_defaults_with_dart_literals(tmp_path: Path) -> None:
    source = _render(tmp_path=tmp_path)

    assert "if (!json.containsKey('operation')) 'operation': 'enter_app_screen'" in source
    assert "if (!json.containsKey('protocol_version')) 'protocol_version': 1" in source
    assert "if (!json.containsKey('ratio')) 'ratio': 1.5" in source
    assert "if (!json.containsKey('accepted')) 'accepted': true" in source
    assert "if (!json.containsKey('evidence')) 'evidence': {}" in source
    assert "if (!json.containsKey('amount')) 'amount': '1.23'" in source
    assert "if (!json.containsKey('status')) 'status': 'unresolved'" in source
    assert "True" not in source


def test_dart_renderer_rejects_unknown_enum_default(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown Dart enum default 'missing'"):
        _render(tmp_path=tmp_path, default_status='"missing"')
