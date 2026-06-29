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
    from aware_meta_ontology_dto.attribute.attribute_change import AttributeChange


class ClassInstanceChange(BaseModel):
    # Relationships
    attribute_changes: list[AttributeChange] = Field(default_factory=list)
    change: Change
