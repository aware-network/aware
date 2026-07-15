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


class ApiViewCapabilityEndpoint(ORMModel):
    """
    Endpoint-backed callable surface exposed by one API view.
    Contract:
    - `ApiView` owns readable view-state.
    - `ApiCapabilityEndpoint` owns service-callable ingress.
    - This object exposes one endpoint once beneath one view; `action_key` is
    dispatch metadata, not identity.
    - Endpointless API view actions are intentionally not modeled.
    """

    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint

    # Attributes
    action_key: str
    endpoint_ref: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_view_id: UUID = Field(description="Foreign key for ApiView.capability_endpoints")
    api_capability_endpoint_id: UUID | None = Field(
        default=None, description="Foreign key for ApiViewCapabilityEndpoint.api_capability_endpoint"
    )

    @classmethod
    async def build_via_api_view(
        cls,
        api_view_id: UUID,
        action_key: str,
        api_capability_endpoint_id: UUID,
        endpoint_ref: str,
        description: str | None = None,
    ) -> ApiViewCapabilityEndpoint:
        """
        Create one deterministic endpoint-backed action binding beneath ApiView.

        Contract:
        - Identity is scoped by parent `ApiView` and `api_capability_endpoint`.
        - `action_key` is the stable dispatch key exposed to Experience/Interface
          consumers and must not be used to duplicate the same endpoint.
        """

        payload = {
            "api_view_id": api_view_id,
            "action_key": action_key,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "endpoint_ref": endpoint_ref,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_api_view", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiViewCapabilityEndpoint):
            return value
        return ApiViewCapabilityEndpoint.validate_invocation_value(value)


class ApiViewCapabilityEndpointBuildViaApiViewInput(BaseModel):
    api_view_id: UUID = Field(description="Foreign key for ApiView.capability_endpoints")
    action_key: str
    api_capability_endpoint_id: UUID
    endpoint_ref: str
    description: str | None = Field(default=None)


class ApiViewCapabilityEndpointBuildViaApiViewOutput(BaseModel):
    value: ApiViewCapabilityEndpoint


FUNCTIONS = {
    "ApiViewCapabilityEndpoint": {
        "build_via_api_view": {
            "canonical": {
                "name": "build_via_api_view",
                "description": "Create one deterministic endpoint-backed action binding beneath ApiView.\n\nContract:\n- Identity is scoped by parent `ApiView` and `api_capability_endpoint`.\n- `action_key` is the stable dispatch key exposed to Experience/Interface\n  consumers and must not be used to duplicate the same endpoint.",
                "is_constructor": True,
            },
            "input": ApiViewCapabilityEndpointBuildViaApiViewInput,
            "output": ApiViewCapabilityEndpointBuildViaApiViewOutput,
        },
    },
}

__all__ = [
    "ApiViewCapabilityEndpoint",
    "ApiViewCapabilityEndpointBuildViaApiViewInput",
    "ApiViewCapabilityEndpointBuildViaApiViewOutput",
    "FUNCTIONS",
]
