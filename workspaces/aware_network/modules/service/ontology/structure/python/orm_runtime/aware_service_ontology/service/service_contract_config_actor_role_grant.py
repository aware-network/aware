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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.role.role_config import RoleConfig


class ServiceContractConfigActorRoleGrant(ORMModel):
    # Relationships
    role_config: RoleConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_scope: str = Field(default="service")
    class_instance_identity_required: bool = Field(default=False)
    description: str | None = Field(default=None)
    grant_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    role_assignment_binding_required: bool = Field(default=True)
    scope_kind: str = Field(default="service")
    scope_ref: str = Field(default="default")

    # Foreign Keys
    service_contract_config_id: UUID = Field(description="Foreign key for ServiceContractConfig.actor_role_grants")
    role_config_id: UUID = Field(description="Foreign key for ServiceContractConfigActorRoleGrant.role_config")

    @classmethod
    async def build_via_service_contract_config(
        cls,
        service_contract_config_id: UUID,
        role_config_id: UUID,
        scope_kind: str = "service",
        scope_ref: str = "default",
        access_scope: str = "service",
        class_instance_identity_required: bool = False,
        role_assignment_binding_required: bool = True,
        grant_policy_json: JsonObject | None = {},
        description: str | None = None,
    ) -> ServiceContractConfigActorRoleGrant:
        """
        Creates one reusable ActorRole grant declaration under a ServiceContractConfig.

        Contract:
        - Parent ServiceContractConfig scope is propagated by constructor lowering.
        - Role policy remains owned by Identity RoleConfig.
        - Concrete ServiceContract activation can materialize/resolve ActorRole evidence through Identity.
        """

        payload = {
            "service_contract_config_id": service_contract_config_id,
            "role_config_id": role_config_id,
            "scope_kind": scope_kind,
            "scope_ref": scope_ref,
            "access_scope": access_scope,
            "class_instance_identity_required": class_instance_identity_required,
            "role_assignment_binding_required": role_assignment_binding_required,
            "grant_policy_json": grant_policy_json,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_contract_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContractConfigActorRoleGrant):
            return value
        return ServiceContractConfigActorRoleGrant.validate_invocation_value(value)


class ServiceContractConfigActorRoleGrantBuildViaServiceContractConfigInput(BaseModel):
    service_contract_config_id: UUID = Field(description="Foreign key for ServiceContractConfig.actor_role_grants")
    role_config_id: UUID
    scope_kind: str = Field(default="service")
    scope_ref: str = Field(default="default")
    access_scope: str = Field(default="service")
    class_instance_identity_required: bool = Field(default=False)
    role_assignment_binding_required: bool = Field(default=True)
    grant_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    description: str | None = Field(default=None)


class ServiceContractConfigActorRoleGrantBuildViaServiceContractConfigOutput(BaseModel):
    value: ServiceContractConfigActorRoleGrant


FUNCTIONS = {
    "ServiceContractConfigActorRoleGrant": {
        "build_via_service_contract_config": {
            "canonical": {
                "name": "build_via_service_contract_config",
                "description": "Creates one reusable ActorRole grant declaration under a ServiceContractConfig.\n\nContract:\n- Parent ServiceContractConfig scope is propagated by constructor lowering.\n- Role policy remains owned by Identity RoleConfig.\n- Concrete ServiceContract activation can materialize/resolve ActorRole evidence through Identity.",
                "is_constructor": True,
            },
            "input": ServiceContractConfigActorRoleGrantBuildViaServiceContractConfigInput,
            "output": ServiceContractConfigActorRoleGrantBuildViaServiceContractConfigOutput,
        },
    },
}

__all__ = [
    "ServiceContractConfigActorRoleGrant",
    "ServiceContractConfigActorRoleGrantBuildViaServiceContractConfigInput",
    "ServiceContractConfigActorRoleGrantBuildViaServiceContractConfigOutput",
    "FUNCTIONS",
]
