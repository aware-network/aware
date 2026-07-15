from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_key import ProjectionExperienceNodeKey

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import stable_projection_experience_node_key_id

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph_node_key import (
    ObjectProjectionGraphNodeKey,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_node(
    projection_experience_node_id: UUID, object_projection_graph_node_key_id: UUID
) -> ProjectionExperienceNodeKey:
    """
    Create deterministic ProjectionExperienceNodeKey compatibility edge.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_node
    session = current_handler_session()
    projection_experience_node = session.imap_get(
        ProjectionExperienceNode,
        projection_experience_node_id,
    )
    if projection_experience_node is None:
        raise RuntimeError(
            "ProjectionExperienceNodeKey.build_via_projection_experience_node requires known "
            + f"ProjectionExperienceNode: projection_experience_node_id={projection_experience_node_id}"
        )
    object_projection_graph_node_key = session.imap_get(
        ObjectProjectionGraphNodeKey,
        object_projection_graph_node_key_id,
    )
    if object_projection_graph_node_key is None:
        raise RuntimeError(
            "ProjectionExperienceNodeKey.build_via_projection_experience_node requires known "
            + "ObjectProjectionGraphNodeKey: "
            + f"object_projection_graph_node_key_id={object_projection_graph_node_key_id}"
        )
    if (
        object_projection_graph_node_key.object_projection_graph_node_id
        != projection_experience_node.object_projection_graph_node_id
    ):
        raise RuntimeError(
            "ProjectionExperienceNodeKey.build_via_projection_experience_node node mismatch: "
            + f"object_projection_graph_node_key_id={object_projection_graph_node_key_id} "
            + "does not belong to "
            + f"projection_experience_node_id={projection_experience_node_id}"
        )

    projection_experience_node_key_id = stable_projection_experience_node_key_id(
        projection_experience_node_id=projection_experience_node_id,
        object_projection_graph_node_key_id=object_projection_graph_node_key_id,
    )
    existing = session.imap_get(ProjectionExperienceNodeKey, projection_experience_node_key_id)
    if existing is not None:
        if (
            existing.projection_experience_node_id != projection_experience_node_id
            or existing.object_projection_graph_node_key_id != object_projection_graph_node_key_id
        ):
            raise RuntimeError(
                "ProjectionExperienceNodeKey.build_via_projection_experience_node payload mismatch "
                + "for existing key: "
                + f"projection_experience_node_key_id={projection_experience_node_key_id}"
            )
        return existing

    return ProjectionExperienceNodeKey(
        id=projection_experience_node_key_id,
        projection_experience_node_id=projection_experience_node_id,
        object_projection_graph_node_key=object_projection_graph_node_key,
        object_projection_graph_node_key_id=object_projection_graph_node_key_id,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_node
