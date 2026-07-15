from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action_commit_event import (
    ExperienceInvocationActionCommitEvent,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_experience_invocation_action_commit_event_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_experience_invocation_action_commit(
    experience_invocation_action_commit_id: UUID,
    event_id: UUID,
    event_role: str = "emitted",
    description: str | None = None,
) -> ExperienceInvocationActionCommitEvent:
    """
    Link one Reactivity event to one invocation-action commit edge.

    Contract:
    - Parent `ExperienceInvocationActionCommit` scope is propagated by
      constructor lowering.
    - The event remains Reactivity-owned runtime evidence.
    """

    # --- AWARE: LOGIC START build_via_experience_invocation_action_commit
    normalized_event_role = (event_role or "").strip() or "emitted"
    normalized_description = (description or "").strip() or None
    commit_event_id = stable_experience_invocation_action_commit_event_id(
        experience_invocation_action_commit_id=experience_invocation_action_commit_id,
        event_id=event_id,
    )

    session = current_handler_session()
    existing = session.imap_get(ExperienceInvocationActionCommitEvent, commit_event_id)
    if existing is not None:
        if (
            existing.experience_invocation_action_commit_id != experience_invocation_action_commit_id
            or existing.event_id != event_id
            or existing.event_role != normalized_event_role
            or existing.description != normalized_description
        ):
            raise RuntimeError(
                "ExperienceInvocationActionCommitEvent payload mismatch for existing event: "
                + f"experience_invocation_action_commit_event_id={commit_event_id}"
            )
        return existing

    return ExperienceInvocationActionCommitEvent(
        id=commit_event_id,
        experience_invocation_action_commit_id=experience_invocation_action_commit_id,
        event_id=event_id,
        event_role=normalized_event_role,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_experience_invocation_action_commit
