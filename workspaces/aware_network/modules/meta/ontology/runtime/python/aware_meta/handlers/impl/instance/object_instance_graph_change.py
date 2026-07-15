from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import ObjectInstanceGraphChangeType
from aware_meta_ontology.graph.instance.object_instance_graph_change import ObjectInstanceGraphChange

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_history_ontology.change.change import Change
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_change_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_object_instance_graph_identity(
    object_instance_graph_identity_id: UUID, change_id: UUID, type: ObjectInstanceGraphChangeType
) -> ObjectInstanceGraphChange:
    """
    Create one deterministic ObjectInstanceGraphChange under this ObjectInstanceGraphIdentity.

    Contract:
    - Parent `object_instance_graph_identity_id` is propagated by traversal lowering.
    - The payload `object_instance_graph` is copied from the parent OIGI boundary pointer.
    - Deterministic identity resolves from `(object_instance_graph_identity_id via path, change_id)`.
    """

    # --- AWARE: LOGIC START create_via_object_instance_graph_identity
    session = current_handler_session()
    change_tree_id = stable_object_instance_graph_change_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        change_id=change_id,
    )

    existing = session.imap_get(ObjectInstanceGraphChange, change_tree_id)
    if existing is not None:
        if (
            existing.object_instance_graph_identity_id != object_instance_graph_identity_id
            or existing.change_id != change_id
            or existing.type != type
        ):
            raise RuntimeError(
                "ObjectInstanceGraphChange.create_via_object_instance_graph_identity payload mismatch for existing change tree: "
                + f"object_instance_graph_change_id={change_tree_id}"
            )
        return existing

    parent_identity = session.imap_get(ObjectInstanceGraphIdentity, object_instance_graph_identity_id)
    if parent_identity is None:
        raise RuntimeError(
            "ObjectInstanceGraphChange.create_via_object_instance_graph_identity requires existing "
            + f"ObjectInstanceGraphIdentity: object_instance_graph_identity_id={object_instance_graph_identity_id}"
        )
    if parent_identity.object_instance_graph_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphChange.create_via_object_instance_graph_identity requires "
            + "parent.object_instance_graph_id"
        )

    change = session.imap_get(Change, change_id)
    if change is None:
        raise RuntimeError(
            "ObjectInstanceGraphChange.create_via_object_instance_graph_identity requires existing "
            + f"Change: change_id={change_id}"
        )

    created = ObjectInstanceGraphChange(
        id=change_tree_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=parent_identity.object_instance_graph_id,
        change=change,
        change_id=change_id,
        type=type,
        class_instance_changes=[],
        class_instance_relationship_changes=[],
    )
    return created
    # --- AWARE: LOGIC END create_via_object_instance_graph_identity
