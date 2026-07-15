from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout import Layout
    from aware_experience_ontology_orm_models.program.program_config_layout_port_section import (
        ProgramConfigLayoutPortSection,
    )


class ProgramConfigLayout(ORMModel):
    """
    Declarative layout contract under one ProgramConfig.
    Contract:
    - Defines section topology and port placement policies for one program config.
    - Runtime materializes ProgramConfigLayout instances from this config rail.
    """

    # Relationships
    layout: Layout | None = Field(default=None, exclude=True)
    port_sections: list[ProgramConfigLayoutPortSection] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    is_default: bool = Field(default=False)

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.layouts")
    layout_id: UUID = Field(description="Foreign key for ProgramConfigLayout.layout")
