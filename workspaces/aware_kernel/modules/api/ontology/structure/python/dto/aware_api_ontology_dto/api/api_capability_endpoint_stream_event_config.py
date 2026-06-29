from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology Dto
from aware_api_ontology_dto.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamEventKind

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class ApiCapabilityEndpointStreamEventConfig(BaseModel):
    """Typed event contract beneath one endpoint stream contract."""

    # Relationships
    class_config: ClassConfig | None = Field(default=None)

    # Attributes
    kind: ApiCapabilityEndpointStreamEventKind
    description: str | None = Field(default=None)
