from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import ObjectProjectionGraphEdge

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_projection_graph_edge_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_object_projection_graph(
    object_projection_graph_id: UUID,
    class_config_relationship_id: UUID,
    include: ObjectProjectionGraphEdgeInclude = ObjectProjectionGraphEdgeInclude.required,
    multiplicity: ObjectProjectionGraphEdgeMultiplicity = ObjectProjectionGraphEdgeMultiplicity.many,
    traversal_direction: ClassConfigRelationshipDirection = ClassConfigRelationshipDirection.forward,
    depth_limit: int | None = None,
    attribute_role: ObjectProjectionGraphAttributeRole = ObjectProjectionGraphAttributeRole.reference,
    loading_override: ClassConfigRelationshipSideLoadingStrategy | None = None,
) -> ObjectProjectionGraphEdge:
    """
    Create deterministic ObjectProjectionGraphEdge under one ObjectProjectionGraph.

    Contract:
    - Parent `object_projection_graph_id` is propagated by constructor lowering.
    - Identity is always OPG-scoped.
    """

    # --- AWARE: LOGIC START build_via_object_projection_graph
    object_projection_graph_edge_id = stable_object_projection_graph_edge_id(
        object_projection_graph_id=object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ObjectProjectionGraphEdge, object_projection_graph_edge_id)
    if existing is not None:
        if (
            existing.object_projection_graph_id != object_projection_graph_id
            or existing.class_config_relationship_id != class_config_relationship_id
            or existing.include != include
            or existing.multiplicity != multiplicity
            or existing.traversal_direction != traversal_direction
            or existing.depth_limit != depth_limit
            or existing.attribute_role != attribute_role
            or existing.loading_override != loading_override
        ):
            raise RuntimeError(
                "ObjectProjectionGraphEdge.build_via_object_projection_graph payload mismatch for existing "
                f"ObjectProjectionGraphEdge: object_projection_graph_edge_id={object_projection_graph_edge_id}"
            )
        return existing

    return ObjectProjectionGraphEdge(
        id=object_projection_graph_edge_id,
        object_projection_graph_id=object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
        include=include,
        multiplicity=multiplicity,
        traversal_direction=traversal_direction,
        depth_limit=depth_limit,
        attribute_role=attribute_role,
        loading_override=loading_override,
    )
    # --- AWARE: LOGIC END build_via_object_projection_graph
