from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology Dto
from aware_api_ontology_dto.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamMode

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint_stream_event_config import (
        ApiCapabilityEndpointStreamEventConfig,
    )


class ApiCapabilityEndpointStreamConfig(BaseModel):
    """Optional stream contract beneath one request contract."""

    # Relationships
    api_capability_endpoint_stream_event_configs: list[ApiCapabilityEndpointStreamEventConfig] = Field(
        default_factory=list
    )

    # Attributes
    stream_mode: ApiCapabilityEndpointStreamMode
    description: str | None = Field(default=None)
