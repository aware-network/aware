from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_config_section_config import LayoutConfigSectionConfig


class LayoutConfig(ORMModel):
    """
    Declarative layout configuration for Attention.
    Contract:
    - Config-level topology source for layout token lowering.
    - Not a runtime instance surface.
    """

    # Relationships
    section_configs: list[LayoutConfigSectionConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)
