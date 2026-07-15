from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_graph_capability_function import ApiGraphCapabilityFunction


class ApiCapabilityEndpointFunction(BaseModel):
    """
    downstream fulfillment contract under one endpoint.
    Config-side truth:
    - this is the API-owned agreement for how an endpoint may be fulfilled toward graph callable truth
    - this is not the caller-facing hit surface
    - stage-one `ApiCall` must not anchor here
    Service/runtime fulfills this contract downstream.
    """

    # Relationships
    api_graph_capability_function: ApiGraphCapabilityFunction | None = Field(default=None)

    # Attributes
    name: str
    description: str | None = Field(default=None)
