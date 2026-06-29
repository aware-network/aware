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
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint


class SdkOperationApiCapabilityEndpoint(ORMModel):
    """SDK operation to API endpoint bridge."""

    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None)

    # Attributes
    name: str
    endpoint_ref: str | None = Field(default=None)
    discriminant: str | None = Field(default=None)
    role: str = Field(default="primary")
    order: int = Field(default=1)
    required: bool = Field(default=True)

    # Foreign Keys
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.api_capability_endpoints")
    api_capability_endpoint_id: UUID = Field(
        description="Foreign key for SdkOperationApiCapabilityEndpoint.api_capability_endpoint"
    )

    @classmethod
    async def create_via_sdk_operation(
        cls,
        sdk_operation_id: UUID,
        name: str,
        api_capability_endpoint_id: UUID,
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        role: str = "primary",
        order: int = 1,
        required: bool = True,
    ) -> SdkOperationApiCapabilityEndpoint:
        """Create one deterministic SDK operation binding to one API capability endpoint."""

        payload = {
            "sdk_operation_id": sdk_operation_id,
            "name": name,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "endpoint_ref": endpoint_ref,
            "discriminant": discriminant,
            "role": role,
            "order": order,
            "required": required,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_sdk_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkOperationApiCapabilityEndpoint):
            return value
        return SdkOperationApiCapabilityEndpoint.validate_invocation_value(value)


class SdkOperationApiCapabilityEndpointCreateViaSdkOperationInput(BaseModel):
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.api_capability_endpoints")
    name: str
    api_capability_endpoint_id: UUID
    endpoint_ref: str | None = Field(default=None)
    discriminant: str | None = Field(default=None)
    role: str = Field(default="primary")
    order: int = Field(default=1)
    required: bool = Field(default=True)


class SdkOperationApiCapabilityEndpointCreateViaSdkOperationOutput(BaseModel):
    value: SdkOperationApiCapabilityEndpoint


FUNCTIONS = {
    "SdkOperationApiCapabilityEndpoint": {
        "create_via_sdk_operation": {
            "canonical": {
                "name": "create_via_sdk_operation",
                "description": "Create one deterministic SDK operation binding to one API capability endpoint.",
                "is_constructor": True,
            },
            "input": SdkOperationApiCapabilityEndpointCreateViaSdkOperationInput,
            "output": SdkOperationApiCapabilityEndpointCreateViaSdkOperationOutput,
        },
    },
}

__all__ = [
    "SdkOperationApiCapabilityEndpoint",
    "SdkOperationApiCapabilityEndpointCreateViaSdkOperationInput",
    "SdkOperationApiCapabilityEndpointCreateViaSdkOperationOutput",
    "FUNCTIONS",
]
