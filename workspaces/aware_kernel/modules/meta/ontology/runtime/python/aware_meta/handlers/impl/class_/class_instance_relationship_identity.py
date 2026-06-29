from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_instance_relationship_identity import ClassInstanceRelationshipIdentity

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_class_instance_relationship_identity_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_object_instance_graph_identity(
    object_instance_graph_identity_id: UUID, class_instance_relationship_id: UUID, label: str | None = None
) -> ClassInstanceRelationshipIdentity:
    """
    Create a deterministic ClassInstanceRelationshipIdentity worldline row.
    """

    # --- AWARE: LOGIC START create_via_object_instance_graph_identity
    class_instance_relationship_identity_id = stable_class_instance_relationship_identity_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        class_instance_relationship_id=class_instance_relationship_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ClassInstanceRelationshipIdentity, class_instance_relationship_identity_id)
    if existing is not None:
        if (
            existing.object_instance_graph_identity_id != object_instance_graph_identity_id
            or (existing.class_instance_relationship_id != class_instance_relationship_id)
            or (existing.label or None) != (label or None)
        ):
            raise RuntimeError(
                "ClassInstanceRelationshipIdentity.create_via_object payload mismatch for existing "
                "ClassInstanceRelationshipIdentity: "
                f"class_instance_relationship_identity_id={class_instance_relationship_identity_id}"
            )
        return existing

    return ClassInstanceRelationshipIdentity(
        id=class_instance_relationship_identity_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        class_instance_relationship_id=class_instance_relationship_id,
        label=label,
    )
    # --- AWARE: LOGIC END create_via_object_instance_graph_identity
