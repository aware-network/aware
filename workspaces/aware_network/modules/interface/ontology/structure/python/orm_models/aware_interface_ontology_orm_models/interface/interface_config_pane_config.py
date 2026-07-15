from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.interface_config_pane_config_section_config import (
        InterfaceConfigPaneConfigSectionConfig,
    )
    from aware_interface_ontology_orm_models.interface.pane_config import PaneConfig


class InterfaceConfigPaneConfig(ORMModel):
    # Relationships
    pane_config: PaneConfig | None = Field(default=None)
    section_mounts: list[InterfaceConfigPaneConfigSectionConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    narrative_key: str | None = Field(default=None)

    # Foreign Keys
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interface_config_pane_configs")
    pane_config_id: UUID = Field(description="Foreign key for InterfaceConfigPaneConfig.pane_config")
