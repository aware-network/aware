from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.app_config_screen_config import AppConfigScreenConfig


class AppConfig(BaseModel):
    # Relationships
    screen_configs: list[AppConfigScreenConfig] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str
    title: str | None = Field(default=None)
