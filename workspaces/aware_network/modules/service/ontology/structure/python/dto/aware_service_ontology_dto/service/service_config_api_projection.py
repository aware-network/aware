from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_graph_projection import ApiGraphProjection


class ServiceConfigApiProjection(BaseModel):
    # Relationships
    api_graph_projection: ApiGraphProjection | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
