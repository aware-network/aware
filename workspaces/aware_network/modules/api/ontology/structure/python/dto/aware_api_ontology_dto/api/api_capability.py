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


class ApiCapability(BaseModel):
    # Relationships
    api_capability_endpoints: list[ApiCapabilityEndpoint] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)
