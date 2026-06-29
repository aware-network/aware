from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute import Attribute


class InlineValueInstanceAttribute(BaseModel):
    # Relationships
    attribute: Attribute = Field(description="Association target reference to Attribute")
