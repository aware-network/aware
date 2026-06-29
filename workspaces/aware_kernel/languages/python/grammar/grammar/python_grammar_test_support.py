from __future__ import annotations

from aware_meta.graph.config.stable_ids import stable_object_config_graph_node_id
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_association import (
    ClassConfigRelationshipAssociation,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.graph.config.object_config_graph_node import ObjectConfigGraphNode


DEFAULT_PACKAGE = "aware_test"
DEFAULT_DOMAIN = "default"
DEFAULT_SCHEMA = "default"


def class_fqn(
    name: str,
    *,
    package: str = DEFAULT_PACKAGE,
    domain: str = DEFAULT_DOMAIN,
    schema: str = DEFAULT_SCHEMA,
) -> str:
    return f"{package}.{domain}.{schema}.{name}"


def enum_fqn(
    name: str,
    *,
    package: str = DEFAULT_PACKAGE,
    domain: str = DEFAULT_DOMAIN,
    schema: str = DEFAULT_SCHEMA,
) -> str:
    return f"{package}.{domain}.{schema}.{name}"


def function_owner_key(owner: ClassConfig | str) -> str:
    if isinstance(owner, ClassConfig):
        return owner.class_fqn
    return owner


def function_io_owner_key(function_config: FunctionConfig, attr_type: FunctionAttributeType | str) -> str:
    type_value = attr_type.value if isinstance(attr_type, FunctionAttributeType) else str(attr_type)
    return f"{function_config.owner_key}.{function_config.name}::{type_value}"


def make_class(
    name: str,
    *,
    package: str = DEFAULT_PACKAGE,
    domain: str = DEFAULT_DOMAIN,
    schema: str = DEFAULT_SCHEMA,
    **kwargs,
) -> ClassConfig:
    return ClassConfig(
        name=name,
        class_fqn=class_fqn(name, package=package, domain=domain, schema=schema),
        **kwargs,
    )


def make_enum(
    name: str,
    *,
    package: str = DEFAULT_PACKAGE,
    domain: str = DEFAULT_DOMAIN,
    schema: str = DEFAULT_SCHEMA,
    **kwargs,
) -> EnumConfig:
    return EnumConfig(
        name=name,
        enum_fqn=enum_fqn(name, package=package, domain=domain, schema=schema),
        **kwargs,
    )


def make_attribute(
    name: str,
    *,
    type_descriptor,
    owner_key: str,
    **kwargs,
) -> AttributeConfig:
    return AttributeConfig(
        owner_key=owner_key,
        name=name,
        type_descriptor=type_descriptor,
        **kwargs,
    )


def make_function(
    name: str,
    *,
    owner_key: str,
    **kwargs,
) -> FunctionConfig:
    return FunctionConfig(
        owner_key=owner_key,
        name=name,
        **kwargs,
    )


def class_attr_link(
    cls: ClassConfig,
    attr: AttributeConfig,
    *,
    position: int = 0,
    is_identity_key: bool = False,
    **kwargs,
) -> ClassConfigAttributeConfig:
    return ClassConfigAttributeConfig(
        class_config_id=cls.id,
        attribute_config=attr,
        attribute_config_id=attr.id,
        name=attr.name,
        position=position,
        is_identity_key=is_identity_key,
        **kwargs,
    )


def function_attr_link(
    fn: FunctionConfig,
    attr: AttributeConfig,
    *,
    type: FunctionAttributeType,
    position: int = 0,
    is_identity_key: bool = False,
    **kwargs,
) -> FunctionConfigAttributeConfig:
    return FunctionConfigAttributeConfig(
        function_config_id=fn.id,
        attribute_config=attr,
        attribute_config_id=attr.id,
        name=attr.name,
        type=type,
        position=position,
        is_identity_key=is_identity_key,
        **kwargs,
    )


def make_relationship(
    source: ClassConfig,
    target: ClassConfig,
    *,
    relationship_key: str,
    relationship_type,
    **kwargs,
) -> ClassConfigRelationship:
    return ClassConfigRelationship(
        class_config_id=source.id,
        target_class_config_id=target.id,
        relationship_key=relationship_key,
        relationship_type=relationship_type,
        **kwargs,
    )


def make_relationship_attribute(
    rel: ClassConfigRelationship,
    attr: AttributeConfig,
    *,
    direction,
    role,
    **kwargs,
) -> ClassConfigRelationshipAttribute:
    return ClassConfigRelationshipAttribute(
        class_config_relationship_id=rel.id,
        attribute_config_id=attr.id,
        attribute_config=attr,
        direction=direction,
        role=role,
        **kwargs,
    )


def make_relationship_association(
    rel: ClassConfigRelationship,
    cls: ClassConfig,
    **kwargs,
) -> ClassConfigRelationshipAssociation:
    return ClassConfigRelationshipAssociation(
        class_config_relationship_id=rel.id,
        class_config_id=cls.id,
        class_config=cls,
        **kwargs,
    )


def make_class_node(object_config_graph_id, class_config: ClassConfig) -> ObjectConfigGraphNode:
    return ObjectConfigGraphNode(
        id=stable_object_config_graph_node_id(
            object_config_graph_id=object_config_graph_id,
            type=ObjectConfigGraphNodeType.class_.value,
            node_key=class_config.class_fqn,
        ),
        object_config_graph_id=object_config_graph_id,
        type=ObjectConfigGraphNodeType.class_,
        node_key=class_config.class_fqn,
        class_config=class_config,
        class_config_id=class_config.id,
    )


__all__ = [
    "class_attr_link",
    "class_fqn",
    "enum_fqn",
    "function_attr_link",
    "function_io_owner_key",
    "function_owner_key",
    "make_attribute",
    "make_class",
    "make_class_node",
    "make_enum",
    "make_function",
    "make_relationship",
    "make_relationship_association",
    "make_relationship_attribute",
]
