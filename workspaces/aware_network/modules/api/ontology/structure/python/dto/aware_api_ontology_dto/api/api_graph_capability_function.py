from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_graph_function import ApiGraphFunction


class ApiGraphCapabilityFunction(BaseModel):
    # Relationships
    api_graph_function: ApiGraphFunction | None = Field(default=None)

    # Attributes
    name: str
    description: str | None = Field(default=None)
