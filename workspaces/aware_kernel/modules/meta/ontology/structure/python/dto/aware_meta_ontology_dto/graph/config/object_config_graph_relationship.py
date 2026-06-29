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
    from aware_meta_ontology_dto.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology_dto.graph.config.object_config_graph_relationship_class import (
        ObjectConfigGraphRelationshipClass,
    )


class ObjectConfigGraphRelationship(BaseModel):
    """Entry linking two ObjectConfigGraphs (source → target) and their relationships"""

    # Relationships
    target_object_config_graph: ObjectConfigGraph | None = Field(default=None)
    class_config_relationships: list[ClassConfigRelationship] = Field(default_factory=list)
    object_config_graph_relationship_classes: list[ObjectConfigGraphRelationshipClass] = Field(default_factory=list)
