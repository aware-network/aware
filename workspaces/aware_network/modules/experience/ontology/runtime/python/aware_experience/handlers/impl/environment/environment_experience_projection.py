from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_projection import EnvironmentExperienceProjection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_experience_projection_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience_profile_config(
    environment_experience_profile_config_id: UUID, projection_experience_id: UUID
) -> EnvironmentExperienceProjection:
    """
    Create a deterministic EnvironmentExperienceProjection association edge.

    Notes:
    - Identity is derived from `(environment_experience_profile_config_id, projection_experience_id)`.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_profile_config
    assoc_id = stable_environment_experience_projection_id(
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        projection_experience_id=projection_experience_id,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceProjection, assoc_id)
    if existing is not None:
        if existing.environment_experience_profile_config_id != environment_experience_profile_config_id:
            raise RuntimeError(
                "EnvironmentExperienceProjection.build_via_environment_experience_profile_config profile mismatch for existing "
                f"association: association_id={assoc_id}"
            )
        if existing.projection_experience_id != projection_experience_id:
            raise RuntimeError(
                "EnvironmentExperienceProjection.build_via_environment_experience_profile_config projection mismatch for existing "
                f"association: association_id={assoc_id}"
            )
        return existing

    return EnvironmentExperienceProjection(
        id=assoc_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        projection_experience_id=projection_experience_id,
    )
    # --- AWARE: LOGIC END build_via_environment_experience_profile_config
