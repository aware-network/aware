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


class EnvironmentExperienceProgram(BaseModel):
    """
    Canonical installed program contract for an EnvironmentExperienceThreadConfig.
    Purpose:
    - Declare which ProgramConfig contracts are available under one experience
    thread config bridge.
    - Keep install/availability separate from later seed/apply execution declarations.
    """

    # Relationships
    program_config: ProgramConfig | None = Field(default=None)
