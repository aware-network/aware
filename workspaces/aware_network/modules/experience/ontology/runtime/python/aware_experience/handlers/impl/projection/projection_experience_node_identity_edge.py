from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_identity_edge import (
    ProjectionExperienceNodeIdentityEdge,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import stable_projection_experience_node_identity_edge_id

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph import ProjectionExperienceGraph

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_graph(
    projection_experience_graph_id: UUID,
    parent_projection_experience_node_identity_id: UUID,
    child_projection_experience_node_identity_id: UUID,
    key: str | None = None,
) -> ProjectionExperienceNodeIdentityEdge:
    """
    Create deterministic ProjectionExperienceNodeIdentityEdge.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_graph
    if parent_projection_experience_node_identity_id == child_projection_experience_node_identity_id:
        raise RuntimeError(
            "ProjectionExperienceNodeIdentityEdge.build_via_projection_experience_graph requires "
            + "distinct parent and child node identity ids"
        )

    session = current_handler_session()
    projection_experience_graph = session.imap_get(ProjectionExperienceGraph, projection_experience_graph_id)
    if projection_experience_graph is None:
        raise RuntimeError(
            "ProjectionExperienceNodeIdentityEdge.build_via_projection_experience_graph requires known "
            + f"ProjectionExperienceGraph: projection_experience_graph_id={projection_experience_graph_id}"
        )

    normalized_key = (key or "").strip() or None
    projection_experience_node_identity_edge_id = stable_projection_experience_node_identity_edge_id(
        projection_experience_graph_id=projection_experience_graph_id,
        parent_projection_experience_node_identity_id=parent_projection_experience_node_identity_id,
        child_projection_experience_node_identity_id=child_projection_experience_node_identity_id,
    )
    existing = session.imap_get(
        ProjectionExperienceNodeIdentityEdge,
        projection_experience_node_identity_edge_id,
    )
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.projection_experience_graph_id != projection_experience_graph_id
            or existing.parent_projection_experience_node_identity_id != parent_projection_experience_node_identity_id
            or existing.child_projection_experience_node_identity_id != child_projection_experience_node_identity_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "ProjectionExperienceNodeIdentityEdge.build_via_projection_experience_graph payload mismatch "
                + "for existing edge: "
                + f"projection_experience_node_identity_edge_id={projection_experience_node_identity_edge_id}"
            )
        return existing

    return ProjectionExperienceNodeIdentityEdge(
        id=projection_experience_node_identity_edge_id,
        projection_experience_graph_id=projection_experience_graph_id,
        parent_projection_experience_node_identity_id=parent_projection_experience_node_identity_id,
        child_projection_experience_node_identity_id=child_projection_experience_node_identity_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_graph
