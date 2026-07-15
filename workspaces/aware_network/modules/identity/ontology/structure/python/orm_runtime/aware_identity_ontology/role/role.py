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
    from aware_identity_ontology.role.role_class_instance import RoleClassInstance
    from aware_identity_ontology.role.role_config import RoleConfig
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class Role(ORMModel):
    # Relationships
    role_class_instances: list[RoleClassInstance] = Field(default_factory=list)
    role_config: RoleConfig | None = Field(default=None, exclude=True)
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Attributes
    object_instance_graph_branch_key: str = Field(default="all")

    # Foreign Keys
    role_config_id: UUID = Field(description="Foreign key for Role.role_config")
    object_instance_graph_identity_id: UUID = Field(description="Foreign key for Role.object_instance_graph_identity")
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for Role.object_instance_graph_branch"
    )

    @classmethod
    async def create(
        cls,
        role_config_id: UUID,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
    ) -> Role:
        """
        Create a canonical Role binding scoped to graph identity.

        Contract (v0):
        - Deterministic id from (role_config_id, object_instance_graph_identity_id,
        object_instance_graph_branch_key).
        - `object_instance_graph_branch_id` is an optional reference binding and does not participate in
        identity.
        - Role scope is the lane envelope only (OIGI required, OIGB optional).
        - Concrete object grants are modeled under `RoleClassInstance`.
        """

        payload = {
            "role_config_id": role_config_id,
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "object_instance_graph_branch_key": object_instance_graph_branch_key,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Role):
            return value
        return Role.validate_invocation_value(value)

    async def add_class_instance(
        self, class_instance_identity_id: UUID, role_config_class_config_id: UUID
    ) -> RoleClassInstance:
        """
        Add one concrete ClassInstanceIdentity grant under this Role.

        Contract:
        - Role remains the lane envelope; `RoleClassInstance` carries object-worldline membership.
        - Capabilities are inherited from the linked `RoleConfigClassConfig`.
        - Idempotent for repeated grants of the same class-instance under the same role.
        """

        payload = {
            "class_instance_identity_id": class_instance_identity_id,
            "role_config_class_config_id": role_config_class_config_id,
        }
        result = await invoke_instance(orm_model=self, function_name="add_class_instance", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.role.role_class_instance import RoleClassInstance

        if isinstance(value, RoleClassInstance):
            return value
        return RoleClassInstance.validate_invocation_value(value)

    async def remove_class_instance(self, class_instance_identity_id: UUID, role_config_class_config_id: UUID) -> None:
        """
        Remove one concrete ClassInstanceIdentity grant under this Role.

        Contract:
        - This is only honest when the caller has already proven that the enclosing Role
          envelope should no longer expose the target class-instance grant.
        - Missing target grants are a no-op.
        - Ambiguous policy bindings for one class-instance fail closed.
        """

        payload = {
            "class_instance_identity_id": class_instance_identity_id,
            "role_config_class_config_id": role_config_class_config_id,
        }
        await invoke_instance(orm_model=self, function_name="remove_class_instance", payload=payload)
        return None

    async def delete(self) -> None:
        """
        Delete an empty Role envelope after all actor-role edges and class-instance grants
        have already been removed.
        """

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None


class RoleCreateInput(BaseModel):
    role_config_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)


class RoleCreateOutput(BaseModel):
    value: Role


class RoleAddClassInstanceInput(BaseModel):
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID


class RoleAddClassInstanceOutput(BaseModel):
    value: RoleClassInstance


class RoleRemoveClassInstanceInput(BaseModel):
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID


class RoleRemoveClassInstanceOutput(BaseModel):
    pass


class RoleDeleteInput(BaseModel):
    pass


class RoleDeleteOutput(BaseModel):
    pass


FUNCTIONS = {
    "Role": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create a canonical Role binding scoped to graph identity.\n\nContract (v0):\n- Deterministic id from (role_config_id, object_instance_graph_identity_id, object_instance_graph_branch_key).\n- `object_instance_graph_branch_id` is an optional reference binding and does not participate in identity.\n- Role scope is the lane envelope only (OIGI required, OIGB optional).\n- Concrete object grants are modeled under `RoleClassInstance`.",
                "is_constructor": True,
            },
            "input": RoleCreateInput,
            "output": RoleCreateOutput,
        },
        "add_class_instance": {
            "canonical": {
                "name": "add_class_instance",
                "description": "Add one concrete ClassInstanceIdentity grant under this Role.\n\nContract:\n- Role remains the lane envelope; `RoleClassInstance` carries object-worldline membership.\n- Capabilities are inherited from the linked `RoleConfigClassConfig`.\n- Idempotent for repeated grants of the same class-instance under the same role.",
                "is_constructor": False,
            },
            "input": RoleAddClassInstanceInput,
            "output": RoleAddClassInstanceOutput,
        },
        "remove_class_instance": {
            "canonical": {
                "name": "remove_class_instance",
                "description": "Remove one concrete ClassInstanceIdentity grant under this Role.\n\nContract:\n- This is only honest when the caller has already proven that the enclosing Role\n  envelope should no longer expose the target class-instance grant.\n- Missing target grants are a no-op.\n- Ambiguous policy bindings for one class-instance fail closed.",
                "is_constructor": False,
            },
            "input": RoleRemoveClassInstanceInput,
            "output": RoleRemoveClassInstanceOutput,
        },
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete an empty Role envelope after all actor-role edges and class-instance grants\nhave already been removed.",
                "is_constructor": False,
            },
            "input": RoleDeleteInput,
            "output": RoleDeleteOutput,
        },
    },
}

__all__ = [
    "Role",
    "RoleCreateInput",
    "RoleCreateOutput",
    "RoleAddClassInstanceInput",
    "RoleAddClassInstanceOutput",
    "RoleRemoveClassInstanceInput",
    "RoleRemoveClassInstanceOutput",
    "RoleDeleteInput",
    "RoleDeleteOutput",
    "FUNCTIONS",
]
