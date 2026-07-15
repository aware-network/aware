from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
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
    ServiceContractKind,
    ServiceContractStatus,
    ServiceOperationStatus,
    ServicePlanCycle,
)

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_service_ontology.service.service_branch import ServiceBranch
    from aware_service_ontology.service.service_commercial_profile import ServiceCommercialProfile
    from aware_service_ontology.service.service_contract import ServiceContract
    from aware_service_ontology.service.service_operation import ServiceOperation
    from aware_service_ontology.service.service_plan import ServicePlan


class Service(ORMModel):
    # Relationships
    branches: list[ServiceBranch] = Field(default_factory=list, exclude=True)
    commercial_profile: ServiceCommercialProfile | None = Field(default=None, exclude=True)
    contracts: list[ServiceContract] = Field(default_factory=list, exclude=True)
    plans: list[ServicePlan] = Field(default_factory=list, exclude=True)
    service_operations: list[ServiceOperation] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    name: str

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.services")

    async def create_operation(
        self,
        service_operation_config_id: UUID,
        operation_key: str,
        api_call_id: UUID | None = None,
        api_endpoint_id: UUID | None = None,
        status: ServiceOperationStatus = ServiceOperationStatus.queued,
        result_info: str | None = None,
        execution_context: JsonObject | None = None,
    ) -> ServiceOperation:
        """Creates one canonical service execution receipt under this concrete Service."""

        payload = {
            "service_operation_config_id": service_operation_config_id,
            "operation_key": operation_key,
            "api_call_id": api_call_id,
            "api_endpoint_id": api_endpoint_id,
            "status": status,
            "result_info": result_info,
            "execution_context": execution_context,
        }
        result = await invoke_instance(orm_model=self, function_name="create_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_operation import ServiceOperation

        if isinstance(value, ServiceOperation):
            return value
        return ServiceOperation.validate_invocation_value(value)

    async def create_commercial_profile(
        self,
        producer_finance_entity_id: UUID,
        default_smart_contract_config_id: UUID | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ServiceCommercialProfile:
        """Creates or ensures the canonical producer-side commercial profile for this Service."""

        payload = {
            "producer_finance_entity_id": producer_finance_entity_id,
            "default_smart_contract_config_id": default_smart_contract_config_id,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="create_commercial_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_commercial_profile import ServiceCommercialProfile

        if isinstance(value, ServiceCommercialProfile):
            return value
        return ServiceCommercialProfile.validate_invocation_value(value)

    async def create_contract(
        self,
        service_contract_config_id: UUID,
        commercial_profile_id: UUID,
        producer_finance_entity_id: UUID,
        consumer_finance_entity_id: UUID,
        smart_contract_id: UUID,
        kind: ServiceContractKind,
        effective_from: datetime,
        status: ServiceContractStatus = ServiceContractStatus.pending,
        effective_until: datetime | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ServiceContract:
        """Creates one Service-owned commercial agreement receipt under this Service."""

        payload = {
            "service_contract_config_id": service_contract_config_id,
            "commercial_profile_id": commercial_profile_id,
            "producer_finance_entity_id": producer_finance_entity_id,
            "consumer_finance_entity_id": consumer_finance_entity_id,
            "smart_contract_id": smart_contract_id,
            "kind": kind,
            "effective_from": effective_from,
            "status": status,
            "effective_until": effective_until,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="create_contract", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_contract import ServiceContract

        if isinstance(value, ServiceContract):
            return value
        return ServiceContract.validate_invocation_value(value)

    async def create_plan(
        self,
        cycle: ServicePlanCycle,
        price_amount: Annotated[Decimal, DecimalWire()],
        coin_id: UUID,
        smart_contract_config_id: UUID,
        external_price_handle: str | None = None,
        policy_json: JsonObject = {},
    ) -> ServicePlan:
        """Appends one provider-owned pricing plan under this concrete Service."""

        payload = {
            "cycle": cycle,
            "price_amount": price_amount,
            "coin_id": coin_id,
            "smart_contract_config_id": smart_contract_config_id,
            "external_price_handle": external_price_handle,
            "policy_json": policy_json,
        }
        result = await invoke_instance(orm_model=self, function_name="create_plan", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_plan import ServicePlan

        if isinstance(value, ServicePlan):
            return value
        return ServicePlan.validate_invocation_value(value)

    async def create_branch(
        self,
        service_config_api_projection_id: UUID,
        object_instance_graph_branch_id: UUID,
        description: str | None = None,
    ) -> ServiceBranch:
        """Creates one concrete subscribed branch binding under this Service."""

        payload = {
            "service_config_api_projection_id": service_config_api_projection_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="create_branch", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_branch import ServiceBranch

        if isinstance(value, ServiceBranch):
            return value
        return ServiceBranch.validate_invocation_value(value)

    @classmethod
    async def build_via_service_config(
        cls, service_config_id: UUID, name: str, description: str | None = None
    ) -> Service:
        """Creates one Service instance under a ServiceConfig."""

        payload = {"service_config_id": service_config_id, "name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Service):
            return value
        return Service.validate_invocation_value(value)


class ServiceCreateOperationInput(BaseModel):
    service_operation_config_id: UUID
    operation_key: str
    api_call_id: UUID | None = Field(default=None)
    api_endpoint_id: UUID | None = Field(default=None)
    status: ServiceOperationStatus = Field(default=ServiceOperationStatus.queued)
    result_info: str | None = Field(default=None)
    execution_context: JsonObject | None = Field(default=None)


class ServiceCreateOperationOutput(BaseModel):
    value: ServiceOperation


class ServiceCreateCommercialProfileInput(BaseModel):
    producer_finance_entity_id: UUID
    default_smart_contract_config_id: UUID | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ServiceCreateCommercialProfileOutput(BaseModel):
    value: ServiceCommercialProfile


class ServiceCreateContractInput(BaseModel):
    service_contract_config_id: UUID
    commercial_profile_id: UUID
    producer_finance_entity_id: UUID
    consumer_finance_entity_id: UUID
    smart_contract_id: UUID
    kind: ServiceContractKind
    effective_from: datetime
    status: ServiceContractStatus = Field(default=ServiceContractStatus.pending)
    effective_until: datetime | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ServiceCreateContractOutput(BaseModel):
    value: ServiceContract


class ServiceCreatePlanInput(BaseModel):
    cycle: ServicePlanCycle
    price_amount: Annotated[Decimal, DecimalWire()]
    coin_id: UUID
    smart_contract_config_id: UUID
    external_price_handle: str | None = Field(default=None)
    policy_json: JsonObject = Field(default_factory=JsonObject)


class ServiceCreatePlanOutput(BaseModel):
    value: ServicePlan


class ServiceCreateBranchInput(BaseModel):
    service_config_api_projection_id: UUID
    object_instance_graph_branch_id: UUID
    description: str | None = Field(default=None)


class ServiceCreateBranchOutput(BaseModel):
    value: ServiceBranch


class ServiceBuildViaServiceConfigInput(BaseModel):
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.services")
    name: str
    description: str | None = Field(default=None)


class ServiceBuildViaServiceConfigOutput(BaseModel):
    value: Service


FUNCTIONS = {
    "Service": {
        "create_operation": {
            "canonical": {
                "name": "create_operation",
                "description": "Creates one canonical service execution receipt under this concrete Service.",
                "is_constructor": False,
            },
            "input": ServiceCreateOperationInput,
            "output": ServiceCreateOperationOutput,
        },
        "create_commercial_profile": {
            "canonical": {
                "name": "create_commercial_profile",
                "description": "Creates or ensures the canonical producer-side commercial profile for this Service.",
                "is_constructor": False,
            },
            "input": ServiceCreateCommercialProfileInput,
            "output": ServiceCreateCommercialProfileOutput,
        },
        "create_contract": {
            "canonical": {
                "name": "create_contract",
                "description": "Creates one Service-owned commercial agreement receipt under this Service.",
                "is_constructor": False,
            },
            "input": ServiceCreateContractInput,
            "output": ServiceCreateContractOutput,
        },
        "create_plan": {
            "canonical": {
                "name": "create_plan",
                "description": "Appends one provider-owned pricing plan under this concrete Service.",
                "is_constructor": False,
            },
            "input": ServiceCreatePlanInput,
            "output": ServiceCreatePlanOutput,
        },
        "create_branch": {
            "canonical": {
                "name": "create_branch",
                "description": "Creates one concrete subscribed branch binding under this Service.",
                "is_constructor": False,
            },
            "input": ServiceCreateBranchInput,
            "output": ServiceCreateBranchOutput,
        },
        "build_via_service_config": {
            "canonical": {
                "name": "build_via_service_config",
                "description": "Creates one Service instance under a ServiceConfig.",
                "is_constructor": True,
            },
            "input": ServiceBuildViaServiceConfigInput,
            "output": ServiceBuildViaServiceConfigOutput,
        },
    },
}

__all__ = [
    "Service",
    "ServiceCreateOperationInput",
    "ServiceCreateOperationOutput",
    "ServiceCreateCommercialProfileInput",
    "ServiceCreateCommercialProfileOutput",
    "ServiceCreateContractInput",
    "ServiceCreateContractOutput",
    "ServiceCreatePlanInput",
    "ServiceCreatePlanOutput",
    "ServiceCreateBranchInput",
    "ServiceCreateBranchOutput",
    "ServiceBuildViaServiceConfigInput",
    "ServiceBuildViaServiceConfigOutput",
    "FUNCTIONS",
]
