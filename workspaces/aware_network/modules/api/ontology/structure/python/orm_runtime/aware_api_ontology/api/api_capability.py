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


class ApiCapability(ORMModel):
    # Relationships
    api_capability_endpoints: list[ApiCapabilityEndpoint] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_id: UUID = Field(description="Foreign key for Api.api_capabilities")

    async def create_endpoint(
        self, name: str, request_class_config_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpoint:
        """Create one external/public endpoint rail under this ApiCapability."""

        payload = {"name": name, "request_class_config_id": request_class_config_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_endpoint", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint

        if isinstance(value, ApiCapabilityEndpoint):
            return value
        return ApiCapabilityEndpoint.validate_invocation_value(value)

    @classmethod
    async def create_via_api(cls, api_id: UUID, name: str, description: str | None = None) -> ApiCapability:
        """Create one named reusable API capability contract under Api."""

        payload = {"api_id": api_id, "name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_api", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCapability):
            return value
        return ApiCapability.validate_invocation_value(value)


class ApiCapabilityCreateEndpointInput(BaseModel):
    name: str
    request_class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityCreateEndpointOutput(BaseModel):
    value: ApiCapabilityEndpoint


class ApiCapabilityCreateViaApiInput(BaseModel):
    api_id: UUID = Field(description="Foreign key for Api.api_capabilities")
    name: str
    description: str | None = Field(default=None)


class ApiCapabilityCreateViaApiOutput(BaseModel):
    value: ApiCapability


FUNCTIONS = {
    "ApiCapability": {
        "create_endpoint": {
            "canonical": {
                "name": "create_endpoint",
                "description": "Create one external/public endpoint rail under this ApiCapability.",
                "is_constructor": False,
            },
            "input": ApiCapabilityCreateEndpointInput,
            "output": ApiCapabilityCreateEndpointOutput,
        },
        "create_via_api": {
            "canonical": {
                "name": "create_via_api",
                "description": "Create one named reusable API capability contract under Api.",
                "is_constructor": True,
            },
            "input": ApiCapabilityCreateViaApiInput,
            "output": ApiCapabilityCreateViaApiOutput,
        },
    },
}

__all__ = [
    "ApiCapability",
    "ApiCapabilityCreateEndpointInput",
    "ApiCapabilityCreateEndpointOutput",
    "ApiCapabilityCreateViaApiInput",
    "ApiCapabilityCreateViaApiOutput",
    "FUNCTIONS",
]
