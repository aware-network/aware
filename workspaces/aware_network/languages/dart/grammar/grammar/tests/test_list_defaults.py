from __future__ import annotations

from pathlib import Path

# Aware Content
from aware_content.builder import get_text

# Code Runtime
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

# Aware Meta
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

# Dart Grammar
from dart_grammar.renderer import DartRenderer
from dart_grammar_test_support import class_attr_link, make_attribute, make_class


class _TestDartLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
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


def _list_descriptor(child: AttributeTypeDescriptor) -> AttributeTypeDescriptor:
    list_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.collection,
        collection_kind=AttributeCollectionType.list,
    )
    list_desc.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=list_desc.id,
            child=child,
            child_id=child.id,
            role=AttributeTypeDescriptorRole.element,
        )
    )
    return list_desc


def test_dart_renderer_defaults_list_fields_to_empty(tmp_path: Path) -> None:
    """
    Lists are non-nullable in canonical Aware. Dart should default list fields to empty
    rather than marking them required or nullable.
    """
    layout = _TestDartLayoutStrategy(base_dir=tmp_path)
    renderer = DartRenderer(layout_strategy=layout)

    prim = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    prim_cfg = PrimitiveConfig(primitive_type=prim, primitive_type_id=prim.id)
    prim_leaf = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=prim_cfg,
        primitive_config_id=prim_cfg.id,
    )
    group_cls = make_class(name="Group")
    tags_attr = make_attribute(
        name="tags",
        owner_key=group_cls.class_fqn,
        is_required=True,
        type_descriptor=_list_descriptor(prim_leaf),
    )

    member_cls = make_class(name="Member")
    class_leaf = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config=member_cls,
        class_config_id=member_cls.id,
    )
    members_attr = make_attribute(
        name="members",
        owner_key=group_cls.class_fqn,
        is_required=True,
        type_descriptor=_list_descriptor(class_leaf),
    )

    group_cls.class_config_attribute_configs = [
        class_attr_link(group_cls, tags_attr, position=0),
        class_attr_link(group_cls, members_attr, position=1),
    ]

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file([member_cls, group_cls], writer)

    dart_source = get_text(code.content_part_text)
    assert "@Default(const []) List<String> tags" in dart_source
    assert "@Default(const []) List<Member> members" in dart_source
    assert "List<String> tags = const []" in dart_source
    assert "List<Member> members = const []" in dart_source
    assert "required List<String>" not in dart_source
    assert "required List<Member>" not in dart_source
    assert "List<String>?" not in dart_source
    assert "List<Member>?" not in dart_source
