from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph_relationship import ObjectProjectionGraphRelationship

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_projection_graph_relationship_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_object_projection_graph(
    object_projection_graph_id: UUID,
    target_object_projection_graph_id: UUID,
    class_config_relationship_id: UUID,
    source_object_projection_graph_node_id: UUID,
    target_object_projection_graph_node_id: UUID,
) -> ObjectProjectionGraphRelationship:
    """
    Create deterministic ObjectProjectionGraphRelationship under one ObjectProjectionGraph.

    Contract:
    - Parent `object_projection_graph_id` is propagated by constructor lowering.
    - Identity is always source-OPG-scoped.
    """

    # --- AWARE: LOGIC START build_via_object_projection_graph
    object_projection_graph_relationship_id = stable_object_projection_graph_relationship_id(
        object_projection_graph_id=object_projection_graph_id,
        target_object_projection_graph_id=target_object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
        source_object_projection_graph_node_id=source_object_projection_graph_node_id,
        target_object_projection_graph_node_id=target_object_projection_graph_node_id,
    )
    session = current_handler_session()
    existing = session.imap_get(
        ObjectProjectionGraphRelationship,
        object_projection_graph_relationship_id,
    )
    if existing is not None:
        if (
            existing.object_projection_graph_id != object_projection_graph_id
            or existing.target_object_projection_graph_id != target_object_projection_graph_id
            or existing.class_config_relationship_id != class_config_relationship_id
            or existing.source_object_projection_graph_node_id != source_object_projection_graph_node_id
            or existing.target_object_projection_graph_node_id != target_object_projection_graph_node_id
        ):
            raise RuntimeError(
                "ObjectProjectionGraphRelationship.build_via_object_projection_graph payload mismatch for "
                "existing ObjectProjectionGraphRelationship: "
                f"object_projection_graph_relationship_id={object_projection_graph_relationship_id}"
            )
        return existing

    return ObjectProjectionGraphRelationship(
        id=object_projection_graph_relationship_id,
        object_projection_graph_id=object_projection_graph_id,
        target_object_projection_graph_id=target_object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
        source_object_projection_graph_node_id=source_object_projection_graph_node_id,
        target_object_projection_graph_node_id=target_object_projection_graph_node_id,
    )
    # --- AWARE: LOGIC END build_via_object_projection_graph
