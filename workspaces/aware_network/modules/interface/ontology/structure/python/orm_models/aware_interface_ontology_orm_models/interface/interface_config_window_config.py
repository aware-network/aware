from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.window_config import WindowConfig


class InterfaceConfigWindowConfig(ORMModel):
    # Relationships
    window_config: WindowConfig | None = Field(default=None)

    # Foreign Keys
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interface_config_window_configs")
    window_config_id: UUID = Field(description="Foreign key for InterfaceConfigWindowConfig.window_config")
