from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction


class ServiceOperationConfigApiEndpointFunction(BaseModel):
    # Relationships
    api_capability_endpoint_function: ApiCapabilityEndpointFunction | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
