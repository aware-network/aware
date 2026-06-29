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
    from aware_meta_ontology_dto.class_.class_instance import ClassInstance
    from aware_meta_ontology_dto.class_.class_instance_relationship_identity import ClassInstanceRelationshipIdentity


class ClassInstanceRelationship(BaseModel):
    # Relationships
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)
    class_instance_relationship_identity: ClassInstanceRelationshipIdentity | None = Field(default=None)
    source_class_instance: ClassInstance | None = Field(default=None)
    target_class_instance: ClassInstance | None = Field(default=None)
