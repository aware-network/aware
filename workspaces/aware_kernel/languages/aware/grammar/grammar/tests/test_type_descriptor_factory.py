"""Validation tests for Aware Type Descriptor Factory mapping."""

from aware_grammar.type_descriptor_adapter import AwareTypeDescriptorAdapter
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_code.type_descriptor_nodes import TypeNodeKind

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)

from aware_meta.fqn_resolver import FqnScope, NamespacePath
from aware_meta.attribute.config.type_descriptor_builder import build_type_descriptor


def test_factory_mapping_enum_and_vector():
    plugin = AWARE_CODE_PLUGIN
    ns = NamespacePath(package="tests", namespace="aware.default")
    enum = EnumConfig(name="CodeLanguage", description="Code language", enum_fqn=ns.fqn("CodeLanguage"))
    enums_by_fqn = {ns.fqn(enum.name): enum}
    d_enum = build_type_descriptor(
        type_descriptor_adapter=plugin.type_descriptor_adapter,
        primitive_codec=plugin.primitive_codec,
        fqn_scope=FqnScope(namespace=ns, classes_by_fqn={}, enums_by_fqn=enums_by_fqn),
        type_text="CodeLanguage",
    )

    assert d_enum.kind == Kind.enum and d_enum.enum_config is enum

    d_enum_list = build_type_descriptor(
        type_descriptor_adapter=plugin.type_descriptor_adapter,
        primitive_codec=plugin.primitive_codec,
        fqn_scope=FqnScope(namespace=ns, classes_by_fqn={}, enums_by_fqn=enums_by_fqn),
        type_text="CodeLanguage[]",
    )
    assert d_enum_list.kind == Kind.collection and d_enum_list.collection_kind == AttributeCollectionType.list
    assert d_enum_list.child_links
    child_link = d_enum_list.child_links[0]
    assert child_link is not None
    assert child_link.role == Role.element
    assert child_link.child is not None
    assert child_link.child.kind == Kind.enum

    d_vec = build_type_descriptor(
        type_descriptor_adapter=plugin.type_descriptor_adapter,
        primitive_codec=plugin.primitive_codec,
        fqn_scope=FqnScope(namespace=ns, classes_by_fqn={}, enums_by_fqn=enums_by_fqn),
        type_text="Vector(1536)",
    )
    assert d_vec.kind == Kind.primitive
    assert d_vec.primitive_config is not None
    ptype = d_vec.primitive_config.primitive_type
    assert ptype is not None
    assert ptype.base_type == CodePrimitiveBaseType.vector
    assert ptype.constraints is not None
    assert ptype.constraints["dimension"] == 1536


def test_factory_mapping_tuple():
    adapter = AwareTypeDescriptorAdapter()
    tuple_node = adapter.parse_type("(User, Post, Comment)")
    assert tuple_node.kind == TypeNodeKind.TUPLE
    assert len(tuple_node.elements) == 3

    named_tuple = adapter.parse_type("(user: User, post: Post)")
    assert [elem.label for elem in named_tuple.elements] == ["user", "post"]
    assert [elem.text for elem in named_tuple.elements] == ["User", "Post"]

    plugin = AWARE_CODE_PLUGIN
    fqn_scope = FqnScope(
        namespace=NamespacePath(package="tests", namespace="aware.default"), classes_by_fqn={}, enums_by_fqn={}
    )
    descriptor = build_type_descriptor(
        type_descriptor_adapter=plugin.type_descriptor_adapter,
        primitive_codec=plugin.primitive_codec,
        fqn_scope=fqn_scope,
        type_text="(name: String, count: Int, ok: Bool)",
    )
    assert descriptor.kind == Kind.tuple
    links = descriptor.child_links
    assert len(links) == 3
    assert [link.position for link in links] == [1, 2, 3]
