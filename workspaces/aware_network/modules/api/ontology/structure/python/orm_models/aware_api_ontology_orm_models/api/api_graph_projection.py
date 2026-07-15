from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph import ObjectProjectionGraph


class ApiGraphProjection(ORMModel):
    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_projections")
    object_projection_graph_id: UUID = Field(description="Foreign key for ApiGraphProjection.object_projection_graph")
