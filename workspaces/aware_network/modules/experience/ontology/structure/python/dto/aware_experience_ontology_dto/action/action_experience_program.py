from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config import ProgramConfig


class ActionExperienceProgram(BaseModel):
    # Relationships
    program_config: ProgramConfig | None = Field(default=None)
