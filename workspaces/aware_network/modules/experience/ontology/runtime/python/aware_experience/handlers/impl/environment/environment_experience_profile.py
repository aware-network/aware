from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_profile import EnvironmentExperienceProfile

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_experience_profile_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience(
    environment_experience_id: UUID,
    profile_config_id: UUID,
    environment_profile_id: UUID,
    status: str = "active",
    title: str | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentExperienceProfile:
    """
    Construct one applied EnvironmentExperienceProfile under EnvironmentExperience.

    Contract:
    - Identity is derived from parent EnvironmentExperience path plus
      `(profile_config_id, environment_profile_id)`.
    - `profile_config_id` owns reusable Experience policy.
    - `environment_profile_id` owns concrete Environment session topology.
    """

    # --- AWARE: LOGIC START build_via_environment_experience
    normalized_status = (status or "").strip()
    if not normalized_status:
        raise RuntimeError("EnvironmentExperienceProfile.build_via_environment requires non-empty status")

    profile_id = stable_environment_experience_profile_id(
        environment_experience_id=environment_experience_id,
        profile_config_id=profile_config_id,
        environment_profile_id=environment_profile_id,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceProfile, profile_id)
    normalized_metadata = metadata_json or {}
    if existing is not None:
        if (
            existing.environment_experience_id != environment_experience_id
            or existing.profile_config_id != profile_config_id
            or existing.environment_profile_id != environment_profile_id
            or existing.status != normalized_status
            or existing.title != title
            or existing.description != description
            or existing.metadata_json != normalized_metadata
        ):
            raise RuntimeError(
                "EnvironmentExperienceProfile.build_via_environment payload mismatch "
                f"for existing profile: profile_id={profile_id}"
            )
        return existing

    return EnvironmentExperienceProfile(
        id=profile_id,
        environment_experience_id=environment_experience_id,
        profile_config_id=profile_config_id,
        environment_profile_id=environment_profile_id,
        status=normalized_status,
        title=title,
        description=description,
        metadata_json=normalized_metadata,
    )
    # --- AWARE: LOGIC END build_via_environment_experience
