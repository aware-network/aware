from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.interface_config_pane_config_section_config import (
        InterfaceConfigPaneConfigSectionConfig,
    )
    from aware_interface_ontology_dto.interface.pane_config import PaneConfig


class InterfaceConfigPaneConfig(BaseModel):
    # Relationships
    pane_config: PaneConfig | None = Field(default=None)
    section_mounts: list[InterfaceConfigPaneConfigSectionConfig] = Field(default_factory=list)

    # Attributes
    narrative_key: str | None = Field(default=None)
