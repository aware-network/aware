from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_layout import ProgramConfigLayout
    from aware_experience_ontology_dto.program.program_layout_section import ProgramLayoutSection


class ProgramLayout(BaseModel):
    """Runtime materialized layout state for one Program run."""

    # Relationships
    config: ProgramConfigLayout | None = Field(default=None)
    sections: list[ProgramLayoutSection] = Field(default_factory=list)

    # Attributes
    key: str
    is_active: bool = Field(default=False)
