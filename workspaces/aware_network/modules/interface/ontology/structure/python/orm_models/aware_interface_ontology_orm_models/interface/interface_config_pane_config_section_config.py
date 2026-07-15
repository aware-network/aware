from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_config_section_config import LayoutConfigSectionConfig


class InterfaceConfigPaneConfigSectionConfig(ORMModel):
    # Relationships
    layout_config_section_config: LayoutConfigSectionConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    interface_config_pane_config_id: UUID = Field(
        description="Foreign key for InterfaceConfigPaneConfig.section_mounts"
    )
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for InterfaceConfigPaneConfigSectionConfig.layout_config_section_config"
    )
