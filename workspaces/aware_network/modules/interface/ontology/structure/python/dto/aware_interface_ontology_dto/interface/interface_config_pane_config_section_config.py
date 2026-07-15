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


class InterfaceConfigPaneConfigSectionConfig(BaseModel):
    # Relationships
    layout_config_section_config: LayoutConfigSectionConfig | None = Field(default=None)
