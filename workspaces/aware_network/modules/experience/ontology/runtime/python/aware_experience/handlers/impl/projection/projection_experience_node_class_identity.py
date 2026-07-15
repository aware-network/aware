from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity_key_binding import (
    ProjectionExperienceNodeClassIdentityKeyBinding,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import (
    stable_projection_experience_node_class_identity_id,
)

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_key import (
    ProjectionExperienceNodeKey,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_key_binding(
    projection_experience_node_class_identity: ProjectionExperienceNodeClassIdentity,
    projection_experience_node_key_id: UUID,
    value: JsonObject | None = None,
) -> ProjectionExperienceNodeClassIdentityKeyBinding:
    """
    Attach one ProjectionKey resolution payload row under this projection node-class identity bridge.
    """

    # --- AWARE: LOGIC START add_key_binding
    projection_experience_node_class_identity_id = projection_experience_node_class_identity.id
    session = current_handler_session()
    projection_experience_node_key = session.imap_get(
        ProjectionExperienceNodeKey,
        projection_experience_node_key_id,
    )
    if projection_experience_node_key is None:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentity.add_key_binding requires known "
            + f"ProjectionExperienceNodeKey: projection_experience_node_key_id={projection_experience_node_key_id}"
        )
    projection_experience_node_identity = session.imap_get(
        ProjectionExperienceNodeIdentity,
        projection_experience_node_class_identity.projection_experience_node_identity_id,
    )
    if projection_experience_node_identity is None:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentity.add_key_binding requires known "
            + "ProjectionExperienceNodeIdentity for "
            + f"projection_experience_node_class_identity_id={projection_experience_node_class_identity_id}"
        )
    if (
        projection_experience_node_key.projection_experience_node_id
        != projection_experience_node_identity.projection_experience_node_id
    ):
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentity.add_key_binding key-node mismatch: "
            + f"projection_experience_node_key_id={projection_experience_node_key_id} "
            + "does not belong to "
            + f"projection_experience_node_identity_id={projection_experience_node_identity.id}"
        )

    created = await ProjectionExperienceNodeClassIdentityKeyBinding.build_via_projection_experience_node_class_identity(
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
        projection_experience_node_key_id=projection_experience_node_key_id,
        value=value,
    )
    for existing in projection_experience_node_class_identity.key_bindings:
        if existing.id == created.id:
            return existing
    projection_experience_node_class_identity.key_bindings.append(created)
    return created
    # --- AWARE: LOGIC END add_key_binding


async def build_via_projection_experience_oigi(
    projection_experience_oigi_id: UUID,
    projection_experience_node_identity_id: UUID,
    class_instance_identity_id: UUID,
    key: str,
) -> ProjectionExperienceNodeClassIdentity:
    """
    Create deterministic ProjectionExperienceNodeClassIdentity.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_oigi
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentity.build_via_projection_experience_oigi requires non-empty key"
        )

    session = current_handler_session()
    projection_experience_node_class_identity_id = stable_projection_experience_node_class_identity_id(
        projection_experience_oigi_id=projection_experience_oigi_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        class_instance_identity_id=class_instance_identity_id,
        key=normalized_key,
    )
    existing = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        projection_experience_node_class_identity_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_oigi_id != projection_experience_oigi_id
            or existing.projection_experience_node_identity_id != projection_experience_node_identity_id
            or existing.class_instance_identity_id != class_instance_identity_id
            or existing.key != normalized_key
        ):
            raise RuntimeError(
                "ProjectionExperienceNodeClassIdentity.build_via_projection_experience_oigi payload mismatch "
                + "for existing association: "
                + "projection_experience_node_class_identity_id="
                + f"{projection_experience_node_class_identity_id}"
            )
        return existing

    return ProjectionExperienceNodeClassIdentity(
        id=projection_experience_node_class_identity_id,
        projection_experience_oigi_id=projection_experience_oigi_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        class_instance_identity_id=class_instance_identity_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_oigi
