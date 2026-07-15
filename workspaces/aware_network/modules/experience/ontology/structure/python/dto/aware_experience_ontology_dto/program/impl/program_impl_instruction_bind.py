from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_port import ProgramConfigPort


class ProgramImplInstructionBind(BaseModel):
    """
    Program branch+view context selection step.
    Contract:
    - `program_config_port` selects branch connectivity contract.
    - `view_key` selects representation contract.
    - No stable-id resolution occurs in config; runtime resolves at turn execution.
    """

    # Relationships
    program_config_port: ProgramConfigPort | None = Field(default=None)

    # Attributes
    is_active: bool = Field(default=True)
    view_key: str
