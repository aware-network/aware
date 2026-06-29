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


class SdkOperationApiCapabilityEndpoint(BaseModel):
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
