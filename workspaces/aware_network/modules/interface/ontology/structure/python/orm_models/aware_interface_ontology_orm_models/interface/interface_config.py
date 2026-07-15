from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.interface import Interface
    from aware_interface_ontology_orm_models.interface.interface_config_pane_config import InterfaceConfigPaneConfig
    from aware_interface_ontology_orm_models.interface.interface_config_window_config import InterfaceConfigWindowConfig


class InterfaceConfig(ORMModel):
    # Relationships
    interfaces: list[Interface] = Field(default_factory=list, exclude=True)
    interface_config_window_configs: list[InterfaceConfigWindowConfig] = Field(default_factory=list, exclude=True)
    interface_config_pane_configs: list[InterfaceConfigPaneConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)
