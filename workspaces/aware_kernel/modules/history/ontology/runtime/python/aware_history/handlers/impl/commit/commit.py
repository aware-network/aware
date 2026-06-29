from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# History Ontology
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_parent import CommitParent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# History
from aware_history_ontology.stable_ids import stable_commit_id, stable_commit_parent_id
from aware_history_ontology.commit.commit_parent import CommitParent

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_parent(commit: Commit, parent_id: UUID) -> CommitParent:
    """
    Attach one parent edge under this Commit.

    Contract:
    - Owner `commit_id` is propagated from Commit via traversal lowering.
    - Only the explicit reference-side `parent_commit_id` is authored here.
    - Stable identity is keyed by `(commit_id, parent_id)`.
    """

    # --- AWARE: LOGIC START add_parent
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END add_parent


async def create_via_lane(
    lane_id: UUID, key: str, author_id: UUID, created_at: datetime, status: CommitStatus = CommitStatus.local
) -> Commit:
    """
    Creates a new Commit in the current Lane.
    """

    # --- AWARE: LOGIC START create_via_lane
    session = current_handler_session()
    commit_id = stable_commit_id(lane_id=lane_id, key=key)
    existing = session.imap_get(Commit, commit_id)
    if existing is not None:
        if existing.lane_id != lane_id:
            raise RuntimeError(
                "Commit.create existing Commit lane mismatch: "
                f"commit_id={commit_id} have={existing.lane_id} expected={lane_id}"
            )
        if existing.key != key:
            raise RuntimeError(
                "Commit.create existing Commit key mismatch: "
                f"commit_id={commit_id} have={existing.key!r} expected={key!r}"
            )
        return existing

    return Commit(
        id=commit_id,
        lane_id=lane_id,
        key=key,
        author_id=author_id,
        created_at=created_at,
        status=status,
    )
    # --- AWARE: LOGIC END create_via_lane
