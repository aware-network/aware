from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class SectionConfig(ORMModel):
    """
    Declarative section configuration for Attention.
    Contract:
    - Config-level section source for layout token lowering.
    - Not a runtime instance surface.
    """

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)

    # Foreign Keys
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for LayoutConfigSectionConfig.section_config"
    )
