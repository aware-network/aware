from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig


class AttributeConfigOverlay(BaseModel):
    """Per-language overrides for AttributeConfig entities."""

    # Relationships
    attribute_config: AttributeConfig | None = Field(
        default=None, description="Association target reference to AttributeConfig"
    )

    # Attributes
    rendered_name: str | None = Field(default=None)
    wire_name: str | None = Field(default=None)
