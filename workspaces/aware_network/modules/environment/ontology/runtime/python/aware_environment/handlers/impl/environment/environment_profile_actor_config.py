from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_profile_actor_config import EnvironmentProfileActorConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_environment_profile_config(
    environment_profile_config_id: UUID,
    actor_config_id: UUID,
    policy_key: str = "admit",
    requirement_kind: str = "environment_actor_config",
    access_scope: str = "profile",
    status: str = "active",
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentProfileActorConfig:
    """
    Create one EnvironmentProfileConfig ActorConfig eligibility edge.

    Contract:
    - Stable identity is `(environment_profile_config_id, actor_config_id, policy_key)`.
    - The edge is policy eligibility only; concrete admission is Identity-owned.
    - `access_scope` is explicit so v0 profile admission does not imply hidden
      ProcessConfig or ThreadConfig rights.
    """

    # --- AWARE: LOGIC START create_via_environment_profile_config
    return EnvironmentProfileActorConfig(
        environment_profile_config_id=environment_profile_config_id,
        actor_config_id=actor_config_id,
        policy_key=policy_key,
        requirement_kind=requirement_kind,
        access_scope=access_scope,
        status=status,
        description=description,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END create_via_environment_profile_config
