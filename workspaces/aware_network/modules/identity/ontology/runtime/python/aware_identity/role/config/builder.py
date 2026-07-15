# Standard Imports
from uuid import UUID

# Kernel Graph Ontology
from aware_identity_ontology.role.role_config import RoleConfig
from aware_identity_ontology.role.role_config_class_config import RoleConfigClassConfig
from aware_identity_ontology.role.role_config_class_config_function_config import (
    RoleConfigClassConfigFunctionConfig,
)
from aware_identity_ontology.role.role_enums import AccessLevelType


def build_role_config(
    name: str,
    description: str | None = None,
) -> RoleConfig:
    """Create a RoleConfig with class/function mappings.

    Args:
        name: Role name
        description: Optional description
    Returns:
        Persisted RoleConfig instance with related RoleConfigClassConfig entries
    """

    role = RoleConfig(name=name, description=description)
    return role


def build_role_config_class_config(
    role: RoleConfig,
    class_config_id: UUID,
    function_config_ids: list[UUID],
    access_level: AccessLevelType,
) -> RoleConfigClassConfig:

    role_config_class_config = RoleConfigClassConfig(
        access_level=access_level,
        class_config_id=class_config_id,
        role_config_id=role.id,
    )
    for fn_id in function_config_ids:
        rcfunc = RoleConfigClassConfigFunctionConfig(
            access_level=access_level,
            role_config_class_config_id=role_config_class_config.id,
            function_config_id=fn_id,
        )
        role_config_class_config.role_config_class_config_function_configs.append(rcfunc)
    return role_config_class_config
