from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

# Kernel Graph Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

# Meta
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.model_bootstrap import get_node_function_config


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphNamespaceIndex:
    """Deterministic namespace index derived from canonical node FQNs."""

    node_namespace_by_node_id: dict[UUID, NamespacePath]
    class_fqn_to_class_config: dict[str, ClassConfig]


def build_node_namespace_by_node_id(
    object_config_graph: ObjectConfigGraph,
) -> dict[UUID, NamespacePath]:
    """Build node_id -> NamespacePath from canonical node FQNs."""

    package = object_config_graph.fqn_prefix
    idx: dict[UUID, NamespacePath] = {}
    class_namespace_by_class_config_id: dict[UUID, NamespacePath] = {}
    for node in object_config_graph.object_config_graph_nodes:
        ns = _namespace_for_node(package=package, node=node)
        if ns is None:
            continue
        idx[node.id] = ns
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            class_namespace_by_class_config_id[node.class_config.id] = ns

    for node in object_config_graph.object_config_graph_nodes:
        if (
            node.type != ObjectConfigGraphNodeType.relationship
            or node.class_config_relationship is None
        ):
            continue
        source_class_config_id = node.class_config_relationship.class_config_id
        if source_class_config_id is None:
            continue
        ns = class_namespace_by_class_config_id.get(source_class_config_id)
        if ns is not None:
            idx[node.id] = ns
    return idx


def build_namespace_index(
    object_config_graph: ObjectConfigGraph,
) -> ObjectConfigGraphNamespaceIndex:
    """Build deterministic per-graph indexes derived from canonical FQNs."""

    node_ns = build_node_namespace_by_node_id(object_config_graph)
    class_fqn_to_class_config: dict[str, ClassConfig] = {}
    for node in object_config_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        if node.class_config.parent_class_id is not None:
            continue
        fqn = class_node_fqn(object_config_graph, node, node_namespace_by_node_id=node_ns)
        if fqn is None:
            continue
        prev = class_fqn_to_class_config.get(fqn)
        if prev is not None and prev.id != node.class_config.id:
            raise ValueError(
                f"Duplicate OBJECT FQN within graph {object_config_graph.id}: {fqn} "
                f"(prev_class_id={prev.id}, class_id={node.class_config.id})"
            )
        class_fqn_to_class_config[fqn] = node.class_config

    return ObjectConfigGraphNamespaceIndex(
        node_namespace_by_node_id=node_ns,
        class_fqn_to_class_config=class_fqn_to_class_config,
    )


def class_node_fqn(
    object_config_graph: ObjectConfigGraph,
    node: ObjectConfigGraphNode,
    node_namespace_by_node_id: dict[UUID, NamespacePath] | None = None,
) -> str | None:
    """Return fully qualified name for a class node."""

    _ = object_config_graph
    _ = node_namespace_by_node_id
    if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
        return None
    return node.class_config.class_fqn


def _namespace_for_node(
    *,
    package: str,
    node: ObjectConfigGraphNode,
) -> NamespacePath | None:
    fqn: str | None = None
    if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
        fqn = node.class_config.class_fqn
    elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
        fqn = node.enum_config.enum_fqn
    elif node.type == ObjectConfigGraphNodeType.function:
        function_config = get_node_function_config(node)
        if function_config is not None:
            fqn = function_config.owner_key
    if not fqn:
        return None
    namespace = _namespace_from_fqn(package=package, fqn=fqn)
    if namespace is None:
        return None
    return NamespacePath(package=package, namespace=namespace)


def _namespace_from_fqn(*, package: str, fqn: str) -> str | None:
    parts = [part.strip() for part in fqn.split(".") if part.strip()]
    if len(parts) < 2 or parts[0] != package:
        return None
    return ".".join(parts[1:-1])
