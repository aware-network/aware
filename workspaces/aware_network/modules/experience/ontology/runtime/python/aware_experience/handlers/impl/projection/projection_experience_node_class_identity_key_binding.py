from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_class_identity_key_binding import (
    ProjectionExperienceNodeClassIdentityKeyBinding,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import (
    stable_projection_experience_node_class_identity_key_binding_id,
)

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_key import (
    ProjectionExperienceNodeKey,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_node_class_identity(
    projection_experience_node_class_identity_id: UUID,
    projection_experience_node_key_id: UUID,
    value: JsonObject | None = None,
) -> ProjectionExperienceNodeClassIdentityKeyBinding:
    """
    Create deterministic ProjectionExperienceNodeClassIdentityKeyBinding.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_node_class_identity
    session = current_handler_session()
    projection_experience_node_class_identity = session.imap_get(
        ProjectionExperienceNodeClassIdentity,
        projection_experience_node_class_identity_id,
    )
    if projection_experience_node_class_identity is None:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityKeyBinding.build_via_projection_experience_node_class_identity "
            + "requires known ProjectionExperienceNodeClassIdentity: "
            + "projection_experience_node_class_identity_id="
            + f"{projection_experience_node_class_identity_id}"
        )
    projection_experience_node_key = session.imap_get(
        ProjectionExperienceNodeKey,
        projection_experience_node_key_id,
    )
    if projection_experience_node_key is None:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityKeyBinding.build_via_projection_experience_node_class_identity "
            + "requires known ProjectionExperienceNodeKey: "
            + f"projection_experience_node_key_id={projection_experience_node_key_id}"
        )
    projection_experience_node_identity = session.imap_get(
        ProjectionExperienceNodeIdentity,
        projection_experience_node_class_identity.projection_experience_node_identity_id,
    )
    if projection_experience_node_identity is None:
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityKeyBinding.build_via_projection_experience_node_class_identity "
            + "requires known ProjectionExperienceNodeIdentity for "
            + "projection_experience_node_class_identity_id="
            + f"{projection_experience_node_class_identity_id}"
        )
    if (
        projection_experience_node_key.projection_experience_node_id
        != projection_experience_node_identity.projection_experience_node_id
    ):
        raise RuntimeError(
            "ProjectionExperienceNodeClassIdentityKeyBinding.build_via_projection_experience_node_class_identity "
            + "key-node mismatch: "
            + f"projection_experience_node_key_id={projection_experience_node_key_id} "
            + "does not belong to "
            + f"projection_experience_node_identity_id={projection_experience_node_identity.id}"
        )

    projection_experience_node_class_identity_key_binding_id = (
        stable_projection_experience_node_class_identity_key_binding_id(
            projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
            projection_experience_node_key_id=projection_experience_node_key_id,
        )
    )
    existing = session.imap_get(
        ProjectionExperienceNodeClassIdentityKeyBinding,
        projection_experience_node_class_identity_key_binding_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_node_class_identity_id != projection_experience_node_class_identity_id
            or existing.projection_experience_node_key_id != projection_experience_node_key_id
            or existing.value != value
        ):
            raise RuntimeError(
                "ProjectionExperienceNodeClassIdentityKeyBinding.build_via_projection_experience_node_class_identity "
                + "payload mismatch for existing association: "
                + "projection_experience_node_class_identity_key_binding_id="
                + f"{projection_experience_node_class_identity_key_binding_id}"
            )
        return existing

    return ProjectionExperienceNodeClassIdentityKeyBinding(
        id=projection_experience_node_class_identity_key_binding_id,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
        projection_experience_node_key_id=projection_experience_node_key_id,
        value=value,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_node_class_identity
