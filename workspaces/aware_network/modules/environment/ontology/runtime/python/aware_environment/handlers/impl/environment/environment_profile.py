from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_profile import EnvironmentProfile
from aware_environment_ontology.process.process import Process

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.process.process import Process
from aware_environment_ontology.stable_ids import (
    stable_environment_profile_id,
)

# --- AWARE: USER_IMPORTS END


async def create_process(
    environment_profile: EnvironmentProfile,
    process_config_id: UUID,
    key: str,
    title: str,
    description: str | None = None,
) -> Process:
    """
    Instantiate one runtime Process under this applied EnvironmentProfile.

    Contract:
    - EnvironmentProfile owns runtime Process membership.
    - ProcessConfig remains a reusable config portal/key.
    - Runtime identity is `(environment_profile_id via path, process_config_id, key)`.
    """

    # --- AWARE: LOGIC START create_process
    if environment_profile.id is None:
        raise RuntimeError("EnvironmentProfile.create_process requires EnvironmentProfile.id")

    created = await Process.build_via_environment_profile(
        environment_profile_id=environment_profile.id,
        process_config_id=process_config_id,
        key=key,
        title=title,
        description=description,
    )
    for existing in environment_profile.processes:
        if existing.id == created.id:
            return existing
    environment_profile.processes.append(created)
    return created
    # --- AWARE: LOGIC END create_process


async def build_via_environment(
    environment_id: UUID,
    profile_config_id: UUID,
    title: str | None = None,
    description: str | None = None,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentProfile:
    """
    Construct one applied EnvironmentProfile under an Environment.

    Contract:
    - Identity is derived from parent Environment path + ProfileConfig.
    - This owns concrete runtime Process membership.
    - It does not own process/thread/session reusable config topology.
    - It links concrete Environment runtime state back to reusable config.
    """

    # --- AWARE: LOGIC START build_via_environment
    environment_profile_id = stable_environment_profile_id(
        environment_id=environment_id,
        profile_config_id=profile_config_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(EnvironmentProfile, environment_profile_id)
    if existing is not None:
        if existing.environment_id != environment_id or existing.profile_config_id != profile_config_id:
            raise RuntimeError(
                "EnvironmentProfile.build_via_environment mismatch "
                f"for existing profile: environment_profile_id={environment_profile_id}"
            )
        return existing

    return EnvironmentProfile(
        id=environment_profile_id,
        environment_id=environment_id,
        profile_config_id=profile_config_id,
        title=title,
        description=description,
        status=status,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_environment
