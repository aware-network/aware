from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_identity import ProjectionExperienceNodeIdentity

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import stable_projection_experience_node_identity_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_node(
    projection_experience_node_id: UUID, key: str
) -> ProjectionExperienceNodeIdentity:
    """
    Create deterministic ProjectionExperienceNodeIdentity association edge.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_node
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError(
            "ProjectionExperienceNodeIdentity.build_via_projection_experience_node requires non-empty key"
        )

    session = current_handler_session()
    projection_experience_node_identity_id = stable_projection_experience_node_identity_id(
        projection_experience_node_id=projection_experience_node_id,
        key=normalized_key,
    )
    existing = session.imap_get(ProjectionExperienceNodeIdentity, projection_experience_node_identity_id)
    if existing is not None:
        if existing.projection_experience_node_id != projection_experience_node_id or existing.key != normalized_key:
            raise RuntimeError(
                "ProjectionExperienceNodeIdentity.build_via_projection_experience_node payload mismatch "
                + "for existing identity: "
                + f"projection_experience_node_identity_id={projection_experience_node_identity_id}"
            )
        return existing

    return ProjectionExperienceNodeIdentity(
        id=projection_experience_node_identity_id,
        projection_experience_node_id=projection_experience_node_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_node
