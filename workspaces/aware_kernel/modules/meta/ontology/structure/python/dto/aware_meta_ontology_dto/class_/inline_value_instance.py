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
    from aware_meta_ontology_dto.class_.inline_value_instance_attribute import InlineValueInstanceAttribute


class InlineValueInstance(BaseModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None)

    # Attributes
    owner_key: UUID = Field(
        description="Stable owner anchor for this value-world instance within one enclosing payload tree."
    )
