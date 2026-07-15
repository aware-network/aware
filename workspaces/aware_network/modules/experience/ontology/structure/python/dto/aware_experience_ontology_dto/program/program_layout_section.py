from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_branch import ProgramBranch
    from aware_experience_ontology_dto.program.program_config_layout_port_section import ProgramConfigLayoutPortSection


class ProgramLayoutSection(BaseModel):
    """
    Runtime section state under one ProgramWindowLayout.
    Contract:
    - Stores current branch/view targeting for one visible section.
    - No reverse ProgramWindowLayout reference is declared in this child class.
    """

    # Relationships
    port_section: ProgramConfigLayoutPortSection | None = Field(default=None)
    program_branch: ProgramBranch | None = Field(default=None)

    # Attributes
    key: str
    order: int = Field(default=0)
    is_visible: bool = Field(default=True)
    flex: float | None = Field(default=None)
    is_active: bool = Field(default=False)
    view_key: str | None = Field(default=None)
