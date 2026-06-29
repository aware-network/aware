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
    from aware_meta_ontology_dto.attribute.attribute_value_change import AttributeValueChange


class AttributeChange(BaseModel):
    # Relationships
    change: Change
    value_root_change: AttributeValueChange | None = Field(
        default=None, description="Canonical descriptor-driven value tree change (root node)."
    )
