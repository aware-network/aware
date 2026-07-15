from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.session.experience_session_enums import ExperienceSessionState
from aware_experience_ontology.environment.environment_experience import EnvironmentExperience
from aware_experience_ontology.environment.environment_experience_profile import EnvironmentExperienceProfile
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.environment.environment_topology_seed import EnvironmentTopologySeed
from aware_experience_ontology.session.experience_session import ExperienceSession

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_experience_id

from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(fqn_prefix: str, title: str | None = None, description: str | None = None) -> EnvironmentExperience:
    """
    Create the canonical EnvironmentExperience namespace root.

    Notes:
    - Identity is derived from `fqn_prefix`.
    - This class is the Experience-owned root for profile composition.
    """

    # --- AWARE: LOGIC START build
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_fqn_prefix:
        raise RuntimeError("EnvironmentExperience.build requires non-empty fqn_prefix")

    session = current_handler_session()
    environment_experience_id = stable_environment_experience_id(fqn_prefix=normalized_fqn_prefix)
    existing = session.imap_get(EnvironmentExperience, environment_experience_id)
    if existing is not None:
        if (
            existing.fqn_prefix != normalized_fqn_prefix
            or existing.title != title
            or existing.description != description
        ):
            raise RuntimeError(
                "EnvironmentExperience.build payload mismatch for existing root: "
                f"environment_experience_id={environment_experience_id}"
            )
        return existing

    return EnvironmentExperience(
        id=environment_experience_id,
        fqn_prefix=normalized_fqn_prefix,
        title=title,
        description=description,
    )
    # --- AWARE: LOGIC END build


async def create_profile_config(
    environment_experience: EnvironmentExperience,
    environment_profile_config_id: UUID,
    key: str,
    environment_provider_grant_id: UUID | None = None,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
) -> EnvironmentExperienceProfileConfig:
    """
    Create one reusable profile config under this EnvironmentExperience namespace.

    Contract:
    - Profile config identity is scoped by parent->child invocation path
      plus the target Environment EnvironmentProfileConfig.
    - Experience profile config references Environment topology config; it
      does not construct EnvironmentProfile/ProcessConfig/ThreadConfig.
    """

    # --- AWARE: LOGIC START create_profile_config
    environment_experience_id = environment_experience.id
    if environment_experience_id is None:
        raise RuntimeError("EnvironmentExperience.create_profile_config requires EnvironmentExperience.id")

    created = await EnvironmentExperienceProfileConfig.build_via_environment_experience(
        environment_experience_id=environment_experience_id,
        environment_profile_config_id=environment_profile_config_id,
        key=key,
        environment_provider_grant_id=environment_provider_grant_id,
        title=title,
        description=description,
        narrative=narrative,
    )

    for existing in environment_experience.profile_configs:
        if existing.id == created.id:
            if (
                existing.environment_profile_config_id != environment_profile_config_id
                or existing.environment_provider_grant_id != environment_provider_grant_id
            ):
                raise RuntimeError(
                    "EnvironmentExperience.create_profile_config payload mismatch "
                    f"for existing profile config: environment_experience_profile_config_id={existing.id}"
                )
            return existing
    environment_experience.profile_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_profile_config


async def create_profile(
    environment_experience: EnvironmentExperience,
    profile_config_id: UUID,
    environment_profile_id: UUID,
    status: str = "active",
    title: str | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentExperienceProfile:
    """
    Create one applied Experience profile bridge under this EnvironmentExperience namespace.

    Contract:
    - Applied profile identity is scoped by parent->child invocation path
      plus `(profile_config_id, environment_profile_id)`.
    - Reusable Experience policy remains on EnvironmentExperienceProfileConfig.
    - Concrete Environment sessions remain on Environment EnvironmentProfile
      until the session rail is added.
    """

    # --- AWARE: LOGIC START create_profile
    environment_experience_id = environment_experience.id
    if environment_experience_id is None:
        raise RuntimeError("EnvironmentExperience.create_profile requires EnvironmentExperience.id")

    created = await EnvironmentExperienceProfile.build_via_environment_experience(
        environment_experience_id=environment_experience_id,
        profile_config_id=profile_config_id,
        environment_profile_id=environment_profile_id,
        status=status,
        title=title,
        description=description,
        metadata_json=metadata_json or {},
    )

    for existing in environment_experience.profiles:
        if existing.id == created.id:
            if (
                existing.profile_config_id != profile_config_id
                or existing.environment_profile_id != environment_profile_id
                or existing.status != status
            ):
                raise RuntimeError(
                    "EnvironmentExperience.create_profile payload mismatch "
                    f"for existing profile: environment_experience_profile_id={existing.id}"
                )
            return existing
    environment_experience.profiles.append(created)
    return created
    # --- AWARE: LOGIC END create_profile


async def create_topology_seed(
    environment_experience: EnvironmentExperience,
    environment_experience_profile_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
) -> EnvironmentTopologySeed:
    """
    Create one topology seed under this EnvironmentExperience namespace.

    Contract:
    - Seeds provide runtime process/thread/layout keys for genesis or named entrypoints.
    - Profile configs remain reusable policy and do not imply one runtime topology.
    """

    # --- AWARE: LOGIC START create_topology_seed
    environment_experience_id = environment_experience.id
    if environment_experience_id is None:
        raise RuntimeError("EnvironmentExperience.create_topology_seed requires EnvironmentExperience.id")

    created = await EnvironmentTopologySeed.build_via_environment_experience(
        environment_experience_id=environment_experience_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        key=key,
        title=title,
        description=description,
        narrative=narrative,
    )

    for existing in environment_experience.topology_seeds:
        if existing.id == created.id:
            if existing.environment_experience_profile_config_id != environment_experience_profile_config_id:
                raise RuntimeError(
                    "EnvironmentExperience.create_topology_seed profile config mismatch "
                    f"for existing seed: topology_seed_id={existing.id}"
                )
            return existing
    environment_experience.topology_seeds.append(created)
    return created
    # --- AWARE: LOGIC END create_topology_seed


async def start_session(
    environment_experience: EnvironmentExperience,
    identity_session_id: UUID,
    environment_session_id: UUID,
    state: ExperienceSessionState = ExperienceSessionState.active,
) -> ExperienceSession:
    """
    Start one commit-backed Experience session for a child Identity Session.

    Contract:
    - The child Identity Session owns participation, roles, and lifecycle.
    - EnvironmentSession supplies explicit shared-environment provenance.
    - ExperienceSession owns profile mount rows and local session state;
      visible/active view state remains scoped downstream.
    """

    # --- AWARE: LOGIC START start_session
    environment_experience_id = environment_experience.id
    if environment_experience_id is None:
        raise RuntimeError("EnvironmentExperience.start_session requires EnvironmentExperience.id")

    created = await ExperienceSession.build_via_environment_experience(
        environment_experience_id=environment_experience_id,
        identity_session_id=identity_session_id,
        environment_session_id=environment_session_id,
        state=state,
    )
    for existing in environment_experience.sessions:
        if existing.id != created.id:
            continue
        if existing.environment_session_id != environment_session_id:
            raise RuntimeError(
                "EnvironmentExperience.start_session payload mismatch for "
                f"existing ExperienceSession: experience_session_id={existing.id}"
            )
        return existing
    environment_experience.sessions.append(created)
    return created
    # --- AWARE: LOGIC END start_session
