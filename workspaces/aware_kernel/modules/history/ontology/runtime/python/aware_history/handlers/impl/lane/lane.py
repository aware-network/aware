from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# History Ontology
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.lane.lane import Lane

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START

# History
from aware_history_ontology.stable_ids import stable_commit_id, stable_lane_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)


def _resolve_commit_in_session(*, session, commit_id: UUID) -> Commit | None:
    """Resolve Commit from current handler session identity map."""
    if commit_id is None:
        return None
    return session.imap_get(Commit, commit_id)


# --- AWARE: USER_IMPORTS END


async def create_commit(
    lane: Lane, key: str, author_id: UUID, created_at: datetime, status: CommitStatus = CommitStatus.local
) -> Commit:
    """
    Create one Commit under this Lane.

    Contract:
    - Parent `lane_id` is propagated by traversal lowering.
    - Stable identity is keyed by `(lane_id, key)`.
    """

    # --- AWARE: LOGIC START create_commit
    session = current_handler_session()
    lane_id = lane.id
    if lane_id is None:
        raise RuntimeError("Lane.create_commit requires Lane.id")

    commit_id = stable_commit_id(lane_id=lane_id, key=key)
    existing = session.imap_get(Commit, commit_id)
    if existing is not None:
        if existing.lane_id != lane_id:
            raise RuntimeError(
                "Lane.create_commit existing Commit lane mismatch: "
                f"commit_id={commit_id} have={existing.lane_id} expected={lane_id}"
            )
        if existing.key != key:
            raise RuntimeError(
                "Lane.create_commit existing Commit key mismatch: "
                f"commit_id={commit_id} have={existing.key!r} expected={key!r}"
            )
        return existing

    commit = Commit(
        id=commit_id,
        lane_id=lane_id,
        key=key,
        author_id=author_id,
        created_at=created_at,
        status=status,
    )
    lane.commits.append(commit)
    return commit
    # --- AWARE: LOGIC END create_commit


async def advance_head(lane: Lane, commit_id: UUID) -> Lane:
    """
    Advance this Lane's head_commit pointer (SSOT: commit store).

    Canonical v0:
    - Used by the OIGI history plane projector to mirror domain lane heads.
    - Mutates only self (`Lane.head_commit_id` + `Lane.head_commit`).
    """

    # --- AWARE: LOGIC START advance_head
    session = current_handler_session()

    if lane.id is None:
        raise RuntimeError("Lane.advance_head requires Lane.id")

    # Idempotent: no-op if already at requested head.
    if lane.head_commit_id == commit_id and lane.head_commit is not None:
        return lane

    # Set FK first (used by OIG diff even if commit relationship is not materialized).
    if "head_commit_id" in Lane.model_fields:
        lane.head_commit_id = commit_id

    # Canonical: the Commit instance must already exist in the lane pre-state
    # (materialized via the OIGI history-plane projector). Avoid synthesizing
    # Commit objects here.

    commit = _resolve_commit_in_session(session=session, commit_id=commit_id)
    lane.head_commit = commit
    return lane
    # --- AWARE: LOGIC END advance_head


async def create_via_branch(branch_id: UUID, lane_hash: str) -> Lane:
    """
    Creates a new Lane in the current Branch.
    """

    # --- AWARE: LOGIC START create_via_branch
    session = current_handler_session()
    lane_id = stable_lane_id(branch_id=branch_id, lane_hash=lane_hash)
    existing = session.imap_get(Lane, lane_id)
    if existing is not None:
        return existing

    lane = Lane(
        id=lane_id,
        branch_id=branch_id,
        lane_hash=lane_hash,
    )
    return lane
    # --- AWARE: LOGIC END create_via_branch
