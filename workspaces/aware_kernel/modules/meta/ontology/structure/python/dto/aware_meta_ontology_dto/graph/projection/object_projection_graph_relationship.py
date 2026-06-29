from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_relationship import (
        ObjectInstanceGraphRelationship,
    )
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ObjectProjectionGraphRelationship(BaseModel):
    """A Relationship between two OPGs with optional related nodes."""

    # Relationships
    target_object_projection_graph: ObjectProjectionGraph | None = Field(default=None)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)
    source_object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None)
    target_object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None)
    object_instance_graph_relationships: list[ObjectInstanceGraphRelationship] = Field(default_factory=list)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None, description="Reverse view for ObjectProjectionGraph.object_projection_graph_relationships"
    )
