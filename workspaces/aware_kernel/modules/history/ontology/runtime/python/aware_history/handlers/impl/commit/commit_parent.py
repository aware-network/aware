from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# History Ontology
from aware_history_ontology.commit.commit_parent import CommitParent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_history.stable_ids import stable_commit_parent_id

# --- AWARE: USER_IMPORTS END


async def create_via_commit(commit_id: UUID, parent_commit_id: UUID) -> CommitParent:
    """
    Creates a new CommitParent in the current Commit.

    Contract:
    - Owner `commit_id` is supplied by the `Commit -> commit_parents` traversal path.
    - Explicit constructor input is limited to the referenced `parent_commit_id`.
    """

    # --- AWARE: LOGIC START create_via_commit
    cp_id = stable_commit_parent_id(
        commit_id=commit_id,
        parent_commit_id=parent_commit_id,
    )
    return CommitParent(
        id=cp_id,
        parent_commit_id=parent_commit_id,
        commit_id=commit_id,
    )
    # --- AWARE: LOGIC END create_via_commit
