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
    from aware_api_ontology.api.api_view import ApiView
    from aware_api_ontology.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_sdk_ontology.sdk.sdk_operation_api_capability_endpoint import SdkOperationApiCapabilityEndpoint


class SdkOperationApiViewCapabilityEndpoint(ORMModel):
    """
    SDK operation to API view endpoint bridge.
    This binds an SDK operation endpoint to the API-owned view action that exposes
    it. The API remains the source of endpoint and action-key truth.
    """

    # Relationships
    sdk_operation_api_capability_endpoint: SdkOperationApiCapabilityEndpoint | None = Field(default=None)
    api_view: ApiView | None = Field(default=None)
    api_view_capability_endpoint: ApiViewCapabilityEndpoint | None = Field(default=None)

    # Attributes
    api_view_ref: str
    action_key: str
    endpoint_ref: str

    # Foreign Keys
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.api_view_capability_endpoints")
    sdk_operation_api_capability_endpoint_id: UUID = Field(
        description="Foreign key for SdkOperationApiViewCapabilityEndpoint.sdk_operation_api_capability_endpoint"
    )
    api_view_id: UUID = Field(description="Foreign key for SdkOperationApiViewCapabilityEndpoint.api_view")
    api_view_capability_endpoint_id: UUID = Field(
        description="Foreign key for SdkOperationApiViewCapabilityEndpoint.api_view_capability_endpoint"
    )

    @classmethod
    async def create_via_sdk_operation(
        cls,
        sdk_operation_id: UUID,
        sdk_operation_api_capability_endpoint_id: UUID,
        api_view_id: UUID,
        api_view_capability_endpoint_id: UUID,
        api_view_ref: str,
        action_key: str,
        endpoint_ref: str,
    ) -> SdkOperationApiViewCapabilityEndpoint:
        """
        Create one deterministic SDK operation binding to one API view endpoint.

        Contract:
        - `sdk_operation_api_capability_endpoint_id` points at the SDK-owned
          operation endpoint row.
        - `api_view_capability_endpoint_id` points at API-owned view action
          truth.
        - `api_view_ref`, `action_key`, and `endpoint_ref` are copied from API
          view capability endpoint resolution for runtime consumers.
        """

        payload = {
            "sdk_operation_id": sdk_operation_id,
            "sdk_operation_api_capability_endpoint_id": sdk_operation_api_capability_endpoint_id,
            "api_view_id": api_view_id,
            "api_view_capability_endpoint_id": api_view_capability_endpoint_id,
            "api_view_ref": api_view_ref,
            "action_key": action_key,
            "endpoint_ref": endpoint_ref,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_sdk_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkOperationApiViewCapabilityEndpoint):
            return value
        return SdkOperationApiViewCapabilityEndpoint.validate_invocation_value(value)


class SdkOperationApiViewCapabilityEndpointCreateViaSdkOperationInput(BaseModel):
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.api_view_capability_endpoints")
    sdk_operation_api_capability_endpoint_id: UUID
    api_view_id: UUID
    api_view_capability_endpoint_id: UUID
    api_view_ref: str
    action_key: str
    endpoint_ref: str


class SdkOperationApiViewCapabilityEndpointCreateViaSdkOperationOutput(BaseModel):
    value: SdkOperationApiViewCapabilityEndpoint


FUNCTIONS = {
    "SdkOperationApiViewCapabilityEndpoint": {
        "create_via_sdk_operation": {
            "canonical": {
                "name": "create_via_sdk_operation",
                "description": "Create one deterministic SDK operation binding to one API view endpoint.\n\nContract:\n- `sdk_operation_api_capability_endpoint_id` points at the SDK-owned\n  operation endpoint row.\n- `api_view_capability_endpoint_id` points at API-owned view action\n  truth.\n- `api_view_ref`, `action_key`, and `endpoint_ref` are copied from API\n  view capability endpoint resolution for runtime consumers.",
                "is_constructor": True,
            },
            "input": SdkOperationApiViewCapabilityEndpointCreateViaSdkOperationInput,
            "output": SdkOperationApiViewCapabilityEndpointCreateViaSdkOperationOutput,
        },
    },
}

__all__ = [
    "SdkOperationApiViewCapabilityEndpoint",
    "SdkOperationApiViewCapabilityEndpointCreateViaSdkOperationInput",
    "SdkOperationApiViewCapabilityEndpointCreateViaSdkOperationOutput",
    "FUNCTIONS",
]
