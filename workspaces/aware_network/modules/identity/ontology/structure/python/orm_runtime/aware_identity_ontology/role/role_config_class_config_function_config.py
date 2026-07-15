from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.role.role_enums import AccessLevelType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_config import FunctionConfig


class RoleConfigClassConfigFunctionConfig(ORMModel):
    # Relationships
    function_config: FunctionConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_level: AccessLevelType

    # Foreign Keys
    role_config_class_config_id: UUID = Field(
        description="Foreign key for RoleConfigClassConfig.role_config_class_config_function_configs"
    )
    function_config_id: UUID = Field(description="Foreign key for RoleConfigClassConfigFunctionConfig.function_config")

    @classmethod
    async def create_via_role_config_class_config(
        cls, role_config_class_config_id: UUID, function_config_id: UUID, access_level: AccessLevelType
    ) -> RoleConfigClassConfigFunctionConfig:
        """
        Create a commit-backed function policy edge under a class policy node.

        Contract (v0):
        - Stable id from (`role_config_class_config_id`, `function_config_id`).
        - Idempotent constructor for deterministic role policy commits.
        """

        payload = {
            "role_config_class_config_id": role_config_class_config_id,
            "function_config_id": function_config_id,
            "access_level": access_level,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_role_config_class_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RoleConfigClassConfigFunctionConfig):
            return value
        return RoleConfigClassConfigFunctionConfig.validate_invocation_value(value)


class RoleConfigClassConfigFunctionConfigCreateViaRoleConfigClassConfigInput(BaseModel):
    role_config_class_config_id: UUID = Field(
        description="Foreign key for RoleConfigClassConfig.role_config_class_config_function_configs"
    )
    function_config_id: UUID
    access_level: AccessLevelType


class RoleConfigClassConfigFunctionConfigCreateViaRoleConfigClassConfigOutput(BaseModel):
    value: RoleConfigClassConfigFunctionConfig


FUNCTIONS = {
    "RoleConfigClassConfigFunctionConfig": {
        "create_via_role_config_class_config": {
            "canonical": {
                "name": "create_via_role_config_class_config",
                "description": "Create a commit-backed function policy edge under a class policy node.\n\nContract (v0):\n- Stable id from (`role_config_class_config_id`, `function_config_id`).\n- Idempotent constructor for deterministic role policy commits.",
                "is_constructor": True,
            },
            "input": RoleConfigClassConfigFunctionConfigCreateViaRoleConfigClassConfigInput,
            "output": RoleConfigClassConfigFunctionConfigCreateViaRoleConfigClassConfigOutput,
        },
    },
}

__all__ = [
    "RoleConfigClassConfigFunctionConfig",
    "RoleConfigClassConfigFunctionConfigCreateViaRoleConfigClassConfigInput",
    "RoleConfigClassConfigFunctionConfigCreateViaRoleConfigClassConfigOutput",
    "FUNCTIONS",
]
