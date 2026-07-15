from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_graph_capability import ApiGraphCapability
    from aware_api_ontology_orm_models.api.api_graph_function import ApiGraphFunction
    from aware_api_ontology_orm_models.api.api_graph_projection import ApiGraphProjection
    from aware_meta_ontology_orm_models.graph.config.object_config_graph import ObjectConfigGraph


class ApiGraph(ORMModel):
    # Relationships
    object_config_graph: ObjectConfigGraph | None = Field(default=None, exclude=True)
    api_graph_functions: list[ApiGraphFunction] = Field(default_factory=list, exclude=True)
    api_graph_projections: list[ApiGraphProjection] = Field(default_factory=list, exclude=True)
    api_graph_capabilities: list[ApiGraphCapability] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_id: UUID = Field(description="Foreign key for Api.api_graphs")
    object_config_graph_id: UUID = Field(description="Foreign key for ApiGraph.object_config_graph")
