from __future__ import annotations

from typing import Any
from uuid import UUID

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
from aware_meta_ontology.graph.config.object_config_graph_node import ObjectConfigGraphNode
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph

from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base


def test_class_fqn(
    name: str,
    *,
    package: str = "tests.meta",
    namespace: str = "default",
) -> str:
    if namespace:
        return f"{package}.{namespace}.{name}"
    return f"{package}.{name}"


def test_enum_fqn(
    name: str,
    *,
    package: str = "tests.meta",
    namespace: str = "default",
) -> str:
    if namespace:
        return f"{package}.{namespace}.{name}"
    return f"{package}.{name}"


test_class_fqn.__test__ = False
test_enum_fqn.__test__ = False


def make_class_config(
    name: str,
    *,
    class_fqn: str,
    **kwargs: Any,
) -> ClassConfig:
    return ClassConfig(
        name=name,
        class_fqn=class_fqn,
        **kwargs,
    )


def make_enum_config(
    name: str,
    *,
    enum_fqn: str,
    **kwargs: Any,
) -> EnumConfig:
    return EnumConfig(
        name=name,
        enum_fqn=enum_fqn,
        **kwargs,
    )


def make_attribute_config(
    *,
    owner_key: str,
    name: str,
    **kwargs: Any,
) -> AttributeConfig:
    return AttributeConfig(
        owner_key=owner_key,
        name=name,
        **kwargs,
    )


def make_function_config(
    *,
    owner_key: str,
    name: str,
    kind: Any,
    **kwargs: Any,
) -> FunctionConfig:
    return FunctionConfig(
        owner_key=owner_key,
        name=name,
        kind=kind,
        **kwargs,
    )


def test_function_attribute_owner_key(
    *,
    function_owner_key: str,
    function_name: str,
    type: Any,
) -> str:
    resolved_type = getattr(type, "value", type)
    return f"{function_owner_key}.{function_name}::{resolved_type}"


test_function_attribute_owner_key.__test__ = False


def make_class_attribute_edge(
    *,
    class_config_id: UUID,
    attribute_config: AttributeConfig,
    name: str | None = None,
    **kwargs: Any,
) -> ClassConfigAttributeConfig:
    if name is not None and name != attribute_config.name:
        raise ValueError(
            "make_class_attribute_edge redundant name must match attribute_config.name "
            + f"(name={name!r}, attribute_config.name={attribute_config.name!r})"
        )
    payload: dict[str, Any] = {
        "class_config_id": class_config_id,
        "attribute_config": attribute_config,
        "attribute_config_id": attribute_config.id,
    }
    payload.update(kwargs)
    return ClassConfigAttributeConfig(
        **payload,
    )


def make_function_attribute_edge(
    *,
    function_config_id: UUID,
    attribute_config: AttributeConfig,
    name: str,
    type: Any,
    **kwargs: Any,
) -> FunctionConfigAttributeConfig:
    return FunctionConfigAttributeConfig(
        function_config_id=function_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config.id,
        name=name,
        type=type,
        **kwargs,
    )


def make_relationship(
    *,
    class_config_id: UUID,
    target_class_config_id: UUID,
    relationship_type: Any,
    relationship_key: str | None = None,
    **kwargs: Any,
) -> ClassConfigRelationship:
    resolved_relationship_type = getattr(relationship_type, "value", relationship_type)
    return ClassConfigRelationship(
        class_config_id=class_config_id,
        target_class_config_id=target_class_config_id,
        relationship_type=relationship_type,
        relationship_key=relationship_key
        or f"{resolved_relationship_type}:{class_config_id}:{target_class_config_id}",
        **kwargs,
    )


def make_ocg_node(
    *,
    object_config_graph_id: UUID,
    type: Any,
    node_key: str | None = None,
    class_config: ClassConfig | None = None,
    enum_config: EnumConfig | None = None,
    class_config_relationship: ClassConfigRelationship | None = None,
    **kwargs: Any,
) -> ObjectConfigGraphNode:
    resolved_node_key = node_key
    if resolved_node_key is None:
        if class_config is not None:
            resolved_node_key = class_config.class_fqn
        elif enum_config is not None:
            resolved_node_key = enum_config.enum_fqn
        elif class_config_relationship is not None:
            resolved_node_key = class_config_relationship.relationship_key
    if resolved_node_key is None:
        raise ValueError("make_ocg_node requires explicit node_key or a keyed contained entity")

    return ObjectConfigGraphNode(
        object_config_graph_id=object_config_graph_id,
        type=type,
        node_key=resolved_node_key,
        class_config=class_config,
        enum_config=enum_config,
        class_config_relationship=class_config_relationship,
        **kwargs,
    )


def make_rooted_object_instance_graph(
    *,
    object_config_graph: ObjectConfigGraph,
    object_projection_graph: ObjectProjectionGraph,
    root_source_object_id: UUID,
    oig_id: UUID,
    key: str = "g",
    name: str = "g",
    description: str = "d",
    root_class_config_id: UUID | None = None,
) -> ObjectInstanceGraph:
    return build_rooted_object_instance_graph_base(
        key=key,
        name=name,
        description=description,
        object_config_graph=object_config_graph,
        object_projection_graph=object_projection_graph,
        root_source_object_id=root_source_object_id,
        root_class_config_id=root_class_config_id,
        oig_id=oig_id,
    )
