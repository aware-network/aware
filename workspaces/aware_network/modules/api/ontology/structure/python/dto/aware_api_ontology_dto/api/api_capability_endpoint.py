from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_call import ApiCall
    from aware_api_ontology_dto.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction
    from aware_api_ontology_dto.api.api_capability_endpoint_request_config import ApiCapabilityEndpointRequestConfig


class ApiCapabilityEndpoint(BaseModel):
    """
    Public API caller hit surface.
    Caller-facing truth:
    - the caller hits one endpoint
    - the caller provides payload through this endpoint's request contract DTO `ClassConfig`
    - stage-one `ApiCall` anchors here, not on endpoint-function fulfillment
    This object is ingress contract truth, not graph-call fulfillment truth.
    Endpoint identity stays on the public port rail (`api_capability_id + name`).
    The required request contract is created beneath that one endpoint rail during
    endpoint construction; it is not a second public authoring step.
    """

    # Relationships
    api_calls: list[ApiCall] = Field(default_factory=list)
    request_config: ApiCapabilityEndpointRequestConfig | None = Field(default=None)
    api_capability_endpoint_functions: list[ApiCapabilityEndpointFunction] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)
