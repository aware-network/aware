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
    from aware_meta_ontology_dto.attribute.attribute_change import AttributeChange
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_dto.attribute.attribute_value import AttributeValue


class Attribute(BaseModel):
    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None)
    attribute_changes: list[AttributeChange] = Field(default_factory=list)
    value_root: AttributeValue = Field(description="Canonical value representation (descriptor-driven value tree).")

    # Attributes
    owner_key: UUID = Field(description="Stable owner anchor for shared contained structural Attribute identity.")
