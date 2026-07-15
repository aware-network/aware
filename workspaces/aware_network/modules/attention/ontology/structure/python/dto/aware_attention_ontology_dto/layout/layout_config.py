from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_config_section_config import LayoutConfigSectionConfig


class LayoutConfig(BaseModel):
    """
    Declarative layout configuration for Attention.
    Contract:
    - Config-level topology source for layout token lowering.
    - Not a runtime instance surface.
    """

    # Relationships
    section_configs: list[LayoutConfigSectionConfig] = Field(default_factory=list)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)
