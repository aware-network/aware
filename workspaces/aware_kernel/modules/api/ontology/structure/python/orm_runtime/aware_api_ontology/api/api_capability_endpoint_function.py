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
    from aware_api_ontology.api.api_graph_capability_function import ApiGraphCapabilityFunction


class ApiCapabilityEndpointFunction(ORMModel):
    """
    downstream fulfillment contract under one endpoint.
    Config-side truth:
    - this is the API-owned agreement for how an endpoint may be fulfilled toward graph callable truth
    - this is not the caller-facing hit surface
    - stage-one `ApiCall` must not anchor here
    Service/runtime fulfills this contract downstream.
    """

    # Relationships
    api_graph_capability_function: ApiGraphCapabilityFunction | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpoint.api_capability_endpoint_functions"
    )
    api_graph_capability_function_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpointFunction.api_graph_capability_function"
    )

    @classmethod
    async def create_via_api_capability_endpoint(
        cls,
        api_capability_endpoint_id: UUID,
        name: str,
        api_graph_capability_function_id: UUID,
        description: str | None = None,
    ) -> ApiCapabilityEndpointFunction:
        """Create one named endpoint-owned binding to one graph-scoped capability function."""

        payload = {
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "name": name,
            "api_graph_capability_function_id": api_graph_capability_function_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_api_capability_endpoint", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCapabilityEndpointFunction):
            return value
        return ApiCapabilityEndpointFunction.validate_invocation_value(value)


class ApiCapabilityEndpointFunctionCreateViaApiCapabilityEndpointInput(BaseModel):
    api_capability_endpoint_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpoint.api_capability_endpoint_functions"
    )
    name: str
    api_graph_capability_function_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointFunctionCreateViaApiCapabilityEndpointOutput(BaseModel):
    value: ApiCapabilityEndpointFunction


FUNCTIONS = {
    "ApiCapabilityEndpointFunction": {
        "create_via_api_capability_endpoint": {
            "canonical": {
                "name": "create_via_api_capability_endpoint",
                "description": "Create one named endpoint-owned binding to one graph-scoped capability function.",
                "is_constructor": True,
            },
            "input": ApiCapabilityEndpointFunctionCreateViaApiCapabilityEndpointInput,
            "output": ApiCapabilityEndpointFunctionCreateViaApiCapabilityEndpointOutput,
        },
    },
}

__all__ = [
    "ApiCapabilityEndpointFunction",
    "ApiCapabilityEndpointFunctionCreateViaApiCapabilityEndpointInput",
    "ApiCapabilityEndpointFunctionCreateViaApiCapabilityEndpointOutput",
    "FUNCTIONS",
]
