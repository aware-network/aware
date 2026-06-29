from __future__ import annotations

from collections.abc import Callable
import time
from typing import cast

from pydantic import BaseModel

from aware_meta.graph.config.runtime_derivation.timer import RuntimeDerivationTimer
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)


def clone_source_graph_for_runtime_handoff(
    graph: ObjectConfigGraph,
    *,
    timer: RuntimeDerivationTimer | None = None,
    label: str = "clone_source_graph_handoff",
) -> ObjectConfigGraph:
    """
    Clone source/compiler IR before runtime derivation without a full graph
    deepcopy.

    The Aware runtime transformer mutates class, relationship, and attribute
    containers while building runtime topology. It reads build-only provenance
    such as CodeSection pointers, annotations, and projection declarations. This
    handoff clones the mutable containers and shares read-only provenance refs
    so the source graph stays isolated without paying full deep-copy cost.
    """

    start = time.perf_counter()
    out = _clone_graph_for_mutable_handoff(graph)
    if timer is not None:
        timer.add(f"{label}.shallow", time.perf_counter() - start)
    return out


def clone_runtime_graph_for_stage_mutation(
    source: ObjectConfigGraph,
    *,
    timer: RuntimeDerivationTimer | None = None,
) -> ObjectConfigGraph:
    """
    Clone an already-derived runtime graph cheaply before attaching runtime-only
    stage metadata.
    """

    start = time.perf_counter()
    out = source.model_copy(deep=False)
    cloned_nodes: list[ObjectConfigGraphNode] = []
    for node in source.object_config_graph_nodes:
        node_copy = node.model_copy(deep=False)
        if (
            node_copy.type == ObjectConfigGraphNodeType.class_
            and node_copy.class_config is not None
        ):
            node_copy.class_config = node_copy.class_config.model_copy(deep=False)
        elif (
            node_copy.type == ObjectConfigGraphNodeType.relationship
            and node_copy.class_config_relationship is not None
        ):
            node_copy.class_config_relationship = (
                node_copy.class_config_relationship.model_copy(deep=False)
            )
        elif (
            node_copy.type == ObjectConfigGraphNodeType.enum
            and node_copy.enum_config is not None
        ):
            node_copy.enum_config = node_copy.enum_config.model_copy(deep=False)
        elif node_copy.type == ObjectConfigGraphNodeType.function:
            node_function_config = getattr(node_copy, "function_config", None)
            if node_function_config is not None:
                node_copy.function_config = node_function_config.model_copy(deep=False)
        cloned_nodes.append(node_copy)
    out.object_config_graph_nodes = cloned_nodes
    if timer is not None:
        timer.add("clone_runtime_graph.shallow", time.perf_counter() - start)
    return out


def clone_runtime_graph_for_language_transformer_handoff(
    source: ObjectConfigGraph,
    *,
    timer: RuntimeDerivationTimer | None = None,
) -> ObjectConfigGraph:
    """
    Clone the runtime graph shell for language transformers without a full graph
    deepcopy.

    Runtime-to-language transformers are allowed to mutate class, relationship,
    and attribute metadata while lowering. They should not mutate external
    graphs or other read-only closure context. This handoff preserves that
    mutation boundary by cloning the graph containers and mutable runtime
    metadata objects while sharing read-only context.
    """

    start = time.perf_counter()
    out = _clone_graph_for_mutable_handoff(source)

    if timer is not None:
        timer.add(
            "clone_runtime_graph_for_language_transformer_handoff.shallow",
            time.perf_counter() - start,
        )
    return out


def _clone_graph_for_mutable_handoff(source: ObjectConfigGraph) -> ObjectConfigGraph:
    """Clone mutable graph/class/relationship containers for transformer handoff."""

    out = source.model_copy(deep=False)

    attr_by_id: dict[object, object] = {}
    relationship_by_id: dict[object, object] = {}
    class_relationships_by_class_copy: list[tuple[object, list[object]]] = []

    def clone_model(value: object) -> object:
        if isinstance(value, BaseModel):
            return value.model_copy(deep=False)
        return value

    def clone_attribute_config(value: object | None) -> object | None:
        if value is None:
            return None
        attr_id = getattr(value, "id", None)
        if attr_id is not None and attr_id in attr_by_id:
            return attr_by_id[attr_id]
        attr_copy = clone_model(value)
        if attr_id is not None:
            attr_by_id[attr_id] = attr_copy
        return attr_copy

    def clone_class_attribute_link(value: object) -> object:
        link_copy = clone_model(value)
        if isinstance(link_copy, BaseModel):
            attr = getattr(value, "attribute_config", None)
            if attr is not None:
                setattr(
                    link_copy,
                    "attribute_config",
                    clone_attribute_config(attr),
                )
        return link_copy

    def clone_relationship(value: object) -> object:
        relationship_id = getattr(value, "id", None)
        if relationship_id is not None and relationship_id in relationship_by_id:
            return relationship_by_id[relationship_id]
        relationship_copy = clone_model(value)
        if isinstance(relationship_copy, BaseModel):
            relationship_copy.class_config_relationship_attributes = [
                clone_model(attribute_link)
                for attribute_link in (
                    getattr(value, "class_config_relationship_attributes", None) or []
                )
            ]
            association = getattr(
                value,
                "class_config_relationship_association_edge",
                None,
            )
            if association is not None:
                relationship_copy.class_config_relationship_association_edge = (
                    clone_model(association)
                )
        if relationship_id is not None:
            relationship_by_id[relationship_id] = relationship_copy
        return relationship_copy

    cloned_nodes: list[ObjectConfigGraphNode] = []
    for node in source.object_config_graph_nodes:
        node_copy = node.model_copy(deep=False)
        if (
            node_copy.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
        ):
            class_copy = node.class_config.model_copy(deep=False)
            class_copy.class_config_attribute_configs = [
                clone_class_attribute_link(link)
                for link in (node.class_config.class_config_attribute_configs or [])
            ]
            class_relationships_by_class_copy.append(
                (
                    class_copy,
                    list(node.class_config.class_config_relationships or []),
                )
            )
            class_copy.class_config_relationships = []
            node_copy.class_config = class_copy
        elif (
            node_copy.type == ObjectConfigGraphNodeType.relationship
            and node.class_config_relationship is not None
        ):
            node_copy.class_config_relationship = clone_relationship(
                node.class_config_relationship
            )
        elif (
            node_copy.type == ObjectConfigGraphNodeType.enum
            and node.enum_config is not None
        ):
            node_copy.enum_config = node.enum_config.model_copy(deep=False)
        elif node_copy.type == ObjectConfigGraphNodeType.function:
            node_function_config = getattr(node, "function_config", None)
            if node_function_config is not None:
                node_copy.function_config = node_function_config.model_copy(deep=False)
        cloned_nodes.append(node_copy)
    out.object_config_graph_nodes = cloned_nodes

    for class_copy, relationships in class_relationships_by_class_copy:
        if isinstance(class_copy, BaseModel):
            class_copy.class_config_relationships = [
                clone_relationship(relationship) for relationship in relationships
            ]

    out.object_config_graph_relationships = [
        relationship_group.model_copy(
            deep=False,
            update={
                "class_config_relationships": [
                    clone_relationship(relationship)
                    for relationship in (
                        relationship_group.class_config_relationships or []
                    )
                ]
            },
        )
        for relationship_group in (source.object_config_graph_relationships or [])
    ]
    out.object_config_graph_annotations = list(
        source.object_config_graph_annotations or []
    )
    out.object_config_graph_overlays = list(source.object_config_graph_overlays or [])
    out.object_projection_graph_declarations = list(
        source.object_projection_graph_declarations or []
    )
    out.object_projection_graphs = [
        projection_graph.model_copy(deep=False)
        for projection_graph in (source.object_projection_graphs or [])
    ]
    return out


def detach_bound_sessions(root: BaseModel) -> Callable[[], None]:
    saved: list[tuple[BaseModel, object]] = []
    seen: set[int] = set()

    def walk(obj: object) -> None:
        oid = id(obj)
        if oid in seen:
            return
        seen.add(oid)
        if isinstance(obj, BaseModel):
            raw_private = cast(object, obj.__pydantic_private__)
            private = (
                cast(dict[object, object], raw_private)
                if isinstance(raw_private, dict)
                else None
            )
            if private is not None and "_bound_session" in private:
                saved.append((obj, private.get("_bound_session")))
                private["_bound_session"] = None
            for value in cast(
                dict[object, object], cast(object, obj.__dict__)
            ).values():
                walk(value)
            return
        if isinstance(obj, dict):
            for value in obj.values():
                walk(value)
            return
        if isinstance(obj, (list, tuple, set, frozenset)):
            for value in obj:
                walk(value)

    walk(root)

    def restore() -> None:
        for obj, value in saved:
            raw_private = cast(object, obj.__pydantic_private__)
            if isinstance(raw_private, dict):
                raw_private["_bound_session"] = value

    return restore


__all__ = [
    "clone_runtime_graph_for_stage_mutation",
    "clone_runtime_graph_for_language_transformer_handoff",
    "clone_source_graph_for_runtime_handoff",
    "detach_bound_sessions",
]
