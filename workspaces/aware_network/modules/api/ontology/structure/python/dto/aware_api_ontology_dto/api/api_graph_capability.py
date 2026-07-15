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
    from aware_api_ontology_dto.api.api_graph_capability_function import ApiGraphCapabilityFunction


class ApiGraphCapability(BaseModel):
    # Relationships
    api_capability: ApiCapability | None = Field(default=None)
    api_graph_capability_functions: list[ApiGraphCapabilityFunction] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
