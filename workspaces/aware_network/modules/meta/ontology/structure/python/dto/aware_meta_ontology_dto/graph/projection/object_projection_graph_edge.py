from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology_dto.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph


class ObjectProjectionGraphEdge(BaseModel):
    # Relationships
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None, description="Reverse view for ObjectProjectionGraph.object_projection_graph_edges"
    )

    # Attributes
    attribute_role: ObjectProjectionGraphAttributeRole = Field(default=ObjectProjectionGraphAttributeRole.reference)
    depth_limit: int | None = Field(default=None)
    include: ObjectProjectionGraphEdgeInclude = Field(default=ObjectProjectionGraphEdgeInclude.required)
    loading_override: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    multiplicity: ObjectProjectionGraphEdgeMultiplicity = Field(default=ObjectProjectionGraphEdgeMultiplicity.many)
    traversal_direction: ClassConfigRelationshipDirection = Field(default=ClassConfigRelationshipDirection.forward)
