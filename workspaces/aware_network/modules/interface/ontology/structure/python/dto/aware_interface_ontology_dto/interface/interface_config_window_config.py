from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.window_config import WindowConfig


class InterfaceConfigWindowConfig(BaseModel):
    # Relationships
    window_config: WindowConfig | None = Field(default=None)
