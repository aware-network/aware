from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_constructor import (
        ObjectProjectionGraphConstructor,
    )
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_edge import ObjectProjectionGraphEdge
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_relationship import (
        ObjectProjectionGraphRelationship,
    )


class ObjectProjectionGraph(BaseModel):
    # Relationships
    object_projection_graph_edges: list[ObjectProjectionGraphEdge] = Field(
        default_factory=list, description="Canonical membership edges declared under this projection graph."
    )
    object_projection_graph_nodes: list[ObjectProjectionGraphNode] = Field(default_factory=list)
    object_projection_graph_constructors: list[ObjectProjectionGraphConstructor] = Field(default_factory=list)
    object_projection_graph_relationships: list[ObjectProjectionGraphRelationship] = Field(default_factory=list)
    object_instance_graphs: list[ObjectInstanceGraph] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    language: CodeLanguage
    name: str
    projection_hash: str
    supports_virtual_build: bool = Field(default=True)
