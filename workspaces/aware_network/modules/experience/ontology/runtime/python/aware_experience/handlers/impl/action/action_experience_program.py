from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.action.action_experience_program import ActionExperienceProgram

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_action_experience_program_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_experience_ontology.action.action_experience import ActionExperience
from aware_experience_ontology.program.program_config import ProgramConfig

# --- AWARE: USER_IMPORTS END


async def build_via_action_experience(action_experience_id: UUID, program_config_id: UUID) -> ActionExperienceProgram:
    """
    Create a deterministic ActionExperienceProgram association edge.
    """

    # --- AWARE: LOGIC START build_via_action_experience
    session = current_handler_session()
    action_experience = session.imap_get(ActionExperience, action_experience_id)
    if action_experience is None:
        raise RuntimeError(
            "ActionExperienceProgram.build_via_action_experience requires existing ActionExperience in "
            + f"session: action_experience_id={action_experience_id}"
        )
    program_config = session.imap_get(ProgramConfig, program_config_id)

    assoc_id = stable_action_experience_program_id(
        action_experience_id=action_experience_id,
        program_config_id=program_config_id,
    )
    existing = session.imap_get(ActionExperienceProgram, assoc_id)
    if existing is not None:
        if existing.action_experience_id != action_experience_id or existing.program_config_id != program_config_id:
            raise RuntimeError(
                "ActionExperienceProgram.build_via_action_experience payload mismatch for existing association: "
                + f"action_experience_program_id={assoc_id}"
            )
        existing.program_config = program_config
        return existing

    return ActionExperienceProgram(
        id=assoc_id,
        action_experience_id=action_experience_id,
        program_config_id=program_config_id,
        program_config=program_config,
    )
    # --- AWARE: LOGIC END build_via_action_experience
