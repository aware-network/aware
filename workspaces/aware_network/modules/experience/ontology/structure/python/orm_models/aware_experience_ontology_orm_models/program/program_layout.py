from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_layout import ProgramConfigLayout
    from aware_experience_ontology_orm_models.program.program_layout_section import ProgramLayoutSection


class ProgramLayout(ORMModel):
    """Runtime materialized layout state for one Program run."""

    # Relationships
    config: ProgramConfigLayout | None = Field(default=None, exclude=True)
    sections: list[ProgramLayoutSection] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    is_active: bool = Field(default=False)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.layouts")
    config_id: UUID | None = Field(default=None, description="Foreign key for ProgramLayout.config")
