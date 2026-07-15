from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_profile_actor_config import EnvironmentProfileActorConfig
from aware_environment_ontology.environment.environment_profile_config import EnvironmentProfileConfig
from aware_environment_ontology.environment.environment_provider import EnvironmentProvider
from aware_environment_ontology.process.process_config import ProcessConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_environment_profile_config_id,
)

# --- AWARE: USER_IMPORTS END


async def create_process_config(
    environment_profile_config: EnvironmentProfileConfig,
    type: str,
    key: str,
    title: str | None = None,
    description: str | None = None,
    shape: str | None = None,
    position: int | None = None,
    is_default: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> ProcessConfig:
    """
    Create a ProcessConfig under this EnvironmentProfileConfig.

    Contract:
    - Deterministic identity is EnvironmentProfileConfig-scoped using `key`.
    - Mutates only profile config membership.
    - Runtime Process instances are constructed under EnvironmentProfile.
    """

    # --- AWARE: LOGIC START create_process_config
    if environment_profile_config.id is None:
        raise RuntimeError("EnvironmentProfileConfig.create_process_config requires EnvironmentProfileConfig.id")

    created = await ProcessConfig.build_via_environment_profile_config(
        environment_profile_config_id=environment_profile_config.id,
        type=type,
        key=key,
        title=title,
        description=description,
        shape=shape,
        position=position,
        is_default=is_default,
        narrative=narrative,
        intent=intent,
    )
    for existing in environment_profile_config.process_configs:
        if existing.id == created.id:
            return existing
    environment_profile_config.process_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_process_config


async def register_provider(
    environment_profile_config: EnvironmentProfileConfig,
    provider_key: str,
    provider_kind: str = "provider",
    contract_ref: str | None = None,
    selection_policy: str = "contract_required",
    status: str = "active",
    title: str | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentProvider:
    """
    Register a provider-neutral slot for this EnvironmentProfileConfig.

    Contract:
    - Does not reference Experience or Service implementation classes.
    - Provider identity remains a contract key until an Experience binds to it.
    """

    # --- AWARE: LOGIC START register_provider
    if environment_profile_config.id is None:
        raise RuntimeError("EnvironmentProfileConfig.register_provider requires EnvironmentProfileConfig.id")

    created = await EnvironmentProvider.build_via_environment_profile_config(
        environment_profile_config_id=environment_profile_config.id,
        provider_key=provider_key,
        provider_kind=provider_kind,
        contract_ref=contract_ref,
        selection_policy=selection_policy,
        status=status,
        title=title,
        description=description,
        metadata_json=metadata_json,
    )
    for existing in environment_profile_config.providers:
        if existing.id == created.id:
            return existing
    environment_profile_config.providers.append(created)
    return created
    # --- AWARE: LOGIC END register_provider


async def add_actor_config(
    environment_profile_config: EnvironmentProfileConfig,
    actor_config_id: UUID,
    policy_key: str = "admit",
    requirement_kind: str = "environment_actor_config",
    access_scope: str = "profile",
    status: str = "active",
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentProfileActorConfig:
    """
    Declare one ActorConfig as eligible for EnvironmentProfileConfig admission.

    Contract:
    - Environment profile config owns eligibility policy for shared OS entrance.
    - Identity owns ActorConfig, RoleConfig, Role / ActorRole materialization.
    - Actors are not embedded here; admission services later translate this
      policy into Identity role assignment requests.
    """

    # --- AWARE: LOGIC START add_actor_config
    if environment_profile_config.id is None:
        raise RuntimeError("EnvironmentProfileConfig.add_actor_config requires EnvironmentProfileConfig.id")

    created = await EnvironmentProfileActorConfig.create_via_environment_profile_config(
        environment_profile_config_id=environment_profile_config.id,
        actor_config_id=actor_config_id,
        policy_key=policy_key,
        requirement_kind=requirement_kind,
        access_scope=access_scope,
        status=status,
        description=description,
        metadata_json=metadata_json,
    )
    for existing in environment_profile_config.actor_configs:
        if existing.id == created.id:
            return existing
    environment_profile_config.actor_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_actor_config


async def build_via_environment_config(
    environment_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
) -> EnvironmentProfileConfig:
    """
    Construct one reusable EnvironmentProfileConfig.

    Contract:
    - Stable identity is EnvironmentConfig path + `key`.
    - Parent EnvironmentConfig is propagated by containment.
    - This profile config is OS topology config, not an Experience profile
      and not a concrete Environment instance profile.
    """

    # --- AWARE: LOGIC START build_via_environment_config
    environment_profile_config_id = stable_environment_profile_config_id(
        environment_config_id=environment_config_id,
        key=key,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(
        EnvironmentProfileConfig,
        environment_profile_config_id,
    )
    if existing is not None:
        if existing.environment_config_id != environment_config_id or existing.key != key:
            raise RuntimeError(
                "EnvironmentProfileConfig.build_via_environment_config mismatch "
                f"for existing profile_config_id={environment_profile_config_id}"
            )
        return existing

    return EnvironmentProfileConfig(
        id=environment_profile_config_id,
        environment_config_id=environment_config_id,
        key=key,
        title=title,
        description=description,
        narrative=narrative,
    )
    # --- AWARE: LOGIC END build_via_environment_config
