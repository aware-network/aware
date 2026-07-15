from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.session.experience_session_profile import ExperienceSessionProfile

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience_ontology.stable_ids import (
    stable_experience_session_profile_id,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_experience_session(
    experience_session_id: UUID,
    profile_id: UUID,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> ExperienceSessionProfile:
    """
    Mount one applied Experience profile under ExperienceSession.

    Stable identity is ExperienceSession plus applied profile.
    """

    # --- AWARE: LOGIC START build_via_experience_session
    if not isinstance(experience_session_id, UUID):
        raise TypeError("ExperienceSessionProfile.build requires experience_session_id (UUID)")
    if not isinstance(profile_id, UUID):
        raise TypeError("ExperienceSessionProfile.build requires profile_id (UUID)")
    normalized_status = status.strip().lower() if isinstance(status, str) else ""
    if not normalized_status:
        raise ValueError("ExperienceSessionProfile.build requires non-empty status")

    mount_id = stable_experience_session_profile_id(
        experience_session_id=experience_session_id,
        profile_id=profile_id,
    )
    try:
        session = current_handler_session()
    except RuntimeError:
        session = None
    if session is not None:
        existing = session.imap_get(ExperienceSessionProfile, mount_id)
        if existing is not None:
            return existing

    return ExperienceSessionProfile(
        id=mount_id,
        experience_session_id=experience_session_id,
        profile=None,
        profile_id=profile_id,
        status=normalized_status,
        metadata_json=metadata_json or JsonObject(),
    )
    # --- AWARE: LOGIC END build_via_experience_session
