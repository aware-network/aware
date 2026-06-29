from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.class_.class_instance import ClassInstance
    from aware_meta_ontology.class_.class_instance_relationship_identity import ClassInstanceRelationshipIdentity


class ClassInstanceRelationship(ORMModel):
    # Relationships
    class_config_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)
    class_instance_relationship_identity: ClassInstanceRelationshipIdentity | None = Field(default=None)
    source_class_instance: ClassInstance | None = Field(default=None, exclude=True)
    target_class_instance: ClassInstance | None = Field(default=None, exclude=True)

    # Foreign Keys
    object_instance_graph_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraph.class_instance_relationships"
    )
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ClassInstanceRelationship.class_config_relationship"
    )
    class_instance_relationship_identity_id: UUID | None = Field(
        default=None, description="Foreign key for ClassInstanceRelationship.class_instance_relationship_identity"
    )
    source_class_instance_id: UUID = Field(
        description="Foreign key for ClassInstanceRelationship.source_class_instance"
    )
    target_class_instance_id: UUID = Field(
        description="Foreign key for ClassInstanceRelationship.target_class_instance"
    )


FUNCTIONS = {
    "ClassInstanceRelationship": {},
}

__all__ = [
    "ClassInstanceRelationship",
    "FUNCTIONS",
]
