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
# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience_profile_config(
    environment_experience_profile_config_id: UUID, actor_config_id: UUID
) -> EnvironmentExperienceActorConfig:
    """
    Create a deterministic EnvironmentExperienceActorConfig association edge.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_profile_config
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_environment_experience_profile_config
