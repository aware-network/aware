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

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceContractKind

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.projection.projection_experience import ProjectionExperience
    from aware_service_ontology.service.service_contract_config_actor_role_grant import (
        ServiceContractConfigActorRoleGrant,
    )
    from aware_service_ontology.service.service_contract_config_operation_grant import (
        ServiceContractConfigOperationGrant,
    )


class ServiceContractConfig(ORMModel):
    # Relationships
    actor_role_grants: list[ServiceContractConfigActorRoleGrant] = Field(default_factory=list, exclude=True)
    operation_grants: list[ServiceContractConfigOperationGrant] = Field(default_factory=list, exclude=True)
    projection_experience: ProjectionExperience | None = Field(default=None, exclude=True)

    # Attributes
    default_kind: ServiceContractKind = Field(default=ServiceContractKind.subscription)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    name: str

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.contract_configs")
    projection_experience_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceContractConfig.projection_experience"
    )

    async def grant_operation(
        self,
        service_operation_config_id: UUID,
        access_scope: str = "operation",
        quota_policy_json: JsonObject | None = {},
        permit_policy_json: JsonObject | None = {},
        price_policy_json: JsonObject | None = {},
        description: str | None = None,
    ) -> ServiceContractConfigOperationGrant:
        """
        Grants access to one ServiceOperationConfig for contracts created from this config.

        Contract:
        - ServiceContractConfig grants reusable executable operation access.
        - Economy primitives fund, reserve, and settle concrete ServiceContract use.
        - Service runtime must resolve the concrete ServiceContract to this config before execution.
        """

        payload = {
            "service_operation_config_id": service_operation_config_id,
            "access_scope": access_scope,
            "quota_policy_json": quota_policy_json,
            "permit_policy_json": permit_policy_json,
            "price_policy_json": price_policy_json,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="grant_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_contract_config_operation_grant import (
            ServiceContractConfigOperationGrant,
        )

        if isinstance(value, ServiceContractConfigOperationGrant):
            return value
        return ServiceContractConfigOperationGrant.validate_invocation_value(value)

    async def grant_actor_role(
        self,
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
        Declares the ActorRole grant/evidence contracts created from this config activate.

        Contract:
        - Role policy remains owned by Identity RoleConfig.
        - This config is activation/evidence input; Identity owns concrete ActorRole assignment truth.
        - Runtime uses resolved ActorRole evidence, not this declaration alone, for execution.
        """

        payload = {
            "role_config_id": role_config_id,
            "scope_kind": scope_kind,
            "scope_ref": scope_ref,
            "access_scope": access_scope,
            "class_instance_identity_required": class_instance_identity_required,
            "role_assignment_binding_required": role_assignment_binding_required,
            "grant_policy_json": grant_policy_json,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="grant_actor_role", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_contract_config_actor_role_grant import (
            ServiceContractConfigActorRoleGrant,
        )

        if isinstance(value, ServiceContractConfigActorRoleGrant):
            return value
        return ServiceContractConfigActorRoleGrant.validate_invocation_value(value)

    @classmethod
    async def build_via_service_config(
        cls,
        service_config_id: UUID,
        name: str,
        default_kind: ServiceContractKind = ServiceContractKind.subscription,
        projection_experience_id: UUID | None = None,
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ServiceContractConfig:
        """
        Creates one ServiceConfig-owned reusable contract definition.

        Contract:
        - Parent ServiceConfig scope is propagated by constructor lowering.
        - Stable identity is `(service_config_id, name)`.
        - This config declares reusable operation and ActorRole grants.
        - Concrete ServiceContract receipts point here when activated for a producer/consumer.
        """

        payload = {
            "service_config_id": service_config_id,
            "name": name,
            "default_kind": default_kind,
            "projection_experience_id": projection_experience_id,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceContractConfig):
            return value
        return ServiceContractConfig.validate_invocation_value(value)


class ServiceContractConfigGrantOperationInput(BaseModel):
    service_operation_config_id: UUID
    access_scope: str = Field(default="operation")
    quota_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    permit_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    price_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    description: str | None = Field(default=None)


class ServiceContractConfigGrantOperationOutput(BaseModel):
    value: ServiceContractConfigOperationGrant


class ServiceContractConfigGrantActorRoleInput(BaseModel):
    role_config_id: UUID
    scope_kind: str = Field(default="service")
    scope_ref: str = Field(default="default")
    access_scope: str = Field(default="service")
    class_instance_identity_required: bool = Field(default=False)
    role_assignment_binding_required: bool = Field(default=True)
    grant_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    description: str | None = Field(default=None)


class ServiceContractConfigGrantActorRoleOutput(BaseModel):
    value: ServiceContractConfigActorRoleGrant


class ServiceContractConfigBuildViaServiceConfigInput(BaseModel):
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.contract_configs")
    name: str
    default_kind: ServiceContractKind = Field(default=ServiceContractKind.subscription)
    projection_experience_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ServiceContractConfigBuildViaServiceConfigOutput(BaseModel):
    value: ServiceContractConfig


FUNCTIONS = {
    "ServiceContractConfig": {
        "grant_operation": {
            "canonical": {
                "name": "grant_operation",
                "description": "Grants access to one ServiceOperationConfig for contracts created from this config.\n\nContract:\n- ServiceContractConfig grants reusable executable operation access.\n- Economy primitives fund, reserve, and settle concrete ServiceContract use.\n- Service runtime must resolve the concrete ServiceContract to this config before execution.",
                "is_constructor": False,
            },
            "input": ServiceContractConfigGrantOperationInput,
            "output": ServiceContractConfigGrantOperationOutput,
        },
        "grant_actor_role": {
            "canonical": {
                "name": "grant_actor_role",
                "description": "Declares the ActorRole grant/evidence contracts created from this config activate.\n\nContract:\n- Role policy remains owned by Identity RoleConfig.\n- This config is activation/evidence input; Identity owns concrete ActorRole assignment truth.\n- Runtime uses resolved ActorRole evidence, not this declaration alone, for execution.",
                "is_constructor": False,
            },
            "input": ServiceContractConfigGrantActorRoleInput,
            "output": ServiceContractConfigGrantActorRoleOutput,
        },
        "build_via_service_config": {
            "canonical": {
                "name": "build_via_service_config",
                "description": "Creates one ServiceConfig-owned reusable contract definition.\n\nContract:\n- Parent ServiceConfig scope is propagated by constructor lowering.\n- Stable identity is `(service_config_id, name)`.\n- This config declares reusable operation and ActorRole grants.\n- Concrete ServiceContract receipts point here when activated for a producer/consumer.",
                "is_constructor": True,
            },
            "input": ServiceContractConfigBuildViaServiceConfigInput,
            "output": ServiceContractConfigBuildViaServiceConfigOutput,
        },
    },
}

__all__ = [
    "ServiceContractConfig",
    "ServiceContractConfigGrantOperationInput",
    "ServiceContractConfigGrantOperationOutput",
    "ServiceContractConfigGrantActorRoleInput",
    "ServiceContractConfigGrantActorRoleOutput",
    "ServiceContractConfigBuildViaServiceConfigInput",
    "ServiceContractConfigBuildViaServiceConfigOutput",
    "FUNCTIONS",
]
