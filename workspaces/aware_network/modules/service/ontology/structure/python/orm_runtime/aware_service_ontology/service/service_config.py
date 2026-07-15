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
    ServiceConfigCodePackageConfigCardinality,
    ServiceContractKind,
    ServiceOperationAdmissionMode,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_service_ontology.service.service import Service
    from aware_service_ontology.service.service_config_api import ServiceConfigApi
    from aware_service_ontology.service.service_config_code_package_config import ServiceConfigCodePackageConfig
    from aware_service_ontology.service.service_config_experience import ServiceConfigExperience
    from aware_service_ontology.service.service_contract_config import ServiceContractConfig
    from aware_service_ontology.service.service_operation_config import ServiceOperationConfig


class ServiceConfig(ORMModel):
    # Relationships
    apis: list[ServiceConfigApi] = Field(default_factory=list, exclude=True)
    contract_configs: list[ServiceContractConfig] = Field(default_factory=list, exclude=True)
    code_package_configs: list[ServiceConfigCodePackageConfig] = Field(default_factory=list)
    experiences: list[ServiceConfigExperience] = Field(default_factory=list, exclude=True)
    service_operation_configs: list[ServiceOperationConfig] = Field(default_factory=list, exclude=True)
    services: list[Service] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    name: str

    @classmethod
    async def build(cls, name: str, description: str | None = None) -> ServiceConfig:
        """Creates one canonical service capability definition."""

        payload = {"name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceConfig):
            return value
        return ServiceConfig.validate_invocation_value(value)

    async def create_service_operation_config(
        self,
        name: str,
        description: str | None = None,
        price_id: UUID | None = None,
        admission_mode: ServiceOperationAdmissionMode = ServiceOperationAdmissionMode.contract_required,
        fulfillment_kind: ServiceOperationFulfillmentKind = ServiceOperationFulfillmentKind.coordination,
        receipt_policy: ServiceOperationReceiptPolicy = ServiceOperationReceiptPolicy.committed,
        settlement_policy: ServiceOperationSettlementPolicy = ServiceOperationSettlementPolicy.none,
    ) -> ServiceOperationConfig:
        """Creates one operation definition under this ServiceConfig."""

        payload = {
            "name": name,
            "description": description,
            "price_id": price_id,
            "admission_mode": admission_mode,
            "fulfillment_kind": fulfillment_kind,
            "receipt_policy": receipt_policy,
            "settlement_policy": settlement_policy,
        }
        result = await invoke_instance(orm_model=self, function_name="create_service_operation_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_operation_config import ServiceOperationConfig

        if isinstance(value, ServiceOperationConfig):
            return value
        return ServiceOperationConfig.validate_invocation_value(value)

    async def create_service(self, name: str, description: str | None = None) -> Service:
        """Creates one Service instance under this ServiceConfig."""

        payload = {"name": name, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_service", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service import Service

        if isinstance(value, Service):
            return value
        return Service.validate_invocation_value(value)

    async def create_contract_config(
        self,
        name: str,
        default_kind: ServiceContractKind = ServiceContractKind.subscription,
        projection_experience_id: UUID | None = None,
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ServiceContractConfig:
        """
        Creates one reusable contract configuration under this ServiceConfig.

        Contract:
        - ServiceContractConfig declares which operations and roles a kind of contract can grant.
        - Concrete ServiceContract receipts reference this config when activated for a consumer.
        - Commercial profile, subscription, and smart-contract receipts do not own reusable grant semantics.
        """

        payload = {
            "name": name,
            "default_kind": default_kind,
            "projection_experience_id": projection_experience_id,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="create_contract_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_contract_config import ServiceContractConfig

        if isinstance(value, ServiceContractConfig):
            return value
        return ServiceContractConfig.validate_invocation_value(value)

    async def create_api(self, api_id: UUID, description: str | None = None) -> ServiceConfigApi:
        """Creates one shared-API discovery bridge under this ServiceConfig."""

        payload = {"api_id": api_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_api", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_config_api import ServiceConfigApi

        if isinstance(value, ServiceConfigApi):
            return value
        return ServiceConfigApi.validate_invocation_value(value)

    async def create_experience(
        self, projection_experience_id: UUID, description: str | None = None
    ) -> ServiceConfigExperience:
        """Creates one shared-Experience discovery bridge under this ServiceConfig."""

        payload = {"projection_experience_id": projection_experience_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_experience", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_config_experience import ServiceConfigExperience

        if isinstance(value, ServiceConfigExperience):
            return value
        return ServiceConfigExperience.validate_invocation_value(value)

    async def declare_code_package_config(
        self,
        slot_key: str,
        code_package_config_id: UUID,
        cardinality: ServiceConfigCodePackageConfigCardinality = ServiceConfigCodePackageConfigCardinality.many,
        required: bool = False,
        description: str | None = None,
    ) -> ServiceConfigCodePackageConfig:
        """
        Declare one CodePackageConfig slot this ServiceConfig can activate.

        Contract:
        - This is service capability truth, not deployment selection.
        - `slot_key` is service-local vocabulary such as `experience`.
        - CodePackageConfig owns package kind, manifest, materialization, and runtime context truth.
        - Node/deployment profiles later bind concrete CodePackage instances to this slot.
        """

        payload = {
            "slot_key": slot_key,
            "code_package_config_id": code_package_config_id,
            "cardinality": cardinality,
            "required": required,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="declare_code_package_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_config_code_package_config import ServiceConfigCodePackageConfig

        if isinstance(value, ServiceConfigCodePackageConfig):
            return value
        return ServiceConfigCodePackageConfig.validate_invocation_value(value)


class ServiceConfigBuildInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class ServiceConfigBuildOutput(BaseModel):
    value: ServiceConfig


class ServiceConfigCreateServiceOperationConfigInput(BaseModel):
    name: str
    description: str | None = Field(default=None)
    price_id: UUID | None = Field(default=None)
    admission_mode: ServiceOperationAdmissionMode = Field(default=ServiceOperationAdmissionMode.contract_required)
    fulfillment_kind: ServiceOperationFulfillmentKind = Field(default=ServiceOperationFulfillmentKind.coordination)
    receipt_policy: ServiceOperationReceiptPolicy = Field(default=ServiceOperationReceiptPolicy.committed)
    settlement_policy: ServiceOperationSettlementPolicy = Field(default=ServiceOperationSettlementPolicy.none)


class ServiceConfigCreateServiceOperationConfigOutput(BaseModel):
    value: ServiceOperationConfig


class ServiceConfigCreateServiceInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class ServiceConfigCreateServiceOutput(BaseModel):
    value: Service


class ServiceConfigCreateContractConfigInput(BaseModel):
    name: str
    default_kind: ServiceContractKind = Field(default=ServiceContractKind.subscription)
    projection_experience_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ServiceConfigCreateContractConfigOutput(BaseModel):
    value: ServiceContractConfig


class ServiceConfigCreateApiInput(BaseModel):
    api_id: UUID
    description: str | None = Field(default=None)


class ServiceConfigCreateApiOutput(BaseModel):
    value: ServiceConfigApi


class ServiceConfigCreateExperienceInput(BaseModel):
    projection_experience_id: UUID
    description: str | None = Field(default=None)


class ServiceConfigCreateExperienceOutput(BaseModel):
    value: ServiceConfigExperience


class ServiceConfigDeclareCodePackageConfigInput(BaseModel):
    slot_key: str
    code_package_config_id: UUID
    cardinality: ServiceConfigCodePackageConfigCardinality = Field(
        default=ServiceConfigCodePackageConfigCardinality.many
    )
    required: bool = Field(default=False)
    description: str | None = Field(default=None)


class ServiceConfigDeclareCodePackageConfigOutput(BaseModel):
    value: ServiceConfigCodePackageConfig


FUNCTIONS = {
    "ServiceConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates one canonical service capability definition.",
                "is_constructor": True,
            },
            "input": ServiceConfigBuildInput,
            "output": ServiceConfigBuildOutput,
        },
        "create_service_operation_config": {
            "canonical": {
                "name": "create_service_operation_config",
                "description": "Creates one operation definition under this ServiceConfig.",
                "is_constructor": False,
            },
            "input": ServiceConfigCreateServiceOperationConfigInput,
            "output": ServiceConfigCreateServiceOperationConfigOutput,
        },
        "create_service": {
            "canonical": {
                "name": "create_service",
                "description": "Creates one Service instance under this ServiceConfig.",
                "is_constructor": False,
            },
            "input": ServiceConfigCreateServiceInput,
            "output": ServiceConfigCreateServiceOutput,
        },
        "create_contract_config": {
            "canonical": {
                "name": "create_contract_config",
                "description": "Creates one reusable contract configuration under this ServiceConfig.\n\nContract:\n- ServiceContractConfig declares which operations and roles a kind of contract can grant.\n- Concrete ServiceContract receipts reference this config when activated for a consumer.\n- Commercial profile, subscription, and smart-contract receipts do not own reusable grant semantics.",
                "is_constructor": False,
            },
            "input": ServiceConfigCreateContractConfigInput,
            "output": ServiceConfigCreateContractConfigOutput,
        },
        "create_api": {
            "canonical": {
                "name": "create_api",
                "description": "Creates one shared-API discovery bridge under this ServiceConfig.",
                "is_constructor": False,
            },
            "input": ServiceConfigCreateApiInput,
            "output": ServiceConfigCreateApiOutput,
        },
        "create_experience": {
            "canonical": {
                "name": "create_experience",
                "description": "Creates one shared-Experience discovery bridge under this ServiceConfig.",
                "is_constructor": False,
            },
            "input": ServiceConfigCreateExperienceInput,
            "output": ServiceConfigCreateExperienceOutput,
        },
        "declare_code_package_config": {
            "canonical": {
                "name": "declare_code_package_config",
                "description": "Declare one CodePackageConfig slot this ServiceConfig can activate.\n\nContract:\n- This is service capability truth, not deployment selection.\n- `slot_key` is service-local vocabulary such as `experience`.\n- CodePackageConfig owns package kind, manifest, materialization, and runtime context truth.\n- Node/deployment profiles later bind concrete CodePackage instances to this slot.",
                "is_constructor": False,
            },
            "input": ServiceConfigDeclareCodePackageConfigInput,
            "output": ServiceConfigDeclareCodePackageConfigOutput,
        },
    },
}

__all__ = [
    "ServiceConfig",
    "ServiceConfigBuildInput",
    "ServiceConfigBuildOutput",
    "ServiceConfigCreateServiceOperationConfigInput",
    "ServiceConfigCreateServiceOperationConfigOutput",
    "ServiceConfigCreateServiceInput",
    "ServiceConfigCreateServiceOutput",
    "ServiceConfigCreateContractConfigInput",
    "ServiceConfigCreateContractConfigOutput",
    "ServiceConfigCreateApiInput",
    "ServiceConfigCreateApiOutput",
    "ServiceConfigCreateExperienceInput",
    "ServiceConfigCreateExperienceOutput",
    "ServiceConfigDeclareCodePackageConfigInput",
    "ServiceConfigDeclareCodePackageConfigOutput",
    "FUNCTIONS",
]
