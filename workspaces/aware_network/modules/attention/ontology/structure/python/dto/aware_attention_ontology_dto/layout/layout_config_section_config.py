from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.section.section_config import SectionConfig


class LayoutConfigSectionConfig(BaseModel):
    """Canonical section configuration entry inside a LayoutConfig."""

    # Relationships
    section_config: SectionConfig | None = Field(default=None)

    # Attributes
    section_key: str
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)
