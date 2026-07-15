from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_constructor import (
        ObjectProjectionGraphConstructor,
    )
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_edge import ObjectProjectionGraphEdge
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_relationship import (
        ObjectProjectionGraphRelationship,
    )


class ObjectProjectionGraph(ORMModel):
    # Relationships
    object_projection_graph_edges: list[ObjectProjectionGraphEdge] = Field(
        default_factory=list, description="Canonical membership edges declared under this projection graph."
    )
    object_projection_graph_nodes: list[ObjectProjectionGraphNode] = Field(default_factory=list)
    object_projection_graph_constructors: list[ObjectProjectionGraphConstructor] = Field(default_factory=list)
    object_projection_graph_relationships: list[ObjectProjectionGraphRelationship] = Field(default_factory=list)
    object_instance_graphs: list[ObjectInstanceGraph] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    language: CodeLanguage
    name: str
    projection_hash: str
    supports_virtual_build: bool = Field(default=True)

    # Foreign Keys
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_projection_graphs")
