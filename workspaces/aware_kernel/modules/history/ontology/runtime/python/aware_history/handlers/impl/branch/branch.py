from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# History Ontology
from aware_history_ontology.branch.branch import Branch
from aware_history_ontology.lane.lane import Lane
from aware_history_ontology.version.version import Version

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_history.stable_ids import stable_lane_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create(
    branch_id: UUID, lane_hash: str, key: str = "default", is_main: bool = False, name: str | None = None
) -> Branch:
    """
    Creates a new Branch as a bundle of lanes.

    Contract:
    - Stable identity is constructor-keyed by `key`.
    - Initial Lane is constructed via Branch->Lane propagation.
    """

    # --- AWARE: LOGIC START create
    session = current_handler_session()
    existing = session.imap_get(Branch, branch_id)
    if existing is not None:
        # Constructors must not mutate existing instances (runtime invariant: "mutate self only").
        # Use Branch.attach_lane(...) when you need to extend the lanes relationship.
        return existing

    branch = Branch(id=branch_id, key=key, is_main=is_main, name=name)
    lane_id = stable_lane_id(branch_id=branch_id, lane_hash=lane_hash)
    lane = session.imap_get(Lane, lane_id)
    if lane is None:
        lane = await Lane.create_via_branch(
            branch_id=branch_id,
            lane_hash=lane_hash,
        )
    else:
        if lane.branch_id != branch_id:
            raise RuntimeError(
                "Branch.create lane/branch mismatch for existing Lane: "
                f"lane_id={lane_id} existing_branch_id={lane.branch_id} expected_branch_id={branch_id}"
            )
        if lane.lane_hash != lane_hash:
            raise RuntimeError(
                "Branch.create lane_hash mismatch for existing Lane: "
                f"lane_id={lane_id} have={lane.lane_hash} expected={lane_hash}"
            )
    branch.lanes.append(lane)
    return branch
    # --- AWARE: LOGIC END create


async def attach_lane(branch: Branch, lane_hash: str) -> Lane:
    """
    Attaches a Lane to this Branch (idempotent).

    Contract:
    - Must be invoked as an instance function so the runtime can enforce
      "mutate self only" for the Branch→Lane relationship.
    - The Lane is created via Lane.create if missing.
    """

    # --- AWARE: LOGIC START attach_lane
    branch_id = branch.id
    if branch_id is None:
        raise RuntimeError("Branch.attach_lane requires Branch.id")

    session = current_handler_session()
    lane_id = stable_lane_id(branch_id=branch_id, lane_hash=lane_hash)
    existing_lane = session.imap_get(Lane, lane_id)
    if existing_lane is None:
        existing_lane = await Lane.create_via_branch(
            branch_id=branch_id,
            lane_hash=lane_hash,
        )
    else:
        if existing_lane.branch_id != branch_id:
            raise RuntimeError(
                "Branch.attach_lane lane/branch mismatch for existing Lane: "
                f"lane_id={lane_id} existing_branch_id={existing_lane.branch_id} expected_branch_id={branch_id}"
            )
        if existing_lane.lane_hash != lane_hash:
            raise RuntimeError(
                "Branch.attach_lane lane_hash mismatch for existing Lane: "
                f"branch_id={branch_id} lane_id={lane_id} "
                f"have={existing_lane.lane_hash} expected={lane_hash}"
            )

    if all(l.id != lane_id for l in branch.lanes):
        branch.lanes.append(existing_lane)
    return existing_lane
    # --- AWARE: LOGIC END attach_lane


async def create_version(branch: Branch, version_number: int, head_commit_id: UUID | None = None) -> Version:
    """
    Create one Version under this Branch.

    Contract:
    - Parent `branch_id` is propagated by traversal lowering.
    - Stable identity is keyed by `(branch_id, version_number)`.
    """

    # --- AWARE: LOGIC START create_version
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_version
