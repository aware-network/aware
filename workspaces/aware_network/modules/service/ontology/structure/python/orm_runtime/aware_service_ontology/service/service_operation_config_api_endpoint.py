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
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_service_ontology.service.service_config_api import ServiceConfigApi
    from aware_service_ontology.service.service_operation_config_api_endpoint_function import (
        ServiceOperationConfigApiEndpointFunction,
    )


class ServiceOperationConfigApiEndpoint(ORMModel):
    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None, exclude=True)
    endpoint_functions: list[ServiceOperationConfigApiEndpointFunction] = Field(default_factory=list, exclude=True)
    service_config_api: ServiceConfigApi | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperationConfig.api_endpoints")
    api_capability_endpoint_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpoint.api_capability_endpoint"
    )
    service_config_api_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpoint.service_config_api"
    )

    async def create_function(
        self, api_capability_endpoint_function_id: UUID, description: str | None = None
    ) -> ServiceOperationConfigApiEndpointFunction:
        """Create one Service-owned bind to one API-owned endpoint function behind this endpoint facade."""

        payload = {
            "api_capability_endpoint_function_id": api_capability_endpoint_function_id,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="create_function", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_operation_config_api_endpoint_function import (
            ServiceOperationConfigApiEndpointFunction,
        )

        if isinstance(value, ServiceOperationConfigApiEndpointFunction):
            return value
        return ServiceOperationConfigApiEndpointFunction.validate_invocation_value(value)

    @classmethod
    async def build_via_service_operation_config(
        cls,
        service_operation_config_id: UUID,
        service_config_api_id: UUID,
        api_capability_endpoint_id: UUID,
        description: str | None = None,
    ) -> ServiceOperationConfigApiEndpoint:
        """Create one config-level binding from one public API endpoint facade to a ServiceOperationConfig."""

        payload = {
            "service_operation_config_id": service_operation_config_id,
            "service_config_api_id": service_config_api_id,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_operation_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceOperationConfigApiEndpoint):
            return value
        return ServiceOperationConfigApiEndpoint.validate_invocation_value(value)


class ServiceOperationConfigApiEndpointCreateFunctionInput(BaseModel):
    api_capability_endpoint_function_id: UUID
    description: str | None = Field(default=None)


class ServiceOperationConfigApiEndpointCreateFunctionOutput(BaseModel):
    value: ServiceOperationConfigApiEndpointFunction


class ServiceOperationConfigApiEndpointBuildViaServiceOperationConfigInput(BaseModel):
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperationConfig.api_endpoints")
    service_config_api_id: UUID
    api_capability_endpoint_id: UUID
    description: str | None = Field(default=None)


class ServiceOperationConfigApiEndpointBuildViaServiceOperationConfigOutput(BaseModel):
    value: ServiceOperationConfigApiEndpoint


FUNCTIONS = {
    "ServiceOperationConfigApiEndpoint": {
        "create_function": {
            "canonical": {
                "name": "create_function",
                "description": "Create one Service-owned bind to one API-owned endpoint function behind this endpoint facade.",
                "is_constructor": False,
            },
            "input": ServiceOperationConfigApiEndpointCreateFunctionInput,
            "output": ServiceOperationConfigApiEndpointCreateFunctionOutput,
        },
        "build_via_service_operation_config": {
            "canonical": {
                "name": "build_via_service_operation_config",
                "description": "Create one config-level binding from one public API endpoint facade to a ServiceOperationConfig.",
                "is_constructor": True,
            },
            "input": ServiceOperationConfigApiEndpointBuildViaServiceOperationConfigInput,
            "output": ServiceOperationConfigApiEndpointBuildViaServiceOperationConfigOutput,
        },
    },
}

__all__ = [
    "ServiceOperationConfigApiEndpoint",
    "ServiceOperationConfigApiEndpointCreateFunctionInput",
    "ServiceOperationConfigApiEndpointCreateFunctionOutput",
    "ServiceOperationConfigApiEndpointBuildViaServiceOperationConfigInput",
    "ServiceOperationConfigApiEndpointBuildViaServiceOperationConfigOutput",
    "FUNCTIONS",
]
