from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.role.role_enums import AccessLevelType
from aware_identity_ontology.role.role_config_class_config import RoleConfigClassConfig
from aware_identity_ontology.role.role_config_class_config_function_config import RoleConfigClassConfigFunctionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import (
    stable_role_config_class_config_function_config_id,
    stable_role_config_class_config_id,
)

# --- AWARE: USER_IMPORTS END


async def upsert_function_config_policy(
    role_config_class_config: RoleConfigClassConfig, function_config_id: UUID, access_level: AccessLevelType
) -> RoleConfigClassConfigFunctionConfig:
    """
    Upsert a function-level policy edge for this class-level policy node.

    Notes:
    - `function_config_id` refers to `aware_meta.function.FunctionConfig`.
    - Idempotent by (`role_config_class_config_id`, `function_config_id`).
    """

    # --- AWARE: LOGIC START upsert_function_config_policy
    if role_config_class_config.id is None:
        raise ValueError(
            "RoleConfigClassConfig.upsert_function_config_policy requires a bound role_config_class_config.id"
        )

    if not isinstance(function_config_id, UUID):
        raise ValueError("RoleConfigClassConfig.upsert_function_config_policy requires a valid function_config_id UUID")

    edge_id = stable_role_config_class_config_function_config_id(
        role_config_class_config_id=role_config_class_config.id,
        function_config_id=function_config_id,
    )

    for existing_edge in role_config_class_config.role_config_class_config_function_configs:
        if existing_edge.id == edge_id:
            return existing_edge

    edge = await RoleConfigClassConfigFunctionConfig.create_via_role_config_class_config(
        role_config_class_config_id=role_config_class_config.id,
        function_config_id=function_config_id,
        access_level=access_level,
    )
    role_config_class_config.role_config_class_config_function_configs.append(edge)
    return edge
    # --- AWARE: LOGIC END upsert_function_config_policy


async def create_via_role_config(
    role_config_id: UUID, class_config_id: UUID, access_level: AccessLevelType
) -> RoleConfigClassConfig:
    """
    Create a RoleConfigClassConfig policy node (commit-backed).

    Runtime invariants:
    - Must be created via a constructor invocation (propagation), not by direct instantiation inside an
    instance handler.
    - Stable id is derived from (role_config_id, class_config_id).
    """

    # --- AWARE: LOGIC START create_via_role_config
    rccc_id = stable_role_config_class_config_id(
        role_config_id=role_config_id,
        class_config_id=class_config_id,
    )
    return RoleConfigClassConfig(
        id=rccc_id,
        role_config_id=role_config_id,
        class_config_id=class_config_id,
        access_level=access_level,
    )
    # --- AWARE: LOGIC END create_via_role_config
