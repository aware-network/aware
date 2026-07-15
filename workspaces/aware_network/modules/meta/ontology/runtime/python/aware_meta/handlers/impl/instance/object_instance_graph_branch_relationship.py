from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_branch_relationship import (
    ObjectInstanceGraphBranchRelationship,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_object_instance_graph_branch(
    object_instance_graph_branch_id: UUID, target_object_instance_graph_branch_id: UUID
) -> ObjectInstanceGraphBranchRelationship:
    """
    Creates a Branch→Branch relationship join (idempotent).

    Contract:
    - Source branch identity is parent-propagated when invoked via
      `ObjectInstanceGraphBranch.attach_branch_relationship`.
    - Deterministic id derived from parent source scope + `(target_oigb_id)`.
    - Used by runtime to make portal branch routing commit-backed (no consumer guessing).
    """

    # --- AWARE: LOGIC START create_via_object_instance_graph_branch
    if not isinstance(object_instance_graph_branch_id, UUID):
        raise TypeError(
            "ObjectInstanceGraphBranchRelationship.create_via_object requires object_instance_graph_branch_id (UUID)"
        )
    if not isinstance(target_object_instance_graph_branch_id, UUID):
        raise TypeError(
            "ObjectInstanceGraphBranchRelationship.create_via_object requires target_object_instance_graph_branch_id (UUID)"
        )

    from aware_meta_ontology.stable_ids import stable_object_instance_graph_branch_relationship_id

    rel_id = stable_object_instance_graph_branch_relationship_id(
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        target_object_instance_graph_branch_id=target_object_instance_graph_branch_id,
    )

    session = current_handler_session()
    existing = session.imap_get(ObjectInstanceGraphBranchRelationship, rel_id)
    if existing is not None:
        return existing

    target_oigb = session.imap_get(ObjectInstanceGraphBranch, target_object_instance_graph_branch_id)
    if target_oigb is None:
        raise RuntimeError(
            "ObjectInstanceGraphBranchRelationship.create_via_object requires target "
            "ObjectInstanceGraphBranch to exist in OIG(pre) state: "
            f"target_object_instance_graph_branch_id={target_object_instance_graph_branch_id}"
        )

    return ObjectInstanceGraphBranchRelationship(
        id=rel_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        target_object_instance_graph_branch=target_oigb,
        target_object_instance_graph_branch_id=target_object_instance_graph_branch_id,
    )
    # --- AWARE: LOGIC END create_via_object_instance_graph_branch
