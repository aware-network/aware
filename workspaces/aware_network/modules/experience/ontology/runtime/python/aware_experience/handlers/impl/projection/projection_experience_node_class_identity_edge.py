from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_class_identity_edge import (
    ProjectionExperienceNodeClassIdentityEdge,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import (
    stable_projection_experience_node_class_identity_edge_id,
)

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_oigi(
    projection_experience_oigi_id: UUID,
    parent_node_class_identity_id: UUID,
    child_node_class_identity_id: UUID,
    class_instance_relationship_identity_id: UUID,
    key: str | None = None,
) -> ProjectionExperienceNodeClassIdentityEdge:
    """
    Create deterministic ProjectionExperienceNodeClassIdentityEdge.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_oigi
    if parent_node_class_identity_id == child_node_class_identity_id:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityEdge.build_via_projection_experience_oigi requires "
            + "distinct parent_node_class_identity_id and child_node_class_identity_id"
        )

    session = current_handler_session()
    parent = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        parent_node_class_identity_id,
    )
    if parent is None:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityEdge.build_via_projection_experience_oigi requires known "
            + "parent ProjectionExperienceNodeClassIdentity: "
            + f"parent_node_class_identity_id={parent_node_class_identity_id}"
        )
    child = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        child_node_class_identity_id,
    )
    if child is None:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityEdge.build_via_projection_experience_oigi requires known "
            + "child ProjectionExperienceNodeClassIdentity: "
            + f"child_node_class_identity_id={child_node_class_identity_id}"
        )
    if parent.projection_experience_oigi_id != projection_experience_oigi_id:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityEdge.build_via_projection_experience_oigi parent belongs "
            + "to a different OIGI: "
            + f"parent.projection_experience_oigi_id={parent.projection_experience_oigi_id} "
            + f"projection_experience_oigi_id={projection_experience_oigi_id}"
        )
    if child.projection_experience_oigi_id != projection_experience_oigi_id:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityEdge.build_via_projection_experience_oigi child belongs "
            + "to a different OIGI: "
            + f"child.projection_experience_oigi_id={child.projection_experience_oigi_id} "
            + f"projection_experience_oigi_id={projection_experience_oigi_id}"
        )

    normalized_key = (key or "").strip() or None
    projection_experience_node_class_identity_edge_id = stable_projection_experience_node_class_identity_edge_id(
        projection_experience_oigi_id=projection_experience_oigi_id,
        parent_node_class_identity_id=parent_node_class_identity_id,
        child_node_class_identity_id=child_node_class_identity_id,
        class_instance_relationship_identity_id=class_instance_relationship_identity_id,
    )
    existing = session.imap_get(
        ProjectionExperienceNodeClassIdentityEdge,
        projection_experience_node_class_identity_edge_id,
    )
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.projection_experience_oigi_id != projection_experience_oigi_id
            or existing.parent_node_class_identity_id != parent_node_class_identity_id
            or existing.child_node_class_identity_id != child_node_class_identity_id
            or existing.class_instance_relationship_identity_id != class_instance_relationship_identity_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "ProjectionExperienceNodeClassIdentityEdge.build_via_projection_experience_oigi payload mismatch "
                + "for existing association: "
                + "projection_experience_node_class_identity_edge_id="
                + f"{projection_experience_node_class_identity_edge_id}"
            )
        return existing

    return ProjectionExperienceNodeClassIdentityEdge(
        id=projection_experience_node_class_identity_edge_id,
        projection_experience_oigi_id=projection_experience_oigi_id,
        parent_node_class_identity_id=parent_node_class_identity_id,
        child_node_class_identity_id=child_node_class_identity_id,
        class_instance_relationship_identity_id=class_instance_relationship_identity_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_oigi
