from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology.change.change import Change
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.class_.class_instance import ClassInstance


class ClassInstanceRelationshipChange(ORMModel):
    # Relationships
    change: Change
    class_config_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)
    source_class_instance: ClassInstance | None = Field(default=None, exclude=True)
    target_class_instance: ClassInstance | None = Field(default=None, exclude=True)

    # Foreign Keys
    change_id: UUID | None = Field(default=None, description="Foreign key for ClassInstanceRelationshipChange.change")
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ClassInstanceRelationshipChange.class_config_relationship"
    )
    source_class_instance_id: UUID = Field(
        description="Foreign key for ClassInstanceRelationshipChange.source_class_instance"
    )
    target_class_instance_id: UUID = Field(
        description="Foreign key for ClassInstanceRelationshipChange.target_class_instance"
    )


FUNCTIONS = {
    "ClassInstanceRelationshipChange": {},
}

__all__ = [
    "ClassInstanceRelationshipChange",
    "FUNCTIONS",
]
