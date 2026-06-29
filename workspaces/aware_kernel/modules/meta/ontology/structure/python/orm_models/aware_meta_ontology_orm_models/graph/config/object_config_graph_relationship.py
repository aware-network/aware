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
    from aware_meta_ontology_orm_models.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_relationship_class import (
        ObjectConfigGraphRelationshipClass,
    )


class ObjectConfigGraphRelationship(ORMModel):
    """Entry linking two ObjectConfigGraphs (source → target) and their relationships"""

    # Relationships
    target_object_config_graph: ObjectConfigGraph | None = Field(default=None, exclude=True)
    class_config_relationships: list[ClassConfigRelationship] = Field(default_factory=list)
    object_config_graph_relationship_classes: list[ObjectConfigGraphRelationshipClass] = Field(default_factory=list)

    # Foreign Keys
    object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraph.object_config_graph_relationships"
    )
    target_object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphRelationship.target_object_config_graph"
    )
