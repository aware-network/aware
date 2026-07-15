from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.app_config_screen_config import AppConfigScreenConfig


class AppConfig(ORMModel):
    # Relationships
    screen_configs: list[AppConfigScreenConfig] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str
    title: str | None = Field(default=None)
