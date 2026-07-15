from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint import ApiCapabilityEndpoint


class ApiViewCapabilityEndpoint(BaseModel):
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
