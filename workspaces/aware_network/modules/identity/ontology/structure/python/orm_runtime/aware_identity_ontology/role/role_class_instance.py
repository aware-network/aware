from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_identity_ontology.role.role_config_class_config import RoleConfigClassConfig
    from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity


class RoleClassInstance(ORMModel):
    # Relationships
    class_instance_identity: ClassInstanceIdentity | None = Field(default=None, exclude=True)
    role_config_class_config: RoleConfigClassConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    role_id: UUID = Field(description="Foreign key for Role.role_class_instances")
    class_instance_identity_id: UUID = Field(description="Foreign key for RoleClassInstance.class_instance_identity")
    role_config_class_config_id: UUID = Field(description="Foreign key for RoleClassInstance.role_config_class_config")

    async def delete(self) -> None:
        """Delete this concrete class-instance grant membership."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None

    @classmethod
    async def create_via_role(
        cls, role_id: UUID, class_instance_identity_id: UUID, role_config_class_config_id: UUID
    ) -> RoleClassInstance:
        """
        Create a concrete class-instance grant membership under one Role.

        Contract (v0):
        - Deterministic id from (`role_id`, `class_instance_identity_id`, `role_config_class_config_id`).
        - `role_config_class_config_id` points to the inherited class-kind capability policy.
        - One Role may include many concrete ClassInstanceIdentity grants.
        """

        payload = {
            "role_id": role_id,
            "class_instance_identity_id": class_instance_identity_id,
            "role_config_class_config_id": role_config_class_config_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_role", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RoleClassInstance):
            return value
        return RoleClassInstance.validate_invocation_value(value)


class RoleClassInstanceDeleteInput(BaseModel):
    pass


class RoleClassInstanceDeleteOutput(BaseModel):
    pass


class RoleClassInstanceCreateViaRoleInput(BaseModel):
    role_id: UUID = Field(description="Foreign key for Role.role_class_instances")
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID


class RoleClassInstanceCreateViaRoleOutput(BaseModel):
    value: RoleClassInstance


FUNCTIONS = {
    "RoleClassInstance": {
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete this concrete class-instance grant membership.",
                "is_constructor": False,
            },
            "input": RoleClassInstanceDeleteInput,
            "output": RoleClassInstanceDeleteOutput,
        },
        "create_via_role": {
            "canonical": {
                "name": "create_via_role",
                "description": "Create a concrete class-instance grant membership under one Role.\n\nContract (v0):\n- Deterministic id from (`role_id`, `class_instance_identity_id`, `role_config_class_config_id`).\n- `role_config_class_config_id` points to the inherited class-kind capability policy.\n- One Role may include many concrete ClassInstanceIdentity grants.",
                "is_constructor": True,
            },
            "input": RoleClassInstanceCreateViaRoleInput,
            "output": RoleClassInstanceCreateViaRoleOutput,
        },
    },
}

__all__ = [
    "RoleClassInstance",
    "RoleClassInstanceDeleteInput",
    "RoleClassInstanceDeleteOutput",
    "RoleClassInstanceCreateViaRoleInput",
    "RoleClassInstanceCreateViaRoleOutput",
    "FUNCTIONS",
]
