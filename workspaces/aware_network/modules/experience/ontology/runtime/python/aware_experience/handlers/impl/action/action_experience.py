from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.action.action_experience import ActionExperience
from aware_experience_ontology.action.action_experience_invocation import ActionExperienceInvocation
from aware_experience_ontology.action.action_experience_program import ActionExperienceProgram

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_action_experience_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(action_config_id: UUID) -> ActionExperience:
    """
    Create a deterministic ActionExperience association edge with associated program configs.

    Contract:
    - ActionExperience identity is scoped by `action_config_id`.
    - Thread-scoped program availability belongs under
      EnvironmentExperienceThreadConfig, not a hidden action parent context.
    """

    # --- AWARE: LOGIC START build
    session = current_handler_session()
    action_config = None

    action_experience_id = stable_action_experience_id(
        action_config_id=action_config_id,
    )
    existing = session.imap_get(ActionExperience, action_experience_id)
    if existing is not None:
        if existing.action_config_id != action_config_id:
            raise RuntimeError(
                "ActionExperience.build payload mismatch for existing action experience: "
                + f"action_experience_id={action_experience_id}"
            )
        if action_config is not None:
            existing.action_config = action_config
        return existing

    return ActionExperience(
        id=action_experience_id,
        action_config_id=action_config_id,
        action_config=action_config,
    )
    # --- AWARE: LOGIC END build


async def add_program_config(action_experience: ActionExperience, program_config_id: UUID) -> ActionExperienceProgram:
    """
    Add a program config to the action experience.
    """

    # --- AWARE: LOGIC START add_program_config
    action_experience_id = action_experience.id
    created = await ActionExperienceProgram.build_via_action_experience(
        action_experience_id=action_experience_id,
        program_config_id=program_config_id,
    )
    if created.action_experience_id != action_experience_id:
        raise RuntimeError(
            "ActionExperience.add_program_config context mismatch for created association: "
            + f"action_experience_program_id={created.id}"
        )

    for existing in action_experience.action_experience_programs:
        if existing.id == created.id:
            return existing
    action_experience.action_experience_programs.append(created)
    return created
    # --- AWARE: LOGIC END add_program_config


async def add_invocation_action_config(
    action_experience: ActionExperience, experience_invocation_action_config_id: UUID
) -> ActionExperienceInvocation:
    """
    Bind an Experience invocation action config to this action experience.

    Contract:
    - Reactivity stays API-agnostic; this edge lives in Experience.
    - Dispatch-time selection among many invocation configs is a later
      concern.
    - The bound ExperienceInvocationActionConfig resolves the typed
      request/response/stream contract through API/SDK target metadata.
    """

    # --- AWARE: LOGIC START add_invocation_action_config
    action_experience_id = action_experience.id
    created = await ActionExperienceInvocation.build_via_action_experience(
        action_experience_id=action_experience_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
    )
    if created.action_experience_id != action_experience_id:
        raise RuntimeError(
            "ActionExperience.add_invocation_action_config context mismatch for created association: "
            + f"action_experience_invocation_id={created.id}"
        )

    for existing in action_experience.action_experience_invocations:
        if existing.id == created.id:
            return existing
    action_experience.action_experience_invocations.append(created)
    return created
    # --- AWARE: LOGIC END add_invocation_action_config
