from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
from aware_meta_ontology.graph.instance.object_instance_graph_branch_relationship import (
    ObjectInstanceGraphBranchRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph_lane import ObjectInstanceGraphLane

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# History Ontology
from aware_history_ontology.branch.branch import Branch
from aware_history_ontology.lane.lane import Lane

# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_instance_graph_branch_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def attach_lane(
    object_instance_graph_branch: ObjectInstanceGraphBranch, lane_id: UUID
) -> ObjectInstanceGraphLane:
    """
    Attaches a history Lane to this ObjectInstanceGraphBranch (idempotent).

    Contract:
    - Mutates the meta association `object_instance_graph_lanes`, so it must be
      invoked as an instance function (runtime mutate-self-only).
    - Creates the ObjectInstanceGraphLane via its own constructor if missing.
    """

    # --- AWARE: LOGIC START attach_lane
    oigb_id = object_instance_graph_branch.id
    if oigb_id is None:
        raise RuntimeError("ObjectInstanceGraphBranch.attach_lane requires ObjectInstanceGraphBranch.id")

    # Ensure the history lane is present in the pre-state.
    session = current_handler_session()
    lane = session.imap_get(Lane, lane_id)
    if lane is None:
        raise RuntimeError(
            "ObjectInstanceGraphBranch.attach_lane requires Lane to exist in OIG(pre) state: " f"lane_id={lane_id}"
        )

    oigb_lane = await ObjectInstanceGraphLane.create_via_object_instance_graph_branch(
        object_instance_graph_branch_id=oigb_id,
        lane_id=lane_id,
    )
    if all(l.id != oigb_lane.id for l in object_instance_graph_branch.object_instance_graph_lanes):
        object_instance_graph_branch.object_instance_graph_lanes.append(oigb_lane)
    return oigb_lane
    # --- AWARE: LOGIC END attach_lane


async def attach_branch_relationship(
    object_instance_graph_branch: ObjectInstanceGraphBranch, target_object_instance_graph_branch_id: UUID
) -> ObjectInstanceGraphBranchRelationship:
    """
    Attaches a Branch→Branch relationship (idempotent).

    Notes:
    - This is a history-plane index primitive used for portal branch routing.
    - Mutates only `object_instance_graph_branch_relationships` (runtime mutate-self-only).
    """

    # --- AWARE: LOGIC START attach_branch_relationship
    source_oigb_id = object_instance_graph_branch.id
    if source_oigb_id is None:
        raise RuntimeError("ObjectInstanceGraphBranch.attach_branch_relationship requires ObjectInstanceGraphBranch.id")

    if not isinstance(target_object_instance_graph_branch_id, UUID):
        raise TypeError(
            "ObjectInstanceGraphBranch.attach_branch_relationship requires target_object_instance_graph_branch_id (UUID)"
        )

    # Idempotent: return existing relationship if present.
    for existing in object_instance_graph_branch.object_instance_graph_branch_relationships:
        if existing.target_object_instance_graph_branch_id == target_object_instance_graph_branch_id:
            return existing

    # Canonical invariant: creation must occur via a constructor handler (domain create allowed only in constructors).
    rel = await ObjectInstanceGraphBranchRelationship.create_via_object_instance_graph_branch(
        object_instance_graph_branch_id=source_oigb_id,
        target_object_instance_graph_branch_id=target_object_instance_graph_branch_id,
    )
    if all(r.id != rel.id for r in object_instance_graph_branch.object_instance_graph_branch_relationships):
        object_instance_graph_branch.object_instance_graph_branch_relationships.append(rel)
    return rel
    # --- AWARE: LOGIC END attach_branch_relationship


async def create_with_lane_and_branch_via_object_instance_graph_identity(
    object_instance_graph_identity_id: UUID,
    branch_id: UUID,
    lane_id: UUID,
    commit_id: UUID,
    lane_hash: str,
    is_main: bool = False,
    name: str | None = None,
) -> ObjectInstanceGraphBranch:
    """
    Create deterministic ObjectInstanceGraphBranch with one initial lane + branch head link.

    Contract:
    - Parent ObjectInstanceGraphIdentity ownership is propagated by traversal lowering.
    - Deterministic identity is constructor-keyed on `(branch_id)` plus parent path.
    """

    # --- AWARE: LOGIC START create_with_lane_and_branch_via_object_instance_graph_identity
    session = current_handler_session()
    object_instance_graph_branch_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=branch_id,
    )
    existing = session.imap_get(ObjectInstanceGraphBranch, object_instance_graph_branch_id)

    # Create or extend the History branch + lane set.
    #
    # NOTE: mutating an existing Branch must happen via an instance handler
    # (runtime invariant: "mutate self only").
    branch_existing = session.imap_get(Branch, branch_id)
    if branch_existing is None:
        branch = await Branch.create(
            branch_id=branch_id,
            lane_hash=lane_hash,
            is_main=is_main,
            name=name,
        )
    else:
        branch = await branch_existing.attach_lane(
            lane_hash=lane_hash,
        )

    if existing is not None:
        if existing.object_instance_graph_identity_id != object_instance_graph_identity_id:
            raise RuntimeError(
                "ObjectInstanceGraphBranch.create_via_object object_instance_graph_identity_id mismatch: "
                f"oigb_id={object_instance_graph_branch_id} have={existing.object_instance_graph_identity_id} "
                f"expected={object_instance_graph_identity_id}"
            )

        # Existing OIGB: attach the lane via an instance handler so the runtime
        # can enforce "mutate self only" on `object_instance_graph_lanes`.
        await existing.attach_lane(lane_id=lane_id)
        return existing

    # Create meta linkage history branch to object instance graph via oigb
    oigb = ObjectInstanceGraphBranch(
        id=object_instance_graph_branch_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch=branch,
        branch_id=branch_id,
    )

    # Create a lane that links oigb-branch to oig-lane.
    oigb_lane = await ObjectInstanceGraphLane.create_via_object_instance_graph_branch(
        object_instance_graph_branch_id=oigb.id,
        lane_id=lane_id,
    )
    if all(l.id != oigb_lane.id for l in oigb.object_instance_graph_lanes):
        oigb.object_instance_graph_lanes.append(oigb_lane)
    return oigb
    # --- AWARE: LOGIC END create_with_lane_and_branch_via_object_instance_graph_identity
