from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_input_config import ProgramConfigInputConfig


class ProgramImplInstructionInput(BaseModel):
    """Program input as instruction"""

    # Relationships
    program_config_input_config: ProgramConfigInputConfig | None = Field(default=None)
