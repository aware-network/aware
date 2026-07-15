from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.role.role_enums import AccessLevelType
from aware_identity_ontology.role.role_config_class_config_function_config import RoleConfigClassConfigFunctionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import (
    stable_role_config_class_config_function_config_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_role_config_class_config(
    role_config_class_config_id: UUID, function_config_id: UUID, access_level: AccessLevelType
) -> RoleConfigClassConfigFunctionConfig:
    """
    Create a commit-backed function policy edge under a class policy node.

    Contract (v0):
    - Stable id from (`role_config_class_config_id`, `function_config_id`).
    - Idempotent constructor for deterministic role policy commits.
    """

    # --- AWARE: LOGIC START create_via_role_config_class_config
    edge_id = stable_role_config_class_config_function_config_id(
        role_config_class_config_id=role_config_class_config_id,
        function_config_id=function_config_id,
    )
    return RoleConfigClassConfigFunctionConfig(
        id=edge_id,
        role_config_class_config_id=role_config_class_config_id,
        function_config_id=function_config_id,
        access_level=access_level,
    )
    # --- AWARE: LOGIC END create_via_role_config_class_config
