from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph_identity_edge import (
    ProjectionExperienceGraphIdentityEdge,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import stable_projection_experience_graph_identity_edge_id

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph import ProjectionExperienceGraph
from aware_experience_ontology.projection.projection_experience_graph_identity import (
    ProjectionExperienceGraphIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_identity_edge import (
    ProjectionExperienceNodeIdentityEdge,
)

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_graph(
    projection_experience_graph_id: UUID,
    parent_projection_experience_graph_identity_id: UUID,
    child_projection_experience_graph_identity_id: UUID,
    projection_experience_node_identity_edge_id: UUID,
    key: str | None = None,
) -> ProjectionExperienceGraphIdentityEdge:
    """
    Create deterministic ProjectionExperienceGraphIdentityEdge.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_graph
    if parent_projection_experience_graph_identity_id == child_projection_experience_graph_identity_id:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph requires "
            + "distinct parent and child graph identity ids"
        )

    session = current_handler_session()
    projection_experience_graph = session.imap_get(ProjectionExperienceGraph, projection_experience_graph_id)
    if projection_experience_graph is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph requires known "
            + f"ProjectionExperienceGraph: projection_experience_graph_id={projection_experience_graph_id}"
        )

    parent_graph_identity = session.imap_get(
        ProjectionExperienceGraphIdentity,
        parent_projection_experience_graph_identity_id,
    )
    if parent_graph_identity is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph requires known parent "
            + "ProjectionExperienceGraphIdentity: "
            + f"parent_projection_experience_graph_identity_id={parent_projection_experience_graph_identity_id}"
        )
    child_graph_identity = session.imap_get(
        ProjectionExperienceGraphIdentity,
        child_projection_experience_graph_identity_id,
    )
    if child_graph_identity is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph requires known child "
            + "ProjectionExperienceGraphIdentity: "
            + f"child_projection_experience_graph_identity_id={child_projection_experience_graph_identity_id}"
        )
    if parent_graph_identity.projection_experience_graph_id != projection_experience_graph_id:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph parent graph mismatch: "
            + f"parent.projection_experience_graph_id={parent_graph_identity.projection_experience_graph_id} "
            + f"graph={projection_experience_graph_id}"
        )
    if child_graph_identity.projection_experience_graph_id != projection_experience_graph_id:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph child graph mismatch: "
            + f"child.projection_experience_graph_id={child_graph_identity.projection_experience_graph_id} "
            + f"graph={projection_experience_graph_id}"
        )

    node_identity_edge = session.imap_get(
        ProjectionExperienceNodeIdentityEdge,
        projection_experience_node_identity_edge_id,
    )
    if node_identity_edge is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph requires known "
            + "ProjectionExperienceNodeIdentityEdge: "
            + f"projection_experience_node_identity_edge_id={projection_experience_node_identity_edge_id}"
        )
    if node_identity_edge.projection_experience_graph_id != projection_experience_graph_id:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph semantic-edge graph mismatch: "
            + f"node_identity_edge.projection_experience_graph_id={node_identity_edge.projection_experience_graph_id} "
            + f"graph={projection_experience_graph_id}"
        )
    if (
        parent_graph_identity.projection_experience_node_identity_id
        != node_identity_edge.parent_projection_experience_node_identity_id
        or child_graph_identity.projection_experience_node_identity_id
        != node_identity_edge.child_projection_experience_node_identity_id
    ):
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph requires graph "
            + "identity endpoints to match semantic ProjectionExperienceNodeIdentityEdge endpoints"
        )

    normalized_key = (key or "").strip() or None
    projection_experience_graph_identity_edge_id = stable_projection_experience_graph_identity_edge_id(
        projection_experience_graph_id=projection_experience_graph_id,
        parent_projection_experience_graph_identity_id=parent_projection_experience_graph_identity_id,
        child_projection_experience_graph_identity_id=child_projection_experience_graph_identity_id,
        projection_experience_node_identity_edge_id=projection_experience_node_identity_edge_id,
    )
    existing = session.imap_get(
        ProjectionExperienceGraphIdentityEdge,
        projection_experience_graph_identity_edge_id,
    )
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.projection_experience_graph_id != projection_experience_graph_id
            or existing.parent_projection_experience_graph_identity_id != parent_projection_experience_graph_identity_id
            or existing.child_projection_experience_graph_identity_id != child_projection_experience_graph_identity_id
            or existing.projection_experience_node_identity_edge_id != projection_experience_node_identity_edge_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "ProjectionExperienceGraphIdentityEdge.build_via_projection_experience_graph payload mismatch "
                + "for existing edge: "
                + f"projection_experience_graph_identity_edge_id={projection_experience_graph_identity_edge_id}"
            )
        return existing

    return ProjectionExperienceGraphIdentityEdge(
        id=projection_experience_graph_identity_edge_id,
        projection_experience_graph_id=projection_experience_graph_id,
        parent_projection_experience_graph_identity_id=parent_projection_experience_graph_identity_id,
        child_projection_experience_graph_identity_id=child_projection_experience_graph_identity_id,
        projection_experience_node_identity_edge_id=projection_experience_node_identity_edge_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_graph
