from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from aware_meta.graph.config.stable_ids_resolution.contracts import (
    StableIdsServiceHooks,
)
from aware_meta.graph.config.stable_ids_resolution.service import (
    load_stable_ids_spec_for_graph,
)
from aware_meta.graph.config.stable_ids_spec.loader import (
    load_stable_ids_spec_from_toml_text,
)
import aware_meta.graph.config.stable_ids_spec as stable_ids_spec_pkg
import aware_meta.graph.config.stable_ids_spec.loader as stable_ids_loader
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.annotation.code_section_annotation_oneof import (
    CodeSectionAnnotationOneOf,
)
from aware_meta_ontology.annotation.code_section_annotation_identity import (
    CodeSectionAnnotationIdentity,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassIdentityMode
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
    FunctionKind,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_function_attribute_edge,
    make_function_config,
    test_function_attribute_owner_key,
)


def test_stable_ids_spec_loader_has_no_environment_manifest_lookup() -> None:
    loader_source = Path(stable_ids_loader.__file__).read_text(encoding="utf-8")

    assert not hasattr(
        stable_ids_loader, "resolve_environment_manifest_path_for_fqn_prefix"
    )
    assert not hasattr(
        stable_ids_spec_pkg, "resolve_environment_manifest_path_for_fqn_prefix"
    )
    assert "environment.manifest.json" not in loader_source
    assert "_ENVIRONMENT_MANIFEST_INDEX" not in loader_source


def _primitive_desc(base: CodePrimitiveBaseType) -> AttributeTypeDescriptor:
    primitive_type = build_code_primitive_type(base_type=base)
    primitive_config = PrimitiveConfig(
        primitive_type=primitive_type, primitive_type_id=primitive_type.id
    )
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
    )


def _input_attr(
    *, owner_key: str, name: str, base: CodePrimitiveBaseType
) -> AttributeConfig:
    desc = _primitive_desc(base)
    return make_attribute_config(
        owner_key=owner_key,
        name=name,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        default_value=None,
        type_descriptor=desc,
        type_descriptor_id=desc.id,
    )


def _optional_input_attr(
    *, owner_key: str, name: str, base: CodePrimitiveBaseType
) -> AttributeConfig:
    base_desc = _primitive_desc(base)
    null_desc = _primitive_desc(CodePrimitiveBaseType.null)
    union_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.union)
    union_desc.child_links = [
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=union_desc.id,
            child=base_desc,
            child_id=base_desc.id,
            role=AttributeTypeDescriptorRole.member,
            position=0,
        ),
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=union_desc.id,
            child=null_desc,
            child_id=null_desc.id,
            role=AttributeTypeDescriptorRole.member,
            position=1,
        ),
    ]
    return make_attribute_config(
        owner_key=owner_key,
        name=name,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        default_value=None,
        type_descriptor=union_desc,
        type_descriptor_id=union_desc.id,
    )


def _class_fqn(
    name: str,
    *,
    fqn_prefix: str = "aware_test",
    namespace: str = "default.default",
) -> str:
    if namespace:
        return f"{fqn_prefix}.{namespace}.{name}"
    return f"{fqn_prefix}.{name}"


def _class_config(
    *,
    name: str,
    is_base: bool = True,
    identity_mode: ClassIdentityMode = ClassIdentityMode.contained,
    fqn_prefix: str = "aware_test",
    namespace: str = "default.default",
) -> ClassConfig:
    return ClassConfig(
        class_fqn=_class_fqn(name, fqn_prefix=fqn_prefix, namespace=namespace),
        name=name,
        is_base=is_base,
        identity_mode=identity_mode,
    )


def _function_config(
    *, owner_name: str, name: str, kind: FunctionKind
) -> FunctionConfig:
    return make_function_config(
        owner_key=_class_fqn(owner_name),
        name=name,
        kind=kind,
    )


def _function_input_attr(
    *, function_config: FunctionConfig, name: str, base: CodePrimitiveBaseType
) -> AttributeConfig:
    return _input_attr(
        owner_key=test_function_attribute_owner_key(
            function_owner_key=function_config.owner_key,
            function_name=function_config.name,
            type=FunctionAttributeType.input,
        ),
        name=name,
        base=base,
    )


def _optional_function_input_attr(
    *,
    function_config: FunctionConfig,
    name: str,
    base: CodePrimitiveBaseType,
) -> AttributeConfig:
    return _optional_input_attr(
        owner_key=test_function_attribute_owner_key(
            function_owner_key=function_config.owner_key,
            function_name=function_config.name,
            type=FunctionAttributeType.input,
        ),
        name=name,
        base=base,
    )


def _class_attr_edge(
    *,
    class_config: ClassConfig,
    attribute_config: AttributeConfig,
    position: int,
) -> ClassConfigAttributeConfig:
    return make_class_attribute_edge(
        class_config_id=class_config.id,
        attribute_config=attribute_config,
        name=attribute_config.name,
        position=position,
    )


def _function_input_edge(
    *,
    function_config: FunctionConfig,
    attribute_config: AttributeConfig,
    position: int,
    is_identity_key: bool = False,
    identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
) -> FunctionConfigAttributeConfig:
    return make_function_attribute_edge(
        function_config_id=function_config.id,
        attribute_config=attribute_config,
        name=attribute_config.name,
        type=FunctionAttributeType.input,
        position=position,
        is_identity_key=is_identity_key,
        identity_key_origin=identity_key_origin,
    )


def _class_node(*, graph_id, class_config: ClassConfig) -> ObjectConfigGraphNode:
    return ObjectConfigGraphNode(
        type=ObjectConfigGraphNodeType.class_,
        node_key=class_config.class_fqn,
        class_config=class_config,
        object_config_graph_id=graph_id,
    )


def _build_compiler_owned_test_graph(
    *, fqn_prefix: str = "aware_conversation"
) -> ObjectConfigGraph:
    graph_id = uuid4()

    conversation = _class_config(name="Conversation")
    conversation_build = _function_config(
        owner_name="Conversation", name="build", kind=FunctionKind.class_
    )
    conversation_id = _function_input_attr(
        function_config=conversation_build,
        name="conversation_id",
        base=CodePrimitiveBaseType.uuid,
    )
    conversation_build.function_config_attribute_configs = [
        _function_input_edge(
            function_config=conversation_build,
            attribute_config=conversation_id,
            position=0,
            is_identity_key=True,
        )
    ]
    conversation.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=conversation.id,
            function_config=conversation_build,
            function_config_id=conversation_build.id,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]

    return ObjectConfigGraph(
        name="test_conversation",
        hash="sha256:test_conversation",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=conversation)
        ],
        object_projection_graphs=[],
    )


def _build_class_attr_signature_divergence_test_graph(
    *, fqn_prefix: str = "aware_conversation"
) -> ObjectConfigGraph:
    graph_id = uuid4()

    conversation = _class_config(name="Conversation")
    slug_attr = _input_attr(
        owner_key=conversation.class_fqn, name="slug", base=CodePrimitiveBaseType.string
    )
    slug_edge = _class_attr_edge(
        class_config=conversation, attribute_config=slug_attr, position=0
    )
    object.__setattr__(slug_edge, "is_identity_key", True)
    conversation.class_config_attribute_configs = [slug_edge]

    # Constructor identity keys intentionally diverge from class-attribute identity keys.
    conversation_build = _function_config(
        owner_name="Conversation", name="build", kind=FunctionKind.class_
    )
    conversation_id = _function_input_attr(
        function_config=conversation_build,
        name="conversation_id",
        base=CodePrimitiveBaseType.uuid,
    )
    conversation_build.function_config_attribute_configs = [
        _function_input_edge(
            function_config=conversation_build,
            attribute_config=conversation_id,
            position=0,
            is_identity_key=True,
        )
    ]
    conversation.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=conversation.id,
            function_config=conversation_build,
            function_config_id=conversation_build.id,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]

    return ObjectConfigGraph(
        name="test_conversation_class_attr_priority",
        hash="sha256:test_conversation_class_attr_priority",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=conversation)
        ],
        object_projection_graphs=[],
    )


def _build_class_attr_priority_compatible_test_graph(
    *, fqn_prefix: str = "aware_conversation"
) -> ObjectConfigGraph:
    graph_id = uuid4()

    conversation = _class_config(name="Conversation")
    slug_attr = _input_attr(
        owner_key=conversation.class_fqn, name="slug", base=CodePrimitiveBaseType.string
    )
    slug_edge = _class_attr_edge(
        class_config=conversation, attribute_config=slug_attr, position=0
    )
    object.__setattr__(slug_edge, "is_identity_key", True)
    conversation.class_config_attribute_configs = [slug_edge]

    # Constructor identity keys match class-attribute identity keys.
    conversation_build = _function_config(
        owner_name="Conversation", name="build", kind=FunctionKind.class_
    )
    slug_input = _function_input_attr(
        function_config=conversation_build,
        name="slug",
        base=CodePrimitiveBaseType.string,
    )
    conversation_build.function_config_attribute_configs = [
        _function_input_edge(
            function_config=conversation_build,
            attribute_config=slug_input,
            position=0,
            is_identity_key=True,
        )
    ]
    conversation.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=conversation.id,
            function_config=conversation_build,
            function_config_id=conversation_build.id,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]

    return ObjectConfigGraph(
        name="test_conversation_class_attr_priority_compatible",
        hash="sha256:test_conversation_class_attr_priority_compatible",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=conversation)
        ],
        object_projection_graphs=[],
    )


def _build_class_attr_default_compatible_test_graph(
    *, fqn_prefix: str = "aware_conversation"
) -> ObjectConfigGraph:
    graph_id = uuid4()

    conversation = _class_config(name="Conversation")
    key_attr = _input_attr(
        owner_key=conversation.class_fqn, name="key", base=CodePrimitiveBaseType.string
    )
    key_edge = _class_attr_edge(
        class_config=conversation, attribute_config=key_attr, position=0
    )
    object.__setattr__(key_edge, "is_identity_key", True)
    conversation.class_config_attribute_configs = [key_edge]

    # Constructor carries a default for the same key/type identity shape.
    conversation_build = _function_config(
        owner_name="Conversation", name="build", kind=FunctionKind.class_
    )
    key_input = _function_input_attr(
        function_config=conversation_build,
        name="key",
        base=CodePrimitiveBaseType.string,
    )
    object.__setattr__(key_input, "default_value", '"default"')
    conversation_build.function_config_attribute_configs = [
        _function_input_edge(
            function_config=conversation_build,
            attribute_config=key_input,
            position=0,
            is_identity_key=True,
        )
    ]
    conversation.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=conversation.id,
            function_config=conversation_build,
            function_config_id=conversation_build.id,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]

    return ObjectConfigGraph(
        name="test_conversation_class_attr_default_compatible",
        hash="sha256:test_conversation_class_attr_default_compatible",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=conversation)
        ],
        object_projection_graphs=[],
    )


def _build_class_attr_with_propagated_parent_constructor_test_graph(
    *,
    fqn_prefix: str = "aware_attention",
    include_propagated_parent_in_class_keys: bool = False,
    identity_mode: ClassIdentityMode = ClassIdentityMode.contained,
) -> ObjectConfigGraph:
    graph_id = uuid4()

    layout = _class_config(name="LayoutConfig")
    layout_key_attr = _input_attr(
        owner_key=layout.class_fqn,
        name="layout_key",
        base=CodePrimitiveBaseType.string,
    )
    layout_key_edge = _class_attr_edge(
        class_config=layout,
        attribute_config=layout_key_attr,
        position=0,
    )
    object.__setattr__(layout_key_edge, "is_identity_key", True)
    layout.class_config_attribute_configs = [layout_key_edge]

    layout_section = _class_config(
        name="LayoutConfigSectionConfig",
        identity_mode=identity_mode,
    )
    layout_config_id_attr = _input_attr(
        owner_key=layout_section.class_fqn,
        name="layout_config_id",
        base=CodePrimitiveBaseType.uuid,
    )
    section_key_attr = _input_attr(
        owner_key=layout_section.class_fqn,
        name="section_key",
        base=CodePrimitiveBaseType.string,
    )
    class_identity_edges: list[ClassConfigAttributeConfig] = []
    if include_propagated_parent_in_class_keys:
        layout_config_id_edge = _class_attr_edge(
            class_config=layout_section,
            attribute_config=layout_config_id_attr,
            position=0,
        )
        object.__setattr__(layout_config_id_edge, "is_identity_key", True)
        class_identity_edges.append(layout_config_id_edge)
    section_key_edge = _class_attr_edge(
        class_config=layout_section,
        attribute_config=section_key_attr,
        position=1 if include_propagated_parent_in_class_keys else 0,
    )
    object.__setattr__(section_key_edge, "is_identity_key", True)
    class_identity_edges.append(section_key_edge)
    layout_section.class_config_attribute_configs = class_identity_edges
    containment_relationship = ClassConfigRelationship(
        relationship_key="layout_config",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        class_config_id=layout.id,
        target_class_config_id=layout_section.id,
        identity_rail=ClassConfigRelationshipIdentityRail.containment,
    )
    containment_relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=containment_relationship.id,
            attribute_config_id=layout_config_id_attr.id,
            direction=ClassConfigRelationshipDirection.reverse,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    ]
    layout_section.class_config_relationships = [containment_relationship]

    create_fn = _function_config(
        owner_name="LayoutConfigSectionConfig",
        name="create_via_layout_config",
        kind=FunctionKind.class_,
    )
    section_key_input = _function_input_attr(
        function_config=create_fn,
        name="section_key",
        base=CodePrimitiveBaseType.string,
    )
    create_fn.function_config_attribute_configs = [
        _function_input_edge(
            function_config=create_fn,
            attribute_config=layout_config_id_attr,
            position=0,
            is_identity_key=True,
            identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
        ),
        _function_input_edge(
            function_config=create_fn,
            attribute_config=section_key_input,
            position=1,
            is_identity_key=True,
            identity_key_origin=FunctionIdentityKeyOrigin.standalone,
        ),
    ]
    layout_section.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=layout_section.id,
            function_config=create_fn,
            function_config_id=create_fn.id,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]

    return ObjectConfigGraph(
        name="test_layout_section_propagated_parent",
        hash="sha256:test_layout_section_propagated_parent",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=layout),
            _class_node(graph_id=graph_id, class_config=layout_section),
        ],
        object_projection_graphs=[],
    )


def _build_class_attr_parent_fk_first_order_test_graph(
    *, fqn_prefix: str = "aware_attention"
) -> ObjectConfigGraph:
    graph_id = uuid4()

    parent = _class_config(name="LayoutConfigSectionConfig")
    section_config = _class_config(name="SectionConfig")
    parent_key_attr = _input_attr(
        owner_key=parent.class_fqn,
        name="parent_key",
        base=CodePrimitiveBaseType.string,
    )
    parent_key_edge = _class_attr_edge(
        class_config=parent, attribute_config=parent_key_attr, position=0
    )
    object.__setattr__(parent_key_edge, "is_identity_key", True)
    parent.class_config_attribute_configs = [parent_key_edge]

    key_attr = _input_attr(
        owner_key=section_config.class_fqn,
        name="key",
        base=CodePrimitiveBaseType.string,
    )
    parent_fk_attr = _input_attr(
        owner_key=section_config.class_fqn,
        name="layout_config_section_config_id",
        base=CodePrimitiveBaseType.uuid,
    )

    key_edge = _class_attr_edge(
        class_config=section_config, attribute_config=key_attr, position=0
    )
    object.__setattr__(key_edge, "is_identity_key", True)
    parent_fk_edge = _class_attr_edge(
        class_config=section_config, attribute_config=parent_fk_attr, position=1
    )
    object.__setattr__(parent_fk_edge, "is_identity_key", True)
    section_config.class_config_attribute_configs = [key_edge, parent_fk_edge]

    relationship = ClassConfigRelationship(
        relationship_key="layout_config_section",
        relationship_type=ClassConfigRelationshipType.one_to_one,
        forward_required=True,
        class_config_id=section_config.id,
        target_class_config_id=parent.id,
    )
    relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=relationship.id,
            attribute_config_id=parent_fk_attr.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    ]
    section_config.class_config_relationships = [relationship]

    return ObjectConfigGraph(
        id=graph_id,
        name="test_class_attr_parent_fk_first_order",
        hash="sha256:test_class_attr_parent_fk_first_order",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=parent),
            _class_node(graph_id=graph_id, class_config=section_config),
        ],
        object_projection_graphs=[],
    )


def _build_class_attr_parent_fk_before_reference_fk_test_graph(
    *,
    fqn_prefix: str = "aware_attention",
) -> ObjectConfigGraph:
    graph_id = uuid4()

    parent = _class_config(name="ParentEntity")
    reference = _class_config(name="ReferenceEntity")
    child = _class_config(name="ChildEntity")
    parent_key_attr = _input_attr(
        owner_key=parent.class_fqn,
        name="parent_key",
        base=CodePrimitiveBaseType.string,
    )
    parent_key_edge = _class_attr_edge(
        class_config=parent, attribute_config=parent_key_attr, position=0
    )
    object.__setattr__(parent_key_edge, "is_identity_key", True)
    parent.class_config_attribute_configs = [parent_key_edge]
    reference_key_attr = _input_attr(
        owner_key=reference.class_fqn,
        name="reference_key",
        base=CodePrimitiveBaseType.string,
    )
    reference_key_edge = _class_attr_edge(
        class_config=reference, attribute_config=reference_key_attr, position=0
    )
    object.__setattr__(reference_key_edge, "is_identity_key", True)
    reference.class_config_attribute_configs = [reference_key_edge]

    parent_fk_attr = _input_attr(
        owner_key=child.class_fqn,
        name="parent_entity_id",
        base=CodePrimitiveBaseType.uuid,
    )
    reference_fk_attr = _input_attr(
        owner_key=child.class_fqn,
        name="reference_entity_id",
        base=CodePrimitiveBaseType.uuid,
    )

    # Deliberately place reference FK earlier than parent FK to prove ordering is
    # identity-rail-driven (containment parent first), not raw position.
    reference_fk_edge = _class_attr_edge(
        class_config=child, attribute_config=reference_fk_attr, position=0
    )
    object.__setattr__(reference_fk_edge, "is_identity_key", True)
    parent_fk_edge = _class_attr_edge(
        class_config=child, attribute_config=parent_fk_attr, position=1
    )
    object.__setattr__(parent_fk_edge, "is_identity_key", True)
    child.class_config_attribute_configs = [reference_fk_edge, parent_fk_edge]

    containment_relationship = ClassConfigRelationship(
        relationship_key="parent_entity",
        relationship_type=ClassConfigRelationshipType.one_to_one,
        forward_required=True,
        class_config_id=parent.id,
        target_class_config_id=child.id,
        identity_rail=ClassConfigRelationshipIdentityRail.containment,
    )
    containment_relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=containment_relationship.id,
            attribute_config_id=parent_fk_attr.id,
            direction=ClassConfigRelationshipDirection.reverse,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    ]

    reference_relationship = ClassConfigRelationship(
        relationship_key="reference_entity",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        class_config_id=child.id,
        target_class_config_id=reference.id,
        identity_rail=ClassConfigRelationshipIdentityRail.reference,
    )
    reference_relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=reference_relationship.id,
            attribute_config_id=reference_fk_attr.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    ]
    child.class_config_relationships = [
        reference_relationship,
        containment_relationship,
    ]

    return ObjectConfigGraph(
        id=graph_id,
        name="test_class_attr_parent_fk_before_reference_fk",
        hash="sha256:test_class_attr_parent_fk_before_reference_fk",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=parent),
            _class_node(graph_id=graph_id, class_config=reference),
            _class_node(graph_id=graph_id, class_config=child),
        ],
        object_projection_graphs=[],
    )


def _build_identity_oneof_class_key_test_graph(
    *,
    fqn_prefix: str = "aware_network",
    include_response_identity_key: bool = True,
) -> ObjectConfigGraph:
    graph_id = uuid4()

    operation = _class_config(
        name="NetworkNodeOperation",
        fqn_prefix=fqn_prefix,
        namespace="core.models",
    )
    request_id_attr = _optional_input_attr(
        owner_key=operation.class_fqn,
        name="request_id",
        base=CodePrimitiveBaseType.uuid,
    )
    response_id_attr = _optional_input_attr(
        owner_key=operation.class_fqn,
        name="response_id",
        base=CodePrimitiveBaseType.uuid,
    )
    request_edge = _class_attr_edge(
        class_config=operation, attribute_config=request_id_attr, position=0
    )
    response_edge = _class_attr_edge(
        class_config=operation, attribute_config=response_id_attr, position=1
    )
    object.__setattr__(request_edge, "is_identity_key", True)
    object.__setattr__(response_edge, "is_identity_key", include_response_identity_key)
    operation.class_config_attribute_configs = [request_edge, response_edge]

    oneof = CodeSectionAnnotationOneOf(
        fqn_prefix=fqn_prefix,
        namespace="core.models",
        class_name="NetworkNodeOperation",
        mode="identity",
        attribute_names=["request_id", "response_id"],
    )
    oneof_ann = ObjectConfigGraphAnnotation(
        kind=ObjectConfigGraphAnnotationKind.oneof,
        object_config_graph_id=graph_id,
        code_section_annotation_oneof=oneof,
        code_section_annotation_oneof_id=oneof.id,
    )

    return ObjectConfigGraph(
        id=graph_id,
        name="test_network_oneof_identity",
        hash="sha256:test_network_oneof_identity",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=operation)
        ],
        object_config_graph_annotations=[oneof_ann],
        object_projection_graphs=[],
    )


def _build_discriminator_identity_oneof_test_graph(
    *,
    fqn_prefix: str = "aware_meta",
) -> ObjectConfigGraph:
    graph_id = uuid4()

    node = _class_config(
        name="ObjectConfigGraphNode",
        fqn_prefix=fqn_prefix,
        namespace="graph.config",
    )
    type_attr = _input_attr(
        owner_key=node.class_fqn, name="type", base=CodePrimitiveBaseType.string
    )
    enum_config_attr = _optional_input_attr(
        owner_key=node.class_fqn, name="enum_config_id", base=CodePrimitiveBaseType.uuid
    )
    class_config_attr = _optional_input_attr(
        owner_key=node.class_fqn,
        name="class_config_id",
        base=CodePrimitiveBaseType.uuid,
    )

    type_edge = _class_attr_edge(
        class_config=node, attribute_config=type_attr, position=0
    )
    enum_edge = _class_attr_edge(
        class_config=node, attribute_config=enum_config_attr, position=1
    )
    class_edge = _class_attr_edge(
        class_config=node, attribute_config=class_config_attr, position=2
    )
    object.__setattr__(type_edge, "is_identity_key", True)
    object.__setattr__(enum_edge, "is_identity_key", False)
    object.__setattr__(class_edge, "is_identity_key", False)
    node.class_config_attribute_configs = [type_edge, enum_edge, class_edge]

    oneof = CodeSectionAnnotationOneOf(
        fqn_prefix=fqn_prefix,
        namespace="graph.config",
        class_name="ObjectConfigGraphNode",
        mode="identity",
        attribute_names=["enum_config_id", "class_config_id"],
        discriminator_attribute_name="type",
        discriminator_cases=["enum=enum_config_id", "class=class_config_id"],
    )
    oneof_ann = ObjectConfigGraphAnnotation(
        kind=ObjectConfigGraphAnnotationKind.oneof,
        object_config_graph_id=graph_id,
        code_section_annotation_oneof=oneof,
        code_section_annotation_oneof_id=oneof.id,
    )

    return ObjectConfigGraph(
        id=graph_id,
        name="test_discriminator_oneof_identity",
        hash="sha256:test_discriminator_oneof_identity",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[_class_node(graph_id=graph_id, class_config=node)],
        object_config_graph_annotations=[oneof_ann],
        object_projection_graphs=[],
    )


def _build_attribute_type_descriptor_discriminator_test_graph(
    *,
    fqn_prefix: str = "aware_meta",
) -> ObjectConfigGraph:
    graph_id = uuid4()

    descriptor = _class_config(
        name="AttributeTypeDescriptor",
        fqn_prefix=fqn_prefix,
        namespace="attribute",
    )
    kind_attr = _input_attr(
        owner_key=descriptor.class_fqn, name="kind", base=CodePrimitiveBaseType.string
    )
    collection_kind_desc = _primitive_desc(CodePrimitiveBaseType.string)
    collection_kind_attr = make_attribute_config(
        owner_key=descriptor.class_fqn,
        name="collection_kind",
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        default_value="single",
        type_descriptor=collection_kind_desc,
        type_descriptor_id=collection_kind_desc.id,
    )
    class_config_attr = _optional_input_attr(
        owner_key=descriptor.class_fqn,
        name="class_config_id",
        base=CodePrimitiveBaseType.uuid,
    )
    enum_config_attr = _optional_input_attr(
        owner_key=descriptor.class_fqn,
        name="enum_config_id",
        base=CodePrimitiveBaseType.uuid,
    )
    primitive_config_attr = _optional_input_attr(
        owner_key=descriptor.class_fqn,
        name="primitive_config_id",
        base=CodePrimitiveBaseType.uuid,
    )
    child_links_element_desc = _primitive_desc(CodePrimitiveBaseType.string)
    child_links_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.collection,
        collection_kind=AttributeCollectionType.list,
        child_links=[
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=uuid4(),
                child=child_links_element_desc,
                child_id=child_links_element_desc.id,
                role=AttributeTypeDescriptorRole.element,
                position=0,
            )
        ],
    )
    child_links_attr = make_attribute_config(
        owner_key=descriptor.class_fqn,
        name="child_links",
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        default_value=None,
        type_descriptor=child_links_desc,
        type_descriptor_id=child_links_desc.id,
    )

    collection_kind_edge = _class_attr_edge(
        class_config=descriptor, attribute_config=collection_kind_attr, position=0
    )
    kind_edge = _class_attr_edge(
        class_config=descriptor, attribute_config=kind_attr, position=1
    )
    class_edge = _class_attr_edge(
        class_config=descriptor, attribute_config=class_config_attr, position=2
    )
    enum_edge = _class_attr_edge(
        class_config=descriptor, attribute_config=enum_config_attr, position=3
    )
    primitive_edge = _class_attr_edge(
        class_config=descriptor, attribute_config=primitive_config_attr, position=4
    )
    object.__setattr__(kind_edge, "is_identity_key", True)
    object.__setattr__(collection_kind_edge, "is_identity_key", True)
    object.__setattr__(class_edge, "is_identity_key", False)
    object.__setattr__(enum_edge, "is_identity_key", False)
    object.__setattr__(primitive_edge, "is_identity_key", False)
    descriptor.class_config_attribute_configs = [
        collection_kind_edge,
        kind_edge,
        class_edge,
        enum_edge,
        primitive_edge,
    ]
    child_links_relationship = ClassConfigRelationship(
        relationship_key="child_links",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        class_config_id=descriptor.id,
        target_class_config_id=uuid4(),
        identity_rail=ClassConfigRelationshipIdentityRail.reference,
    )
    child_links_relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=child_links_relationship.id,
            attribute_config=child_links_attr,
            attribute_config_id=child_links_attr.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    descriptor.class_config_relationships = [child_links_relationship]

    oneof = CodeSectionAnnotationOneOf(
        fqn_prefix=fqn_prefix,
        namespace="attribute",
        class_name="AttributeTypeDescriptor",
        mode="identity",
        attribute_names=["class_config_id", "enum_config_id", "primitive_config_id"],
        discriminator_attribute_name="kind",
        discriminator_cases=[
            "class=class_config_id",
            "enum=enum_config_id",
            "primitive=primitive_config_id",
        ],
    )
    oneof_ann = ObjectConfigGraphAnnotation(
        kind=ObjectConfigGraphAnnotationKind.oneof,
        object_config_graph_id=graph_id,
        code_section_annotation_oneof=oneof,
        code_section_annotation_oneof_id=oneof.id,
    )
    identity = CodeSectionAnnotationIdentity(
        fqn_prefix=fqn_prefix,
        namespace="attribute",
        class_name="AttributeTypeDescriptor",
        mode=ClassIdentityMode.standalone,
        structural_relation_name="child_links",
    )
    identity_ann = ObjectConfigGraphAnnotation(
        kind=ObjectConfigGraphAnnotationKind.identity,
        object_config_graph_id=graph_id,
        code_section_annotation_identity=identity,
        code_section_annotation_identity_id=identity.id,
    )

    return ObjectConfigGraph(
        id=graph_id,
        name="test_attribute_type_descriptor_discriminator_identity",
        hash="sha256:test_attribute_type_descriptor_discriminator_identity",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=descriptor)
        ],
        object_config_graph_annotations=[oneof_ann, identity_ann],
        object_projection_graphs=[],
    )


def _build_contained_discriminator_identity_parent_subset_test_graph(
    *,
    fqn_prefix: str = "aware_social",
) -> ObjectConfigGraph:
    graph_id = uuid4()

    feed = _class_config(name="Feed", fqn_prefix=fqn_prefix, namespace="social")
    feed_item = _class_config(
        name="FeedItem",
        fqn_prefix=fqn_prefix,
        namespace="social",
    )

    feed_key_attr = _input_attr(
        owner_key=feed.class_fqn, name="feed_key", base=CodePrimitiveBaseType.string
    )
    feed_key_edge = _class_attr_edge(
        class_config=feed, attribute_config=feed_key_attr, position=0
    )
    object.__setattr__(feed_key_edge, "is_identity_key", True)
    feed.class_config_attribute_configs = [feed_key_edge]

    feed_id_attr = _input_attr(
        owner_key=feed_item.class_fqn, name="feed_id", base=CodePrimitiveBaseType.uuid
    )
    kind_attr = _input_attr(
        owner_key=feed_item.class_fqn, name="kind", base=CodePrimitiveBaseType.string
    )
    post_id_attr = _optional_input_attr(
        owner_key=feed_item.class_fqn, name="post_id", base=CodePrimitiveBaseType.uuid
    )
    event_id_attr = _optional_input_attr(
        owner_key=feed_item.class_fqn, name="event_id", base=CodePrimitiveBaseType.uuid
    )

    feed_id_edge = _class_attr_edge(
        class_config=feed_item, attribute_config=feed_id_attr, position=0
    )
    kind_edge = _class_attr_edge(
        class_config=feed_item, attribute_config=kind_attr, position=1
    )
    post_id_edge = _class_attr_edge(
        class_config=feed_item, attribute_config=post_id_attr, position=2
    )
    event_id_edge = _class_attr_edge(
        class_config=feed_item, attribute_config=event_id_attr, position=3
    )
    object.__setattr__(feed_id_edge, "is_identity_key", True)
    object.__setattr__(kind_edge, "is_identity_key", True)
    object.__setattr__(post_id_edge, "is_identity_key", False)
    object.__setattr__(event_id_edge, "is_identity_key", False)
    feed_item.class_config_attribute_configs = [
        feed_id_edge,
        kind_edge,
        post_id_edge,
        event_id_edge,
    ]

    containment_relationship = ClassConfigRelationship(
        relationship_key="items",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        class_config_id=feed.id,
        target_class_config_id=feed_item.id,
        identity_rail=ClassConfigRelationshipIdentityRail.containment,
    )
    containment_relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=containment_relationship.id,
            attribute_config_id=feed_id_attr.id,
            direction=ClassConfigRelationshipDirection.reverse,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    ]
    feed_item.class_config_relationships = [containment_relationship]

    create_post_fn = _function_config(
        owner_name="FeedItem",
        name="create_post_item_via_feed",
        kind=FunctionKind.class_,
    )
    post_key_input = _function_input_attr(
        function_config=create_post_fn,
        name="post_key",
        base=CodePrimitiveBaseType.string,
    )
    create_post_fn.function_config_attribute_configs = [
        _function_input_edge(
            function_config=create_post_fn,
            attribute_config=feed_id_attr,
            position=0,
            is_identity_key=True,
            identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
        ),
        _function_input_edge(
            function_config=create_post_fn,
            attribute_config=post_key_input,
            position=1,
            is_identity_key=False,
        ),
    ]

    create_event_fn = _function_config(
        owner_name="FeedItem",
        name="create_event_item_via_feed",
        kind=FunctionKind.class_,
    )
    event_input = _function_input_attr(
        function_config=create_event_fn,
        name="event_id",
        base=CodePrimitiveBaseType.uuid,
    )
    create_event_fn.function_config_attribute_configs = [
        _function_input_edge(
            function_config=create_event_fn,
            attribute_config=feed_id_attr,
            position=0,
            is_identity_key=True,
            identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
        ),
        _function_input_edge(
            function_config=create_event_fn,
            attribute_config=event_input,
            position=1,
            is_identity_key=False,
        ),
    ]

    feed_item.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=feed_item.id,
            function_config=create_post_fn,
            function_config_id=create_post_fn.id,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
        ClassConfigFunctionConfig(
            class_config_id=feed_item.id,
            function_config=create_event_fn,
            function_config_id=create_event_fn.id,
            is_public=True,
            is_constructor=True,
            position=1,
        ),
    ]

    oneof = CodeSectionAnnotationOneOf(
        fqn_prefix=fqn_prefix,
        namespace="social",
        class_name="FeedItem",
        mode="identity",
        attribute_names=["post_id", "event_id"],
        discriminator_attribute_name="kind",
        discriminator_cases=["post=post_id", "event=event_id"],
    )
    oneof_ann = ObjectConfigGraphAnnotation(
        kind=ObjectConfigGraphAnnotationKind.oneof,
        object_config_graph_id=graph_id,
        code_section_annotation_oneof=oneof,
        code_section_annotation_oneof_id=oneof.id,
    )

    return ObjectConfigGraph(
        id=graph_id,
        name="test_contained_discriminator_identity_parent_subset",
        hash="sha256:test_contained_discriminator_identity_parent_subset",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _class_node(graph_id=graph_id, class_config=feed),
            _class_node(graph_id=graph_id, class_config=feed_item),
        ],
        object_config_graph_annotations=[oneof_ann],
        object_projection_graphs=[],
    )


def _build_hooks(
    *,
    resolve_spec_path_for_fqn_prefix,
    load_spec_from_path,
    count_authored_functions_in_path,
) -> StableIdsServiceHooks:
    return StableIdsServiceHooks(
        resolve_spec_path_for_fqn_prefix=resolve_spec_path_for_fqn_prefix,
        load_spec_from_path=load_spec_from_path,
        count_authored_functions_in_path=count_authored_functions_in_path,
    )


def test_stable_ids_service_compiler_ownership_rejects_constructor_only_identity_by_default() -> (
    None
):
    graph = _build_compiler_owned_test_graph()

    with pytest.raises(
        ValueError,
        match=r"class_strict stable-id resolution failed; missing_graph_ref_class_identity_keys=\[Conversation\]",
    ):
        load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")


def test_stable_ids_service_class_strict_rejects_graph_ref_constructor_only_identity() -> (
    None
):
    graph = _build_compiler_owned_test_graph()

    with pytest.raises(
        ValueError,
        match=r"class_strict stable-id resolution failed; missing_graph_ref_class_identity_keys=\[Conversation\]",
    ):
        load_stable_ids_spec_for_graph(
            graph=graph,
            ownership="compiler",
            resolution_policy="class_strict",
        )


def test_stable_ids_service_derives_from_class_keys_when_constructor_signature_diverges() -> (
    None
):
    graph = _build_class_attr_signature_divergence_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(fn for fn in spec.functions if fn.name == "stable_conversation_id")
    assert [param.name for param in stable_fn.params] == ["slug"]
    assert stable_fn.template == "aware:conversation:{slug_norm}"
    assert (
        stable_fn.doc == "Compiler-generated from class-attribute identity keys: slug"
    )


def test_stable_ids_service_prefers_class_attribute_identity_keys_when_signature_is_compatible() -> (
    None
):
    graph = _build_class_attr_priority_compatible_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(fn for fn in spec.functions if fn.name == "stable_conversation_id")
    assert [param.name for param in stable_fn.params] == ["slug"]
    assert stable_fn.template == "aware:conversation:{slug_norm}"
    assert (
        stable_fn.doc == "Compiler-generated from class-attribute identity keys: slug"
    )


def test_stable_ids_service_explicit_class_strict_derives_from_class_keys_when_constructor_signature_diverges() -> (
    None
):
    graph = _build_class_attr_signature_divergence_test_graph()

    spec = load_stable_ids_spec_for_graph(
        graph=graph,
        ownership="compiler",
        resolution_policy="class_strict",
    )

    assert spec is not None
    stable_fn = next(fn for fn in spec.functions if fn.name == "stable_conversation_id")
    assert [param.name for param in stable_fn.params] == ["slug"]
    assert stable_fn.template == "aware:conversation:{slug_norm}"
    assert (
        stable_fn.doc == "Compiler-generated from class-attribute identity keys: slug"
    )


def test_stable_ids_service_derives_from_class_keys_when_constructor_defaults_exist_by_default() -> (
    None
):
    graph = _build_class_attr_default_compatible_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(fn for fn in spec.functions if fn.name == "stable_conversation_id")
    assert [param.name for param in stable_fn.params] == ["key"]
    assert stable_fn.params[0].default is None
    assert stable_fn.doc == "Compiler-generated from class-attribute identity keys: key"


def test_stable_ids_service_class_strict_derives_from_class_keys_even_when_constructor_defaults_exist() -> (
    None
):
    graph = _build_class_attr_default_compatible_test_graph()

    spec = load_stable_ids_spec_for_graph(
        graph=graph,
        ownership="compiler",
        resolution_policy="class_strict",
    )

    assert spec is not None
    stable_fn = next(fn for fn in spec.functions if fn.name == "stable_conversation_id")
    assert [param.name for param in stable_fn.params] == ["key"]
    assert stable_fn.params[0].default is None
    assert stable_fn.doc == "Compiler-generated from class-attribute identity keys: key"


def test_stable_ids_service_class_strict_exports_contained_constructor_parent_formula() -> (
    None
):
    graph = _build_class_attr_with_propagated_parent_constructor_test_graph()
    layout_config = next(
        node.class_config
        for node in graph.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "LayoutConfig"
    )
    key_attr = _input_attr(
        owner_key=layout_config.class_fqn,
        name="key",
        base=CodePrimitiveBaseType.string,
    )
    key_edge = _class_attr_edge(
        class_config=layout_config,
        attribute_config=key_attr,
        position=0,
    )
    object.__setattr__(key_edge, "is_identity_key", True)
    layout_config.class_config_attribute_configs = [key_edge]

    spec = load_stable_ids_spec_for_graph(
        graph=graph,
        ownership="compiler",
        resolution_policy="class_strict",
    )

    assert spec is not None
    stable_fn = next(
        fn
        for fn in spec.functions
        if fn.name == "stable_layout_config_section_config_id"
    )
    assert [param.name for param in stable_fn.params] == [
        "layout_config_id",
        "section_key",
    ]
    assert stable_fn.template == (
        "aware:layout_config_section_config:" "{layout_config_id}:{section_key_norm}"
    )
    assert stable_fn.doc == (
        "Compiler-generated from constructor identity keys: "
        "layout_config_id, section_key"
    )


def test_stable_ids_service_rejects_constructor_standalone_match_for_contained_class() -> (
    None
):
    graph = _build_class_attr_with_propagated_parent_constructor_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(
        fn
        for fn in spec.functions
        if fn.name == "stable_layout_config_section_config_id"
    )
    assert [param.name for param in stable_fn.params] == [
        "layout_config_id",
        "section_key",
    ]
    assert stable_fn.doc == (
        "Compiler-generated from constructor identity keys: "
        "layout_config_id, section_key"
    )


def test_stable_ids_service_accepts_class_identity_keys_that_include_propagated_parent_fk() -> (
    None
):
    graph = _build_class_attr_with_propagated_parent_constructor_test_graph(
        include_propagated_parent_in_class_keys=True,
    )

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(
        fn
        for fn in spec.functions
        if fn.name == "stable_layout_config_section_config_id"
    )
    assert [param.name for param in stable_fn.params] == [
        "layout_config_id",
        "section_key",
    ]
    assert (
        stable_fn.template
        == "aware:layout_config_section_config:{layout_config_id}:{section_key_norm}"
    )
    assert (
        stable_fn.doc
        == "Compiler-generated from class-attribute identity keys: layout_config_id, section_key"
    )


def test_stable_ids_service_accepts_constructor_standalone_match_for_standalone_class() -> (
    None
):
    graph = _build_class_attr_with_propagated_parent_constructor_test_graph(
        identity_mode=ClassIdentityMode.standalone,
    )

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(
        fn
        for fn in spec.functions
        if fn.name == "stable_layout_config_section_config_id"
    )
    assert [param.name for param in stable_fn.params] == ["section_key"]
    assert stable_fn.template == "aware:layout_config_section_config:{section_key_norm}"
    assert (
        stable_fn.doc
        == "Compiler-generated from class-attribute identity keys: section_key"
    )


def test_stable_ids_service_excludes_containment_parent_fk_from_standalone_class_formula() -> (
    None
):
    graph = _build_class_attr_with_propagated_parent_constructor_test_graph(
        include_propagated_parent_in_class_keys=True,
        identity_mode=ClassIdentityMode.standalone,
    )

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(
        fn
        for fn in spec.functions
        if fn.name == "stable_layout_config_section_config_id"
    )
    assert [param.name for param in stable_fn.params] == ["section_key"]
    assert stable_fn.template == "aware:layout_config_section_config:{section_key_norm}"
    assert (
        stable_fn.doc
        == "Compiler-generated from class-attribute identity keys: section_key"
    )


def test_stable_ids_service_orders_parent_fk_identity_before_local_class_keys() -> None:
    graph = _build_class_attr_parent_fk_first_order_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(
        fn for fn in spec.functions if fn.name == "stable_section_config_id"
    )
    assert [param.name for param in stable_fn.params] == [
        "layout_config_section_config_id",
        "key",
    ]
    assert (
        stable_fn.template
        == "aware:section_config:{layout_config_section_config_id}:{key_norm}"
    )
    assert (
        stable_fn.doc
        == "Compiler-generated from class-attribute identity keys: layout_config_section_config_id, key"
    )


def test_stable_ids_service_orders_containment_parent_fk_before_reference_fk() -> None:
    graph = _build_class_attr_parent_fk_before_reference_fk_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(fn for fn in spec.functions if fn.name == "stable_child_entity_id")
    assert [param.name for param in stable_fn.params] == [
        "parent_entity_id",
        "reference_entity_id",
    ]
    assert (
        stable_fn.template
        == "aware:child_entity:{parent_entity_id}:{reference_entity_id}"
    )
    assert (
        stable_fn.doc
        == "Compiler-generated from class-attribute identity keys: parent_entity_id, reference_entity_id"
    )


def test_stable_ids_service_derives_identity_oneof_nullable_uuid_formula() -> None:
    graph = _build_identity_oneof_class_key_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(
        fn for fn in spec.functions if fn.name == "stable_network_node_operation_id"
    )
    assert [param.name for param in stable_fn.params] == ["request_id", "response_id"]
    assert [param.optional for param in stable_fn.params] == [True, True]
    assert (
        stable_fn.template
        == "aware:network_node_operation:{request_id_str}:{response_id_str}"
    )
    assert [let.op for let in stable_fn.lets] == [
        "uuid_str_default",
        "uuid_str_default",
    ]
    assert (
        stable_fn.doc
        == "Compiler-generated from class-attribute identity keys: request_id, response_id"
    )


def test_stable_ids_service_identity_oneof_requires_member_identity_keys() -> None:
    graph = _build_identity_oneof_class_key_test_graph(
        include_response_identity_key=False
    )

    with pytest.raises(
        ValueError,
        match=r"identity oneof annotation requires each member attribute to be declared as class identity key",
    ):
        load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")


def test_stable_ids_service_derives_discriminator_identity_oneof_entity_formula() -> (
    None
):
    graph = _build_discriminator_identity_oneof_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(
        fn for fn in spec.functions if fn.name == "stable_object_config_graph_node_id"
    )
    assert [param.name for param in stable_fn.params] == ["type", "entity_id"]
    assert (
        stable_fn.template == "aware:object_config_graph_node:{type_norm}:{entity_id}"
    )
    assert (
        stable_fn.doc
        == "Compiler-generated from class-attribute identity keys: type, entity_id"
    )


def test_stable_ids_service_derives_attribute_type_descriptor_leaf_entity_formula() -> (
    None
):
    graph = _build_attribute_type_descriptor_discriminator_test_graph()

    spec = load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")

    assert spec is not None
    stable_fn = next(
        fn for fn in spec.functions if fn.name == "stable_attribute_type_descriptor_id"
    )
    assert [param.name for param in stable_fn.params] == [
        "collection_kind",
        "kind",
        "entity_id",
        "child_links_fingerprint",
    ]
    assert [param.optional for param in stable_fn.params] == [False, False, True, False]
    assert stable_fn.template == (
        "aware:attribute_type_descriptor:{collection_kind_norm}:{kind_norm}:{entity_id_str}:{child_links_fingerprint}"
    )
    assert stable_fn.doc == (
        "Compiler-generated from class-attribute identity keys: collection_kind, kind, entity_id, child_links_fingerprint"
    )


def test_stable_ids_service_accepts_contained_discriminator_identity_extending_parent_subset() -> (
    None
):
    graph = _build_contained_discriminator_identity_parent_subset_test_graph()

    spec = load_stable_ids_spec_for_graph(
        graph=graph,
        ownership="compiler",
        resolution_policy="class_strict",
    )

    assert spec is not None
    stable_fn = next(fn for fn in spec.functions if fn.name == "stable_feed_item_id")
    assert [param.name for param in stable_fn.params] == [
        "feed_id",
        "kind",
        "entity_id",
    ]
    assert [param.optional for param in stable_fn.params] == [False, False, False]
    assert stable_fn.template == "aware:feed_item:{feed_id}:{kind_norm}:{entity_id}"
    assert (
        stable_fn.doc
        == "Compiler-generated from class-attribute identity keys: feed_id, kind, entity_id"
    )


def test_stable_ids_service_rejects_unknown_ownership_mode() -> None:
    graph = _build_compiler_owned_test_graph()

    with pytest.raises(
        ValueError, match=r"stable_ids ownership must be one of authored\|compiler"
    ):
        load_stable_ids_spec_for_graph(graph=graph, ownership="mystery")


def test_stable_ids_service_rejects_unknown_resolution_policy() -> None:
    graph = _build_compiler_owned_test_graph()

    with pytest.raises(
        ValueError,
        match=r"stable_ids resolution policy must be class_strict",
    ):
        load_stable_ids_spec_for_graph(
            graph=graph, ownership="compiler", resolution_policy="strict"
        )


def test_stable_ids_service_rejects_compat_resolution_policy() -> None:
    graph = _build_class_attr_priority_compatible_test_graph()

    with pytest.raises(
        ValueError,
        match=r"stable_ids resolution policy must be class_strict",
    ):
        load_stable_ids_spec_for_graph(
            graph=graph, ownership="compiler", resolution_policy="compat"
        )


def test_stable_ids_service_compiler_ownership_rejects_non_aware_source_graph() -> None:
    graph = _build_compiler_owned_test_graph()
    graph.language = CodeLanguage.dart

    with pytest.raises(
        ValueError, match=r"compiler-owned stable ids require an Aware source graph"
    ):
        load_stable_ids_spec_for_graph(graph=graph, ownership="compiler")


def test_stable_ids_service_compiler_ownership_does_not_load_source_spec() -> None:
    graph = _build_class_attr_priority_compatible_test_graph()
    hooks = _build_hooks(
        resolve_spec_path_for_fqn_prefix=lambda _fqn_prefix: Path(
            "/tmp/stable_ids.toml"
        ),
        load_spec_from_path=lambda _spec_path: (_ for _ in ()).throw(
            AssertionError("source spec must not load")
        ),
        count_authored_functions_in_path=lambda _spec_path: 0,
    )

    spec = load_stable_ids_spec_for_graph(
        graph=graph, ownership="compiler", hooks=hooks
    )

    assert spec is not None
    assert "stable_conversation_id" in {fn.name for fn in spec.functions}


def test_stable_ids_service_compiler_ownership_fails_when_authored_spec_exists_but_no_derivation() -> (
    None
):
    graph = ObjectConfigGraph(
        name="authored_only",
        hash="sha256:authored_only",
        fqn_prefix="aware_authored_only",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
    )
    hooks = _build_hooks(
        resolve_spec_path_for_fqn_prefix=lambda _fqn_prefix: Path(
            "/tmp/stable_ids.toml"
        ),
        load_spec_from_path=lambda _spec_path: (_ for _ in ()).throw(
            AssertionError("compiler mode must not load spec")
        ),
        count_authored_functions_in_path=lambda _spec_path: 1,
    )

    with pytest.raises(
        ValueError,
        match=(
            r"compiler-owned stable ids derived no formulas from "
            r"class-attribute identity keys"
        ),
    ):
        load_stable_ids_spec_for_graph(graph=graph, ownership="compiler", hooks=hooks)


def test_stable_ids_service_authored_mode_returns_authored_spec_without_graph_derivation() -> (
    None
):
    graph = _build_compiler_owned_test_graph(fqn_prefix="aware_test_authored")
    authored = load_stable_ids_spec_from_toml_text(
        toml_text=(
            "\n".join(
                [
                    "version = 1",
                    "",
                    "[[namespaces]]",
                    'name = "NS_TEST"',
                    'kind = "ns_url"',
                    'value = "aware://test/v1"',
                    "",
                    "[[functions]]",
                    'name = "stable_legacy_id"',
                    'namespace = "NS_TEST"',
                    'template = "legacy:{key}"',
                    "",
                    "[[functions.params]]",
                    'name = "key"',
                    'type = "str"',
                ]
            )
            + "\n"
        ),
        source_label="<memory:authored>",
    )
    hooks = _build_hooks(
        resolve_spec_path_for_fqn_prefix=lambda _fqn_prefix: Path(
            "/tmp/stable_ids.toml"
        ),
        load_spec_from_path=lambda _spec_path: authored,
        count_authored_functions_in_path=lambda _spec_path: len(authored.functions),
    )

    resolved = load_stable_ids_spec_for_graph(
        graph=graph, ownership="authored", hooks=hooks
    )

    assert resolved == authored
    assert {fn.name for fn in resolved.functions} == {"stable_legacy_id"}
