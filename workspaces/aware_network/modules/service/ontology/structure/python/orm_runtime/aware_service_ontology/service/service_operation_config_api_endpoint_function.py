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
    from aware_api_ontology.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction


class ServiceOperationConfigApiEndpointFunction(ORMModel):
    # Relationships
    api_capability_endpoint_function: ApiCapabilityEndpointFunction | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_operation_config_api_endpoint_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpoint.endpoint_functions"
    )
    api_capability_endpoint_function_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpointFunction.api_capability_endpoint_function"
    )

    @classmethod
    async def build_via_service_operation_config_api_endpoint(
        cls,
        service_operation_config_api_endpoint_id: UUID,
        api_capability_endpoint_function_id: UUID,
        description: str | None = None,
    ) -> ServiceOperationConfigApiEndpointFunction:
        """
        Create one config-level binding from a ServiceOperationConfigApiEndpoint to one API-owned endpoint
        function.
        """

        payload = {
            "service_operation_config_api_endpoint_id": service_operation_config_api_endpoint_id,
            "api_capability_endpoint_function_id": api_capability_endpoint_function_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_operation_config_api_endpoint", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceOperationConfigApiEndpointFunction):
            return value
        return ServiceOperationConfigApiEndpointFunction.validate_invocation_value(value)


class ServiceOperationConfigApiEndpointFunctionBuildViaServiceOperationConfigApiEndpointInput(BaseModel):
    service_operation_config_api_endpoint_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpoint.endpoint_functions"
    )
    api_capability_endpoint_function_id: UUID
    description: str | None = Field(default=None)


class ServiceOperationConfigApiEndpointFunctionBuildViaServiceOperationConfigApiEndpointOutput(BaseModel):
    value: ServiceOperationConfigApiEndpointFunction


FUNCTIONS = {
    "ServiceOperationConfigApiEndpointFunction": {
        "build_via_service_operation_config_api_endpoint": {
            "canonical": {
                "name": "build_via_service_operation_config_api_endpoint",
                "description": "Create one config-level binding from a ServiceOperationConfigApiEndpoint to one API-owned endpoint function.",
                "is_constructor": True,
            },
            "input": ServiceOperationConfigApiEndpointFunctionBuildViaServiceOperationConfigApiEndpointInput,
            "output": ServiceOperationConfigApiEndpointFunctionBuildViaServiceOperationConfigApiEndpointOutput,
        },
    },
}

__all__ = [
    "ServiceOperationConfigApiEndpointFunction",
    "ServiceOperationConfigApiEndpointFunctionBuildViaServiceOperationConfigApiEndpointInput",
    "ServiceOperationConfigApiEndpointFunctionBuildViaServiceOperationConfigApiEndpointOutput",
    "FUNCTIONS",
]
