from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph


class ApiGraphProjection(BaseModel):
    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
