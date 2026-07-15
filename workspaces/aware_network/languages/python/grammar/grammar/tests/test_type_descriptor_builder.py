"""Validation tests for Python Type Descriptor Adapter and Meta mapping."""

# Python Grammar
from python_grammar.type_descriptor_adapter import PythonTypeDescriptorAdapter
from python_grammar.code_language_plugin import PYTHON_CODE_PLUGIN

# Code Runtime
from aware_code.type_descriptor_nodes import TypeNodeKind
from aware_code.language.plugin import CodeLanguagePlugin
from aware_code.types import Json

# Kernel Graph Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.class_.class_config import ClassConfig

# Aware Kernel Meta
from aware_meta.attribute.config.type_descriptor_builder import build_type_descriptor
from aware_meta.fqn_resolver import FqnScope, NamespacePath
from python_grammar_test_support import make_class, make_enum


def build_type_descriptor_factory(
    plugin: CodeLanguagePlugin, fqn_scope: FqnScope, type_text: str
) -> AttributeTypeDescriptor:
    return build_type_descriptor(
        type_descriptor_adapter=plugin.type_descriptor_adapter,
        primitive_codec=plugin.primitive_codec,
        fqn_scope=fqn_scope,
        type_text=type_text,
    )


def test_factory_mapping_basic_structures():
    # Prepare plugin and enums
    plugin = PYTHON_CODE_PLUGIN
    enums = [make_enum(name="Status", package="tests", namespace="meta")]
    classes = [make_class(name="User", package="tests", namespace="meta", description="User class")]
    # Minimal FQN scope for tests: package/domain/schema are arbitrary but must be consistent.
    ns = NamespacePath(package="tests", namespace="meta.default")
    fqn_scope = FqnScope(
        namespace=ns,
        classes_by_fqn={ns.fqn(classes[0].name): classes[0]},
        enums_by_fqn={ns.fqn(enums[0].name): enums[0]},
    )

    # Primitive
    d_prim = build_type_descriptor_factory(plugin, fqn_scope, "int")
    assert d_prim.kind == Kind.primitive
    assert d_prim.primitive_config is not None

    # Collection list
    d_list = build_type_descriptor_factory(plugin, fqn_scope, "list[str]")
    assert d_list.kind == Kind.collection
    assert d_list.collection_kind == AttributeCollectionType.list
    assert len(d_list.child_links) == 1
    elem_link = d_list.child_links[0]
    assert elem_link.role == Role.element
    assert elem_link.child.kind == Kind.primitive

    # Mapping dict
    d_map = build_type_descriptor_factory(plugin, fqn_scope, "dict[str, int]")
    assert d_map.kind == Kind.mapping
    roles = {link.role for link in d_map.child_links}
    assert {Role.key, Role.value_}.issubset(roles)

    # Tuple
    d_tuple = build_type_descriptor_factory(plugin, fqn_scope, "tuple[str, int]")
    assert d_tuple.kind == Kind.tuple
    assert len(d_tuple.child_links) == 2
    assert {link.role for link in d_tuple.child_links} == {Role.member}
    assert {link.position for link in d_tuple.child_links} == {1, 2}

    # Union
    d_union = build_type_descriptor_factory(plugin, fqn_scope, "Union[str, int]")
    assert d_union.kind == Kind.union
    assert len(d_union.child_links) == 2
    assert {link.role for link in d_union.child_links} == {Role.member}

    # Enum by IDENT name
    d_enum = build_type_descriptor_factory(plugin, fqn_scope, "Status")
    assert d_enum.kind == Kind.enum
    assert d_enum.enum_config is enums[0]

    # Class by IDENT name
    d_class = build_type_descriptor_factory(plugin, fqn_scope, "User")
    assert d_class.kind == Kind.class_


def test_adapter_and_factory_vector_annotated():
    adapter = PythonTypeDescriptorAdapter()

    n_vec = adapter.parse_type("Annotated[Vector, VectorDim(768)]")
    assert n_vec.kind == TypeNodeKind.PRIMITIVE
    assert (n_vec.text or "").startswith("Vector(")

    plugin = PYTHON_CODE_PLUGIN
    ns = NamespacePath(package="tests", namespace="meta.default")
    fqn_scope = FqnScope(namespace=ns, classes_by_fqn={}, enums_by_fqn={})
    d_vec = build_type_descriptor_factory(plugin, fqn_scope, "Annotated[Vector, VectorDim(768)]")
    assert d_vec.kind == Kind.primitive
    assert d_vec.primitive_config is not None
    assert d_vec.primitive_config.primitive_type.base_type == CodePrimitiveBaseType.vector
    assert d_vec.primitive_config.primitive_type.constraints == Json({"dimension": 768})


def test_adapter_and_factory_json():
    adapter = PythonTypeDescriptorAdapter()

    # Adapter should recognize Json as primitive
    n_json = adapter.parse_type("Json")
    assert n_json.kind == TypeNodeKind.PRIMITIVE
    assert (n_json.text or "") == "Json"

    # Factory should map to BaseType.JSON in primitive payload
    plugin = PYTHON_CODE_PLUGIN
    ns = NamespacePath(package="tests", namespace="meta.default")
    fqn_scope = FqnScope(namespace=ns, classes_by_fqn={}, enums_by_fqn={})
    d_json = build_type_descriptor_factory(plugin, fqn_scope, "Json")
    assert d_json.kind == Kind.primitive
    assert d_json.primitive_config is not None
    assert d_json.primitive_config.primitive_type.base_type == CodePrimitiveBaseType.json


def test_literal_descriptor_maps_to_string_with_one_of():
    adapter = PythonTypeDescriptorAdapter()

    n_lit = adapter.parse_type("Literal['linear', 'exponential']")
    assert n_lit.kind == TypeNodeKind.PRIMITIVE

    plugin = PYTHON_CODE_PLUGIN
    ns = NamespacePath(package="tests", namespace="meta.default")
    fqn_scope = FqnScope(namespace=ns, classes_by_fqn={}, enums_by_fqn={})
    d_lit = build_type_descriptor_factory(plugin, fqn_scope, "Literal['linear', 'exponential']")
    assert d_lit.kind == Kind.primitive and d_lit.primitive_config is not None
    assert d_lit.primitive_config.primitive_type.base_type == CodePrimitiveBaseType.string
    assert d_lit.primitive_config.primitive_type.constraints == Json({"one_of": ["linear", "exponential"]})
