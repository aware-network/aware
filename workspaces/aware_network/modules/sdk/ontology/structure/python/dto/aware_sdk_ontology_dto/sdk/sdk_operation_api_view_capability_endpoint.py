from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_view import ApiView
    from aware_api_ontology_dto.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_sdk_ontology_dto.sdk.sdk_operation_api_capability_endpoint import SdkOperationApiCapabilityEndpoint


class SdkOperationApiViewCapabilityEndpoint(BaseModel):
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
