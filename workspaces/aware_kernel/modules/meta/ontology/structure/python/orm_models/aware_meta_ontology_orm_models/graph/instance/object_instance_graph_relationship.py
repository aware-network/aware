from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_instance import ClassInstance
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph import ObjectInstanceGraph


class ObjectInstanceGraphRelationship(ORMModel):
    """A Relationship between two OIGs with optional related nodes."""

    # Relationships
    target_object_instance_graph: ObjectInstanceGraph | None = Field(default=None, exclude=True)
    source_class_instance: ClassInstance | None = Field(default=None, exclude=True)
    target_class_instance: ClassInstance | None = Field(default=None, exclude=True)

    # Foreign Keys
    object_projection_graph_relationship_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.object_instance_graph_relationships"
    )
    target_object_instance_graph_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphRelationship.target_object_instance_graph"
    )
    source_class_instance_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphRelationship.source_class_instance"
    )
    target_class_instance_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphRelationship.target_class_instance"
    )
