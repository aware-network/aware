from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint_response_config import ApiCapabilityEndpointResponseConfig
    from aware_api_ontology_dto.api.api_capability_endpoint_stream_config import ApiCapabilityEndpointStreamConfig
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class ApiCapabilityEndpointRequestConfig(BaseModel):
    """
    Required request contract under one endpoint.
    Caller-facing contract truth:
    - owns the endpoint request DTO `ClassConfig`
    - may own one terminal response contract
    - may own one stream contract
    """

    # Relationships
    class_config: ClassConfig | None = Field(default=None)
    response_config: ApiCapabilityEndpointResponseConfig | None = Field(default=None)
    stream_config: ApiCapabilityEndpointStreamConfig | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
