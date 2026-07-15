from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph import ObjectProjectionGraph


class ObjectProjectionGraphEdge(ORMModel):
    # Relationships
    class_config_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None, exclude=True, description="Reverse view for ObjectProjectionGraph.object_projection_graph_edges"
    )

    # Attributes
    attribute_role: ObjectProjectionGraphAttributeRole = Field(default=ObjectProjectionGraphAttributeRole.reference)
    depth_limit: int | None = Field(default=None)
    include: ObjectProjectionGraphEdgeInclude = Field(default=ObjectProjectionGraphEdgeInclude.required)
    loading_override: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    multiplicity: ObjectProjectionGraphEdgeMultiplicity = Field(default=ObjectProjectionGraphEdgeMultiplicity.many)
    traversal_direction: ClassConfigRelationshipDirection = Field(default=ClassConfigRelationshipDirection.forward)

    # Foreign Keys
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_edges"
    )
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphEdge.class_config_relationship"
    )
