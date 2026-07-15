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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_identity_ontology.role.role_config import RoleConfig


class ServiceOperationConfigRoleRequirement(ORMModel):
    # Relationships
    role_config: RoleConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_scope: str = Field(default="operation")
    class_instance_identity_required: bool = Field(default=False)
    description: str | None = Field(default=None)
    role_assignment_binding_required: bool = Field(default=True)
    scope_kind: str = Field(default="operation")
    scope_ref: str = Field(default="default")

    # Foreign Keys
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperationConfig.role_requirements")
    role_config_id: UUID = Field(description="Foreign key for ServiceOperationConfigRoleRequirement.role_config")

    @classmethod
    async def build_via_service_operation_config(
        cls,
        service_operation_config_id: UUID,
        role_config_id: UUID,
        access_scope: str = "operation",
        scope_kind: str = "operation",
        scope_ref: str = "default",
        class_instance_identity_required: bool = False,
        role_assignment_binding_required: bool = True,
        description: str | None = None,
    ) -> ServiceOperationConfigRoleRequirement:
        """
        Creates one ActorRole evidence requirement for a ServiceOperationConfig.

        Contract:
        - Role policy remains owned by Identity RoleConfig.
        - ServiceOperationConfig only declares the evidence required before operation/view fulfillment.
        - Runtime gate must resolve this through Identity and fail closed when missing.
        """

        payload = {
            "service_operation_config_id": service_operation_config_id,
            "role_config_id": role_config_id,
            "access_scope": access_scope,
            "scope_kind": scope_kind,
            "scope_ref": scope_ref,
            "class_instance_identity_required": class_instance_identity_required,
            "role_assignment_binding_required": role_assignment_binding_required,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_operation_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceOperationConfigRoleRequirement):
            return value
        return ServiceOperationConfigRoleRequirement.validate_invocation_value(value)


class ServiceOperationConfigRoleRequirementBuildViaServiceOperationConfigInput(BaseModel):
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperationConfig.role_requirements")
    role_config_id: UUID
    access_scope: str = Field(default="operation")
    scope_kind: str = Field(default="operation")
    scope_ref: str = Field(default="default")
    class_instance_identity_required: bool = Field(default=False)
    role_assignment_binding_required: bool = Field(default=True)
    description: str | None = Field(default=None)


class ServiceOperationConfigRoleRequirementBuildViaServiceOperationConfigOutput(BaseModel):
    value: ServiceOperationConfigRoleRequirement


FUNCTIONS = {
    "ServiceOperationConfigRoleRequirement": {
        "build_via_service_operation_config": {
            "canonical": {
                "name": "build_via_service_operation_config",
                "description": "Creates one ActorRole evidence requirement for a ServiceOperationConfig.\n\nContract:\n- Role policy remains owned by Identity RoleConfig.\n- ServiceOperationConfig only declares the evidence required before operation/view fulfillment.\n- Runtime gate must resolve this through Identity and fail closed when missing.",
                "is_constructor": True,
            },
            "input": ServiceOperationConfigRoleRequirementBuildViaServiceOperationConfigInput,
            "output": ServiceOperationConfigRoleRequirementBuildViaServiceOperationConfigOutput,
        },
    },
}

__all__ = [
    "ServiceOperationConfigRoleRequirement",
    "ServiceOperationConfigRoleRequirementBuildViaServiceOperationConfigInput",
    "ServiceOperationConfigRoleRequirementBuildViaServiceOperationConfigOutput",
    "FUNCTIONS",
]
