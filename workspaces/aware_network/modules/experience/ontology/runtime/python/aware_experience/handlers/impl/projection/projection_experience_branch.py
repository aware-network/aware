from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_branch import ProjectionExperienceBranch

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_projection_experience_branch_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_projection_experience(projection_experience_id: UUID, name: str) -> ProjectionExperienceBranch:
    """
    Construct a deterministic ProjectionExperienceBranch under a ProjectionExperience.

    Contract:
    - `ProjectionExperienceBranch.id` is deterministic for `(projection_experience_id, name)`.
    - Constructor is idempotent for repeated calls with the same pair.
    """

    # --- AWARE: LOGIC START create_via_projection_experience
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProjectionExperienceBranch.create_via_projection_experience requires non-empty name")

    session = current_handler_session()
    branch_id = stable_projection_experience_branch_id(
        projection_experience_id=projection_experience_id,
        name=normalized_name,
    )
    existing = session.imap_get(ProjectionExperienceBranch, branch_id)
    if existing is not None:
        if existing.projection_experience_id != projection_experience_id or existing.name != normalized_name:
            raise RuntimeError(
                "ProjectionExperienceBranch.create_via_projection_experience payload mismatch for existing branch: "
                + f"projection_experience_branch_id={branch_id}"
            )
        return existing

    return ProjectionExperienceBranch(
        id=branch_id,
        projection_experience_id=projection_experience_id,
        name=normalized_name,
    )
    # --- AWARE: LOGIC END create_via_projection_experience
