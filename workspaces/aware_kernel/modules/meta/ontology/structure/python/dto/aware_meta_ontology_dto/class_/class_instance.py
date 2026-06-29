from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute import Attribute
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.class_.class_instance_attribute import ClassInstanceAttribute
    from aware_meta_ontology_dto.class_.class_instance_change import ClassInstanceChange


class ClassInstance(BaseModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None)
    class_instance_changes: list[ClassInstanceChange] = Field(default_factory=list)

    # Attributes
    source_object_id: UUID = Field(
        description="Stable external object anchor for this projected instance within one OIG worldline."
    )
