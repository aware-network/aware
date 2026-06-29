"""
Describe an ObjectProjectionGraph in natural language.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID
from typing import NamedTuple

from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
)

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

from aware_utils.logging import logger


class _EdgeTraversal(NamedTuple):
    neighbor_id: UUID
    direction_label: str
    relationship_type: str
    include: str
    multiplicity: str
    relationship_id: UUID


def get_natural_language_description(
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    *,
    external_graphs: Iterable[ObjectConfigGraph] | None = None,
) -> str:
    """Build a topology-focused natural language description for an ObjectProjectionGraph."""

    class_name_by_class_id: dict[UUID, str] = {}
    class_relationships_by_id: dict[UUID, ClassConfigRelationship] = {}

    graphs_to_index: list[ObjectConfigGraph] = [ocg]
    if external_graphs is not None:
        graphs_to_index.extend(list(external_graphs))
    # In-memory cross-OCG links may carry hydrated target graphs (not persisted on JSON).
    for ocg_rel in ocg.object_config_graph_relationships:
        tgt = ocg_rel.target_object_config_graph
        if tgt is None:
            continue
        if all(existing.id != tgt.id for existing in graphs_to_index):
            graphs_to_index.append(tgt)

    for graph in graphs_to_index:
        for node in graph.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_:
                if node.class_config is None:
                    raise ValueError(f"ClassConfig not found for node {node.id}")
                class_name_by_class_id[node.class_config.id] = node.class_config.name
            elif node.type == ObjectConfigGraphNodeType.relationship:
                if node.class_config_relationship is None:
                    raise ValueError(f"ClassConfigRelationship not found for node {node.id}")
                class_relationships_by_id[node.class_config_relationship.id] = node.class_config_relationship
        # Cross-OCG relationships may be materialized as detached relationship objects.
        for ocg_rel in graph.object_config_graph_relationships:
            for rel in ocg_rel.class_config_relationships:
                class_relationships_by_id.setdefault(rel.id, rel)

    def resolve_class_name(class_config_id: UUID | None) -> str:
        if class_config_id is None:
            return "Unknown"
        return class_name_by_class_id.get(class_config_id, str(class_config_id))

    name = opg.name or "Unnamed Projection"
    description = opg.description or ""
    root_class_config_ids: list[UUID] = []
    node_ids: list[UUID] = []

    # Capture all nodes and determine roots.
    for node in opg.object_projection_graph_nodes:
        node_class_config_id = node.class_config_id
        node_ids.append(node_class_config_id)
        if node.is_root:
            root_class_config_ids.append(node_class_config_id)

    if not root_class_config_ids:
        logger.error("Root class config id not found")
        return f"No root class config id found for OPG {name}"

    # Gather adjacency data for hierarchical traversal.
    adjacency: dict[UUID, list[_EdgeTraversal]] = {}
    for edge in opg.object_projection_graph_edges:
        relationship = class_relationships_by_id.get(edge.class_config_relationship_id)
        if relationship is None:
            logger.error(f"Relationship {edge.class_config_relationship_id} not found for edge {edge.id}")
            continue

        source_id = relationship.class_config_id
        target_id = relationship.target_class_config_id
        if source_id is None or target_id is None:
            logger.error(f"Relationship {edge.class_config_relationship_id} missing endpoint ids")
            continue

        traversal_direction = edge.traversal_direction
        traversal_direction_label = traversal_direction.name

        # IMPORTANT: Do NOT implicitly add reverse traversals.
        # The OPG lens is the SSOT for traversal direction.
        if traversal_direction == ClassConfigRelationshipDirection.forward:
            parent_id = source_id
            neighbor_id = target_id
        else:
            parent_id = target_id
            neighbor_id = source_id

        adjacency.setdefault(parent_id, []).append(
            _EdgeTraversal(
                neighbor_id=neighbor_id,
                direction_label=traversal_direction_label,
                relationship_type=relationship.relationship_type.name,
                include=edge.include.name,
                multiplicity=edge.multiplicity.name,
                relationship_id=relationship.id,
            )
        )

    def render_tree(node_id: UUID, indent: int, visited: set[UUID], output: list[str]) -> None:
        entries = adjacency.get(node_id, [])
        entries = sorted(
            entries,
            key=lambda entry: (
                resolve_class_name(entry.neighbor_id),
                str(entry.relationship_id),
            ),
        )
        for entry in entries:
            neighbor_id = entry.neighbor_id
            prefix = "  " * indent
            neighbor_name = resolve_class_name(neighbor_id)
            line = (
                f"{prefix}- [{entry.direction_label}] type={entry.relationship_type}, "
                f"include={entry.include}, multiplicity={entry.multiplicity} "
                f"-> {neighbor_name} (cc_id={neighbor_id}) "
                f"[relationship_id={entry.relationship_id}"
            )

            if neighbor_id in visited:
                output.append(f"{line} (already visited)")
                continue

            output.append(line)
            visited.add(neighbor_id)
            render_tree(neighbor_id, indent + 1, visited, output)

    # Build node summary with deterministic ordering for quick reference.
    unique_node_ids = sorted(set(node_ids), key=lambda value: str(value))
    node_summaries = [f"{resolve_class_name(node_id)} (cc_id={node_id})" for node_id in unique_node_ids]

    header = f'ObjectProjectionGraph "{name}"'
    if description:
        header += f" — {description}"

    lines: list[str] = [
        header,
        f"Nodes ({len(unique_node_ids)} total): {', '.join(node_summaries)}.",
        "Topology:",
    ]

    for root_id in sorted(root_class_config_ids, key=str):
        root_name = resolve_class_name(root_id)
        lines.append(f"- {root_name} (cc_id={root_id})")
        visited_nodes = {root_id}
        render_tree(root_id, 1, visited_nodes, lines)

    return "\n".join(lines)
