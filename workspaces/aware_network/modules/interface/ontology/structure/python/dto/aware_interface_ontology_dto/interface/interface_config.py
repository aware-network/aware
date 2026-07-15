from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.interface import Interface
    from aware_interface_ontology_dto.interface.interface_config_pane_config import InterfaceConfigPaneConfig
    from aware_interface_ontology_dto.interface.interface_config_window_config import InterfaceConfigWindowConfig


class InterfaceConfig(BaseModel):
    # Relationships
    interfaces: list[Interface] = Field(default_factory=list)
    interface_config_window_configs: list[InterfaceConfigWindowConfig] = Field(default_factory=list)
    interface_config_pane_configs: list[InterfaceConfigPaneConfig] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)
