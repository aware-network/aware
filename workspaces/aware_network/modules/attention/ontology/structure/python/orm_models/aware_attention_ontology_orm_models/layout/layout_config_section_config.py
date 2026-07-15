from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.section.section_config import SectionConfig


class LayoutConfigSectionConfig(ORMModel):
    """Canonical section configuration entry inside a LayoutConfig."""

    # Relationships
    section_config: SectionConfig | None = Field(default=None, exclude=True)

    # Attributes
    section_key: str
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)

    # Foreign Keys
    layout_config_id: UUID = Field(description="Foreign key for LayoutConfig.section_configs")
