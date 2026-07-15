"""Validation tests for SQL canonical Type Descriptor builder mapping."""

from sql_grammar.code_language_plugin import SQL_CODE_PLUGIN

from aware_meta.attribute.config.type_descriptor_builder import build_type_descriptor
from aware_meta.fqn_resolver import FqnScope, NamespacePath

from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.enum.enum_config import EnumConfig


def test_sql_factory_enum_and_vector_mapping():
    plugin = SQL_CODE_PLUGIN
    ns = NamespacePath(package="tests", namespace="sql.public")
    enums = [
        EnumConfig(name="TransactionIntentStatus", description=None, enum_fqn=ns.fqn("TransactionIntentStatus")),
        EnumConfig(
            name="InterfaceOs",
            description=None,
            enum_fqn=f"{ns.package}.sql.interface.InterfaceOs",
        ),
        EnumConfig(
            name="InterfaceSessionState",
            description=None,
            enum_fqn=f"{ns.package}.sql.interface.InterfaceSessionState",
        ),
    ]
    enums_by_fqn = {
        # default schema: public
        ns.fqn("TransactionIntentStatus"): enums[0],
        # schema-qualified enums in `interface` schema
        f"{ns.package}.sql.interface.InterfaceOs": enums[1],
        f"{ns.package}.sql.interface.InterfaceSessionState": enums[2],
    }
    fqn_scope = FqnScope(namespace=ns, classes_by_fqn={}, enums_by_fqn=enums_by_fqn)

    # User-defined enum names -> ENUM
    d_enum = build_type_descriptor(
        plugin.type_descriptor_adapter, plugin.primitive_codec, fqn_scope, "transaction_intent_status"
    )
    assert d_enum.kind == Kind.enum and d_enum.enum_config is enums[0]

    d_enum_schema = build_type_descriptor(
        plugin.type_descriptor_adapter, plugin.primitive_codec, fqn_scope, "interface.interface_session_state"
    )
    assert d_enum_schema.kind == Kind.enum and d_enum_schema.enum_config is enums[2]

    # Array + enum
    d_enum_arr = build_type_descriptor(
        plugin.type_descriptor_adapter, plugin.primitive_codec, fqn_scope, "interface.interface_os[]"
    )
    assert d_enum_arr.kind == Kind.collection and d_enum_arr.collection_kind == AttributeCollectionType.list
    assert d_enum_arr.child_links
    assert d_enum_arr.child_links[0].role == Role.element
    elem = d_enum_arr.child_links[0].child
    assert elem is not None and elem.kind == Kind.enum and elem.enum_config is enums[1]

    # Schema-qualified enum array (public schema)
    d_enum_arr_pub = build_type_descriptor(
        plugin.type_descriptor_adapter, plugin.primitive_codec, fqn_scope, "public.transaction_intent_status[]"
    )
    assert d_enum_arr_pub.kind == Kind.collection and d_enum_arr_pub.collection_kind == AttributeCollectionType.list
    assert d_enum_arr_pub.child_links
    elem_pub = d_enum_arr_pub.child_links[0].child
    assert elem_pub is not None and elem_pub.kind == Kind.enum and elem_pub.enum_config is enums[0]

    # Vector mapping
    d_vec = build_type_descriptor(plugin.type_descriptor_adapter, plugin.primitive_codec, fqn_scope, "VECTOR(512)")
    assert d_vec.kind == Kind.primitive and d_vec.primitive_config is not None
    p = d_vec.primitive_config.primitive_type
    assert p is not None
    assert p.base_type.value == "vector"
    assert (p.constraints or {}).get("dimension") == 512
