from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_graph_capability import ApiGraphCapability
    from aware_api_ontology_dto.api.api_graph_function import ApiGraphFunction
    from aware_api_ontology_dto.api.api_graph_projection import ApiGraphProjection
    from aware_meta_ontology_dto.graph.config.object_config_graph import ObjectConfigGraph


class ApiGraph(BaseModel):
    # Relationships
    object_config_graph: ObjectConfigGraph | None = Field(default=None)
    api_graph_functions: list[ApiGraphFunction] = Field(default_factory=list)
    api_graph_projections: list[ApiGraphProjection] = Field(default_factory=list)
    api_graph_capabilities: list[ApiGraphCapability] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
