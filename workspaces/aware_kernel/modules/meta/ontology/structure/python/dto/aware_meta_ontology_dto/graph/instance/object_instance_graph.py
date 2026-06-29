from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_instance import ClassInstance
    from aware_meta_ontology_dto.class_.class_instance_relationship import ClassInstanceRelationship


class ObjectInstanceGraph(BaseModel):
    # Relationships
    root_class_instance: ClassInstance
    class_instances: list[ClassInstance] = Field(default_factory=list)
    class_instance_relationships: list[ClassInstanceRelationship] = Field(default_factory=list)

    # Attributes
    key: str
    name: str
    description: str | None = Field(default=None)
    hash: str
