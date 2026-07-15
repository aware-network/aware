from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_program import EnvironmentExperienceProgram

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_experience_program_id

from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience_thread_config(
    environment_experience_thread_config_id: UUID, program_config_id: UUID
) -> EnvironmentExperienceProgram:
    """
    Construct the canonical EnvironmentExperienceProgram for an environment territory.

    Contract:
    - Identity is derived from `(environment_experience_thread_config_id, program_config_id)`.
    - Constructor does not mutate EnvironmentExperienceThreadConfig directly.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_thread_config
    program_id = stable_environment_experience_program_id(
        environment_experience_thread_config_id=environment_experience_thread_config_id,
        program_config_id=program_config_id,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceProgram, program_id)
    if existing is not None:
        if (
            existing.environment_experience_thread_config_id != environment_experience_thread_config_id
            or existing.program_config_id != program_config_id
        ):
            raise RuntimeError(
                "EnvironmentExperienceProgram.build payload mismatch for existing program: "
                f"environment_experience_program_id={program_id}"
            )
        return existing
    return EnvironmentExperienceProgram(
        id=program_id,
        environment_experience_thread_config_id=environment_experience_thread_config_id,
        program_config_id=program_config_id,
    )
    # --- AWARE: LOGIC END build_via_environment_experience_thread_config
