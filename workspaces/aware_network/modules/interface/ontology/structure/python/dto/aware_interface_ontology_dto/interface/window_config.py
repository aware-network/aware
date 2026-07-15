from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.window_config_layout_config import WindowConfigLayoutConfig


class WindowConfig(BaseModel):
    # Relationships
    layout_configs: list[WindowConfigLayoutConfig] = Field(default_factory=list)

    # Attributes
    key: str
    description: str | None = Field(default=None)
