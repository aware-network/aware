from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.window_config_layout_config import WindowConfigLayoutConfig


class WindowConfig(ORMModel):
    # Relationships
    layout_configs: list[WindowConfigLayoutConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    description: str | None = Field(default=None)
