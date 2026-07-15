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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_identity_ontology.role.role_config_class_config_function_config import (
        RoleConfigClassConfigFunctionConfig,
    )
    from aware_meta_ontology.class_.class_config import ClassConfig


class RoleConfigClassConfig(ORMModel):
    # Relationships
    role_config_class_config_function_configs: list[RoleConfigClassConfigFunctionConfig] = Field(
        default_factory=list, exclude=True
    )
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_level: AccessLevelType

    # Foreign Keys
    role_config_id: UUID = Field(description="Foreign key for RoleConfig.role_config_class_configs")
    class_config_id: UUID = Field(description="Foreign key for RoleConfigClassConfig.class_config")

    async def upsert_function_config_policy(
        self, function_config_id: UUID, access_level: AccessLevelType
    ) -> RoleConfigClassConfigFunctionConfig:
        """
        Upsert a function-level policy edge for this class-level policy node.

        Notes:
        - `function_config_id` refers to `aware_meta.function.FunctionConfig`.
        - Idempotent by (`role_config_class_config_id`, `function_config_id`).
        """

        payload = {"function_config_id": function_config_id, "access_level": access_level}
        result = await invoke_instance(orm_model=self, function_name="upsert_function_config_policy", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.role.role_config_class_config_function_config import (
            RoleConfigClassConfigFunctionConfig,
        )

        if isinstance(value, RoleConfigClassConfigFunctionConfig):
            return value
        return RoleConfigClassConfigFunctionConfig.validate_invocation_value(value)

    @classmethod
    async def create_via_role_config(
        cls, role_config_id: UUID, class_config_id: UUID, access_level: AccessLevelType
    ) -> RoleConfigClassConfig:
        """
        Create a RoleConfigClassConfig policy node (commit-backed).

        Runtime invariants:
        - Must be created via a constructor invocation (propagation), not by direct instantiation inside an
        instance handler.
        - Stable id is derived from (role_config_id, class_config_id).
        """

        payload = {"role_config_id": role_config_id, "class_config_id": class_config_id, "access_level": access_level}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_role_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RoleConfigClassConfig):
            return value
        return RoleConfigClassConfig.validate_invocation_value(value)


class RoleConfigClassConfigUpsertFunctionConfigPolicyInput(BaseModel):
    function_config_id: UUID
    access_level: AccessLevelType


class RoleConfigClassConfigUpsertFunctionConfigPolicyOutput(BaseModel):
    value: RoleConfigClassConfigFunctionConfig


class RoleConfigClassConfigCreateViaRoleConfigInput(BaseModel):
    role_config_id: UUID = Field(description="Foreign key for RoleConfig.role_config_class_configs")
    class_config_id: UUID
    access_level: AccessLevelType


class RoleConfigClassConfigCreateViaRoleConfigOutput(BaseModel):
    value: RoleConfigClassConfig


FUNCTIONS = {
    "RoleConfigClassConfig": {
        "upsert_function_config_policy": {
            "canonical": {
                "name": "upsert_function_config_policy",
                "description": "Upsert a function-level policy edge for this class-level policy node.\n\nNotes:\n- `function_config_id` refers to `aware_meta.function.FunctionConfig`.\n- Idempotent by (`role_config_class_config_id`, `function_config_id`).",
                "is_constructor": False,
            },
            "input": RoleConfigClassConfigUpsertFunctionConfigPolicyInput,
            "output": RoleConfigClassConfigUpsertFunctionConfigPolicyOutput,
        },
        "create_via_role_config": {
            "canonical": {
                "name": "create_via_role_config",
                "description": "Create a RoleConfigClassConfig policy node (commit-backed).\n\nRuntime invariants:\n- Must be created via a constructor invocation (propagation), not by direct instantiation inside an instance handler.\n- Stable id is derived from (role_config_id, class_config_id).",
                "is_constructor": True,
            },
            "input": RoleConfigClassConfigCreateViaRoleConfigInput,
            "output": RoleConfigClassConfigCreateViaRoleConfigOutput,
        },
    },
}

__all__ = [
    "RoleConfigClassConfig",
    "RoleConfigClassConfigUpsertFunctionConfigPolicyInput",
    "RoleConfigClassConfigUpsertFunctionConfigPolicyOutput",
    "RoleConfigClassConfigCreateViaRoleConfigInput",
    "RoleConfigClassConfigCreateViaRoleConfigOutput",
    "FUNCTIONS",
]
