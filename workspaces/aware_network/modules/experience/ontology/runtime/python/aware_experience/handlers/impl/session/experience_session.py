from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.session.experience_session_enums import ExperienceSessionState
from aware_experience_ontology.session.experience_session import ExperienceSession
from aware_experience_ontology.session.experience_session_profile import ExperienceSessionProfile

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience_ontology.stable_ids import stable_experience_session_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def mount_profile(
    experience_session: ExperienceSession,
    profile_id: UUID,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> ExperienceSessionProfile:
    """
    Mount one applied Experience profile into this session.

    Contract:
    - Stable identity is ExperienceSession plus applied profile.
    - Many applied profiles may be mounted in one ExperienceSession.
    - Mounting does not select a global active profile or projection.
    """

    # --- AWARE: LOGIC START mount_profile
    experience_session_id = experience_session.id
    if experience_session_id is None:
        raise RuntimeError("ExperienceSession.mount_profile requires ExperienceSession.id")
    created = await ExperienceSessionProfile.build_via_experience_session(
        experience_session_id=experience_session_id,
        profile_id=profile_id,
        status=status,
        metadata_json=metadata_json or JsonObject(),
    )
    for existing in experience_session.profiles:
        if existing.id != created.id:
            continue
        if existing.profile_id != profile_id or existing.status != status:
            raise RuntimeError(
                "ExperienceSession.mount_profile payload mismatch for existing "
                f"mount: experience_session_profile_id={existing.id}"
            )
        return existing
    experience_session.profiles.append(created)
    return created
    # --- AWARE: LOGIC END mount_profile


async def build_via_environment_experience(
    environment_experience_id: UUID,
    identity_session_id: UUID,
    environment_session_id: UUID,
    state: ExperienceSessionState = ExperienceSessionState.active,
) -> ExperienceSession:
    """
    Construct one Experience session under EnvironmentExperience.

    Stable identity is EnvironmentExperience plus child Identity Session.
    Replaying the same child Identity Session resolves the same committed
    Experience session instead of creating a second authority.
    """

    # --- AWARE: LOGIC START build_via_environment_experience
    for field_name, value in (
        ("environment_experience_id", environment_experience_id),
        ("identity_session_id", identity_session_id),
        ("environment_session_id", environment_session_id),
    ):
        if not isinstance(value, UUID):
            raise TypeError(f"ExperienceSession.build requires {field_name} (UUID)")
    experience_session_id = stable_experience_session_id(
        environment_experience_id=environment_experience_id,
        identity_session_id=identity_session_id,
    )
    try:
        session = current_handler_session()
    except RuntimeError:
        session = None
    if session is not None:
        existing = session.imap_get(ExperienceSession, experience_session_id)
        if existing is not None:
            return existing

    return ExperienceSession(
        id=experience_session_id,
        environment_experience_id=environment_experience_id,
        identity_session=None,
        identity_session_id=identity_session_id,
        environment_session=None,
        environment_session_id=environment_session_id,
        profiles=[],
        state=state,
    )
    # --- AWARE: LOGIC END build_via_environment_experience
