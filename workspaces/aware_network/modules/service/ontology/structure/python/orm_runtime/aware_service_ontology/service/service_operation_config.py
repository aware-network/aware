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
from aware_service_ontology.service.service_enums import (
    ServiceOperationAdmissionMode,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
)

if TYPE_CHECKING:
    from aware_economy_ontology.price.price import Price
    from aware_service_ontology.service.service_operation_config_api_endpoint import ServiceOperationConfigApiEndpoint
    from aware_service_ontology.service.service_operation_config_api_view import ServiceOperationConfigApiView
    from aware_service_ontology.service.service_operation_config_role_requirement import (
        ServiceOperationConfigRoleRequirement,
    )


class ServiceOperationConfig(ORMModel):
    # Relationships
    api_endpoints: list[ServiceOperationConfigApiEndpoint] = Field(default_factory=list, exclude=True)
    api_views: list[ServiceOperationConfigApiView] = Field(default_factory=list, exclude=True)
    price: Price | None = Field(default=None, exclude=True)
    role_requirements: list[ServiceOperationConfigRoleRequirement] = Field(default_factory=list, exclude=True)

    # Attributes
    admission_mode: ServiceOperationAdmissionMode = Field(default=ServiceOperationAdmissionMode.contract_required)
    description: str | None = Field(default=None)
    fulfillment_kind: ServiceOperationFulfillmentKind = Field(default=ServiceOperationFulfillmentKind.coordination)
    name: str
    receipt_policy: ServiceOperationReceiptPolicy = Field(default=ServiceOperationReceiptPolicy.committed)
    settlement_policy: ServiceOperationSettlementPolicy = Field(default=ServiceOperationSettlementPolicy.none)

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.service_operation_configs")
    price_id: UUID | None = Field(default=None, description="Foreign key for ServiceOperationConfig.price")

    async def create_api_endpoint(
        self, service_config_api_id: UUID, api_capability_endpoint_id: UUID, description: str | None = None
    ) -> ServiceOperationConfigApiEndpoint:
        """Creates one config-level endpoint binding under this ServiceOperationConfig."""

        payload = {
            "service_config_api_id": service_config_api_id,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="create_api_endpoint", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_operation_config_api_endpoint import (
            ServiceOperationConfigApiEndpoint,
        )

        if isinstance(value, ServiceOperationConfigApiEndpoint):
            return value
        return ServiceOperationConfigApiEndpoint.validate_invocation_value(value)

    async def create_api_view(
        self, service_config_api_id: UUID, api_view_id: UUID, description: str | None = None
    ) -> ServiceOperationConfigApiView:
        """
        Creates one config-level API view fulfillment binding under this ServiceOperationConfig.

        Contract:
        - ApiView is the API-owned readable view-state contract.
        - This ServiceOperationConfig declares that this service operation fulfills the ApiView state
        contract.
        - Experience composes above ApiView and is not the Service operation target.
        - Runtime view DTOs must carry provenance and actor/access evidence before protected use.
        """

        payload = {
            "service_config_api_id": service_config_api_id,
            "api_view_id": api_view_id,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="create_api_view", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_operation_config_api_view import ServiceOperationConfigApiView

        if isinstance(value, ServiceOperationConfigApiView):
            return value
        return ServiceOperationConfigApiView.validate_invocation_value(value)

    async def require_role(
        self,
        role_config_id: UUID,
        access_scope: str = "operation",
        scope_kind: str = "operation",
        scope_ref: str = "default",
        class_instance_identity_required: bool = False,
        role_assignment_binding_required: bool = True,
        description: str | None = None,
    ) -> ServiceOperationConfigRoleRequirement:
        """
        Declares ActorRole evidence required before this ServiceOperationConfig can execute.

        Contract:
        - Service declares the role requirement, Identity materializes and resolves ActorRole.
        - Runtime must fail closed when the required role evidence is missing or invalid.
        """

        payload = {
            "role_config_id": role_config_id,
            "access_scope": access_scope,
            "scope_kind": scope_kind,
            "scope_ref": scope_ref,
            "class_instance_identity_required": class_instance_identity_required,
            "role_assignment_binding_required": role_assignment_binding_required,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="require_role", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_operation_config_role_requirement import (
            ServiceOperationConfigRoleRequirement,
        )

        if isinstance(value, ServiceOperationConfigRoleRequirement):
            return value
        return ServiceOperationConfigRoleRequirement.validate_invocation_value(value)

    @classmethod
    async def build_via_service_config(
        cls,
        service_config_id: UUID,
        name: str,
        description: str | None = None,
        price_id: UUID | None = None,
        admission_mode: ServiceOperationAdmissionMode = ServiceOperationAdmissionMode.contract_required,
        fulfillment_kind: ServiceOperationFulfillmentKind = ServiceOperationFulfillmentKind.coordination,
        receipt_policy: ServiceOperationReceiptPolicy = ServiceOperationReceiptPolicy.committed,
        settlement_policy: ServiceOperationSettlementPolicy = ServiceOperationSettlementPolicy.none,
    ) -> ServiceOperationConfig:
        """
        Creates one canonical service operation definition under a ServiceConfig.

        Contract:
        - fulfillment_kind declares the service plane this operation may fulfill.
        - view is read-model state fulfillment.
        - coordination is ontology-plane graph/API coordination.
        - actuation is world-profile side-effect fulfillment.
        - Runtime dispatch must fail closed when the selected operation kind is
          incompatible with the dispatch shape.
        """

        payload = {
            "service_config_id": service_config_id,
            "name": name,
            "description": description,
            "price_id": price_id,
            "admission_mode": admission_mode,
            "fulfillment_kind": fulfillment_kind,
            "receipt_policy": receipt_policy,
            "settlement_policy": settlement_policy,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceOperationConfig):
            return value
        return ServiceOperationConfig.validate_invocation_value(value)


class ServiceOperationConfigCreateApiEndpointInput(BaseModel):
    service_config_api_id: UUID
    api_capability_endpoint_id: UUID
    description: str | None = Field(default=None)


class ServiceOperationConfigCreateApiEndpointOutput(BaseModel):
    value: ServiceOperationConfigApiEndpoint


class ServiceOperationConfigCreateApiViewInput(BaseModel):
    service_config_api_id: UUID
    api_view_id: UUID
    description: str | None = Field(default=None)


class ServiceOperationConfigCreateApiViewOutput(BaseModel):
    value: ServiceOperationConfigApiView


class ServiceOperationConfigRequireRoleInput(BaseModel):
    role_config_id: UUID
    access_scope: str = Field(default="operation")
    scope_kind: str = Field(default="operation")
    scope_ref: str = Field(default="default")
    class_instance_identity_required: bool = Field(default=False)
    role_assignment_binding_required: bool = Field(default=True)
    description: str | None = Field(default=None)


class ServiceOperationConfigRequireRoleOutput(BaseModel):
    value: ServiceOperationConfigRoleRequirement


class ServiceOperationConfigBuildViaServiceConfigInput(BaseModel):
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.service_operation_configs")
    name: str
    description: str | None = Field(default=None)
    price_id: UUID | None = Field(default=None)
    admission_mode: ServiceOperationAdmissionMode = Field(default=ServiceOperationAdmissionMode.contract_required)
    fulfillment_kind: ServiceOperationFulfillmentKind = Field(default=ServiceOperationFulfillmentKind.coordination)
    receipt_policy: ServiceOperationReceiptPolicy = Field(default=ServiceOperationReceiptPolicy.committed)
    settlement_policy: ServiceOperationSettlementPolicy = Field(default=ServiceOperationSettlementPolicy.none)


class ServiceOperationConfigBuildViaServiceConfigOutput(BaseModel):
    value: ServiceOperationConfig


FUNCTIONS = {
    "ServiceOperationConfig": {
        "create_api_endpoint": {
            "canonical": {
                "name": "create_api_endpoint",
                "description": "Creates one config-level endpoint binding under this ServiceOperationConfig.",
                "is_constructor": False,
            },
            "input": ServiceOperationConfigCreateApiEndpointInput,
            "output": ServiceOperationConfigCreateApiEndpointOutput,
        },
        "create_api_view": {
            "canonical": {
                "name": "create_api_view",
                "description": "Creates one config-level API view fulfillment binding under this ServiceOperationConfig.\n\nContract:\n- ApiView is the API-owned readable view-state contract.\n- This ServiceOperationConfig declares that this service operation fulfills the ApiView state contract.\n- Experience composes above ApiView and is not the Service operation target.\n- Runtime view DTOs must carry provenance and actor/access evidence before protected use.",
                "is_constructor": False,
            },
            "input": ServiceOperationConfigCreateApiViewInput,
            "output": ServiceOperationConfigCreateApiViewOutput,
        },
        "require_role": {
            "canonical": {
                "name": "require_role",
                "description": "Declares ActorRole evidence required before this ServiceOperationConfig can execute.\n\nContract:\n- Service declares the role requirement, Identity materializes and resolves ActorRole.\n- Runtime must fail closed when the required role evidence is missing or invalid.",
                "is_constructor": False,
            },
            "input": ServiceOperationConfigRequireRoleInput,
            "output": ServiceOperationConfigRequireRoleOutput,
        },
        "build_via_service_config": {
            "canonical": {
                "name": "build_via_service_config",
                "description": "Creates one canonical service operation definition under a ServiceConfig.\n\nContract:\n- fulfillment_kind declares the service plane this operation may fulfill.\n- view is read-model state fulfillment.\n- coordination is ontology-plane graph/API coordination.\n- actuation is world-profile side-effect fulfillment.\n- Runtime dispatch must fail closed when the selected operation kind is\n  incompatible with the dispatch shape.",
                "is_constructor": True,
            },
            "input": ServiceOperationConfigBuildViaServiceConfigInput,
            "output": ServiceOperationConfigBuildViaServiceConfigOutput,
        },
    },
}

__all__ = [
    "ServiceOperationConfig",
    "ServiceOperationConfigCreateApiEndpointInput",
    "ServiceOperationConfigCreateApiEndpointOutput",
    "ServiceOperationConfigCreateApiViewInput",
    "ServiceOperationConfigCreateApiViewOutput",
    "ServiceOperationConfigRequireRoleInput",
    "ServiceOperationConfigRequireRoleOutput",
    "ServiceOperationConfigBuildViaServiceConfigInput",
    "ServiceOperationConfigBuildViaServiceConfigOutput",
    "FUNCTIONS",
]
