from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.role.role_enums import AccessLevelType
from aware_identity_ontology.role.role_config import RoleConfig
from aware_identity_ontology.role.role_config_class_config import RoleConfigClassConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import (
    stable_role_config_class_config_id,
    stable_role_config_id,
)

# --- AWARE: USER_IMPORTS END


async def create(name: str, description: str | None = None) -> RoleConfig:
    """
    Create a RoleConfig (policy root) inside the `role_config` projection.

    Contract (v0):
    - Policy creation is commit-backed (no transport-only RoleConfigs).
    - `name` is the canonical key (runtime derives a stable id from it).
    - Idempotent by name: creating the same RoleConfig twice returns the existing instance.
    """

    # --- AWARE: LOGIC START create
    canonical_name = name.casefold().strip()
    if not canonical_name:
        raise ValueError("RoleConfig.create requires a non-empty name")

    role_config_id = stable_role_config_id(name=canonical_name)
    return RoleConfig(
        id=role_config_id,
        name=canonical_name,
        description=description,
    )
    # --- AWARE: LOGIC END create


async def upsert_class_config_policy(
    role_config: RoleConfig, class_config_id: UUID, access_level: AccessLevelType
) -> RoleConfigClassConfig:
    """
    Upsert a class-level policy edge for a given meta ClassConfig.

    Notes:
    - `class_config_id` refers to `aware_meta.class.ClassConfig` via the `role_config` →
    `object_config_graph` portal.
    - Function-level policy is modeled on `RoleConfigClassConfigFunctionConfig`.
    """

    # --- AWARE: LOGIC START upsert_class_config_policy
    if role_config.id is None:
        raise ValueError("RoleConfig.upsert_class_config_policy requires a bound role_config.id")

    if not isinstance(class_config_id, UUID):
        raise ValueError("RoleConfig.upsert_class_config_policy requires a valid class_config_id UUID")

    rccc_id = stable_role_config_class_config_id(
        role_config_id=role_config.id,
        class_config_id=class_config_id,
    )

    for existing_policy in role_config.role_config_class_configs:
        if existing_policy.id == rccc_id:
            return existing_policy

    # Domain object creation must occur via constructor propagation (see change_collector invariants).
    policy = await RoleConfigClassConfig.create_via_role_config(
        role_config_id=role_config.id,
        class_config_id=class_config_id,
        access_level=access_level,
    )
    role_config.role_config_class_configs.append(policy)
    return policy
    # --- AWARE: LOGIC END upsert_class_config_policy
