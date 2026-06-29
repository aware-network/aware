from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability import ApiCapability
    from aware_api_ontology_dto.api.api_graph import ApiGraph


class Api(BaseModel):
    # Relationships
    api_graphs: list[ApiGraph] = Field(default_factory=list)
    api_capabilities: list[ApiCapability] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)
