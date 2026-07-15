from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action_commit import ExperienceInvocationActionCommit
from aware_experience_ontology.invocation.experience_invocation_action_commit_event import (
    ExperienceInvocationActionCommitEvent,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_experience_invocation_action_commit_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_event(
    experience_invocation_action_commit: ExperienceInvocationActionCommit,
    event_id: UUID,
    event_role: str = "emitted",
    description: str | None = None,
) -> ExperienceInvocationActionCommitEvent:
    """
    Link one Reactivity event to this invocation action commit.

    Contract:
    - Reactivity owns `Event`.
    - This edge closes the Experience provenance loop: action -> commit -> event.
    """

    # --- AWARE: LOGIC START add_event
    event = await ExperienceInvocationActionCommitEvent.build_via_experience_invocation_action_commit(
        experience_invocation_action_commit_id=experience_invocation_action_commit.id,
        event_id=event_id,
        event_role=event_role,
        description=description,
    )
    for existing in experience_invocation_action_commit.events:
        if existing.id == event.id:
            return existing
    experience_invocation_action_commit.events.append(event)
    return event
    # --- AWARE: LOGIC END add_event


async def build_via_experience_invocation_action(
    experience_invocation_action_id: UUID,
    object_instance_graph_commit_id: UUID,
    commit_role: str = "mutation",
    description: str | None = None,
) -> ExperienceInvocationActionCommit:
    """
    Link one Meta-owned graph commit to this invocation action.

    Contract:
    - Parent `ExperienceInvocationAction` scope is propagated by constructor lowering.
    - `commit_role` names whether the commit was produced, consumed, or
      otherwise observed by this action.
    """

    # --- AWARE: LOGIC START build_via_experience_invocation_action
    normalized_commit_role = (commit_role or "").strip() or "mutation"
    normalized_description = (description or "").strip() or None
    commit_id = stable_experience_invocation_action_commit_id(
        experience_invocation_action_id=experience_invocation_action_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )

    session = current_handler_session()
    existing = session.imap_get(ExperienceInvocationActionCommit, commit_id)
    if existing is not None:
        if (
            existing.experience_invocation_action_id != experience_invocation_action_id
            or existing.object_instance_graph_commit_id != object_instance_graph_commit_id
            or existing.commit_role != normalized_commit_role
            or existing.description != normalized_description
        ):
            raise RuntimeError(
                "ExperienceInvocationActionCommit payload mismatch for existing commit: "
                + f"experience_invocation_action_commit_id={commit_id}"
            )
        return existing

    return ExperienceInvocationActionCommit(
        id=commit_id,
        experience_invocation_action_id=experience_invocation_action_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        commit_role=normalized_commit_role,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_experience_invocation_action
