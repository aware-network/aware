from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node import ProjectionExperienceNode
from aware_experience_ontology.projection.projection_experience_node_identity import ProjectionExperienceNodeIdentity
from aware_experience_ontology.projection.projection_experience_node_key import ProjectionExperienceNodeKey

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import stable_projection_experience_node_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_identity(
    projection_experience_node: ProjectionExperienceNode, key: str
) -> ProjectionExperienceNodeIdentity:
    """
    Attach one human-stable identity under this ProjectionExperienceNode.
    """

    # --- AWARE: LOGIC START create_identity
    projection_experience_node_id = projection_experience_node.id
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProjectionExperienceNode.create_identity requires non-empty key")

    created = await ProjectionExperienceNodeIdentity.build_via_projection_experience_node(
        projection_experience_node_id=projection_experience_node_id,
        key=normalized_key,
    )
    for existing in projection_experience_node.projection_experience_node_identities:
        if existing.id == created.id:
            return existing
    projection_experience_node.projection_experience_node_identities.append(created)
    return created
    # --- AWARE: LOGIC END create_identity


async def add_key(
    projection_experience_node: ProjectionExperienceNode, object_projection_graph_node_key_id: UUID
) -> ProjectionExperienceNodeKey:
    """
    Attach one canonical ProjectionKey consumer row under this ProjectionExperienceNode.
    """

    # --- AWARE: LOGIC START add_key
    projection_experience_node_id = projection_experience_node.id
    created = await ProjectionExperienceNodeKey.build_via_projection_experience_node(
        projection_experience_node_id=projection_experience_node_id,
        object_projection_graph_node_key_id=object_projection_graph_node_key_id,
    )
    for existing in projection_experience_node.projection_experience_node_keys:
        if existing.id == created.id:
            return existing
    projection_experience_node.projection_experience_node_keys.append(created)
    return created
    # --- AWARE: LOGIC END add_key


async def build_via_projection_experience(
    projection_experience_id: UUID, object_projection_graph_node_id: UUID, key: str
) -> ProjectionExperienceNode:
    """
    Create deterministic ProjectionExperienceNode association edge.
    """

    # --- AWARE: LOGIC START build_via_projection_experience
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProjectionExperienceNode.build_via_projection_experience requires non-empty key")

    session = current_handler_session()
    projection_experience_node_id = stable_projection_experience_node_id(
        projection_experience_id=projection_experience_id,
        object_projection_graph_node_id=object_projection_graph_node_id,
        key=normalized_key,
    )
    existing = session.imap_get(ProjectionExperienceNode, projection_experience_node_id)
    if existing is not None:
        if (
            existing.projection_experience_id != projection_experience_id
            or existing.object_projection_graph_node_id != object_projection_graph_node_id
            or existing.key != normalized_key
        ):
            raise RuntimeError(
                "ProjectionExperienceNode.build_via_projection_experience payload mismatch for existing node: "
                + f"projection_experience_node_id={projection_experience_node_id}"
            )
        return existing

    return ProjectionExperienceNode(
        id=projection_experience_node_id,
        projection_experience_id=projection_experience_id,
        object_projection_graph_node_id=object_projection_graph_node_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience
