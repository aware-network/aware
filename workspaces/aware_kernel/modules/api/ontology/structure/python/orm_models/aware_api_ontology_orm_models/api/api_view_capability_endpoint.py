from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability_endpoint import ApiCapabilityEndpoint


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
