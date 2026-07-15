from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_relationship import (
        ObjectInstanceGraphRelationship,
    )
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ObjectProjectionGraphRelationship(ORMModel):
    """A Relationship between two OPGs with optional related nodes."""

    # Relationships
    target_object_projection_graph: ObjectProjectionGraph | None = Field(default=None, exclude=True)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)
    source_object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None, exclude=True)
    target_object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None, exclude=True)
    object_instance_graph_relationships: list[ObjectInstanceGraphRelationship] = Field(
        default_factory=list, exclude=True
    )
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None,
        exclude=True,
        description="Reverse view for ObjectProjectionGraph.object_projection_graph_relationships",
    )

    # Foreign Keys
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_relationships"
    )
    target_object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.target_object_projection_graph"
    )
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.class_config_relationship"
    )
    source_object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.source_object_projection_graph_node"
    )
    target_object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.target_object_projection_graph_node"
    )
