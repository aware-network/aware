from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_history_ontology_dto.change.change import Change
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_dto.class_.class_instance import ClassInstance


class ClassInstanceRelationshipChange(BaseModel):
    # Relationships
    change: Change
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)
    source_class_instance: ClassInstance | None = Field(default=None)
    target_class_instance: ClassInstance | None = Field(default=None)
