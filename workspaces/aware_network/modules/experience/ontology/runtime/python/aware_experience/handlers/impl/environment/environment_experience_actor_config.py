from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_actor import EnvironmentExperienceActorConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_experience_actor_config_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience_profile_config(
    environment_experience_profile_config_id: UUID, actor_config_id: UUID
) -> EnvironmentExperienceActorConfig:
    """
    Create a deterministic EnvironmentExperienceActorConfig association edge.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_profile_config
    association_id = stable_environment_experience_actor_config_id(
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        actor_config_id=actor_config_id,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceActorConfig, association_id)
    if existing is not None:
        if (
            existing.environment_experience_profile_config_id
            != environment_experience_profile_config_id
            or existing.actor_config_id != actor_config_id
        ):
            raise RuntimeError(
                "EnvironmentExperienceActorConfig.build_via_environment_experience_profile_config payload mismatch "
                + f"for existing association: environment_experience_actor_config_id={association_id}"
            )
        return existing

    return EnvironmentExperienceActorConfig(
        id=association_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        actor_config_id=actor_config_id,
    )
    # --- AWARE: LOGIC END build_via_environment_experience_profile_config
