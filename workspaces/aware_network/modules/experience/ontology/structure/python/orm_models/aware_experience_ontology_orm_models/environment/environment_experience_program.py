from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config import ProgramConfig


class EnvironmentExperienceProgram(ORMModel):
    """
    Canonical installed program contract for an EnvironmentExperienceThreadConfig.
    Purpose:
    - Declare which ProgramConfig contracts are available under one experience
    thread config bridge.
    - Keep install/availability separate from later seed/apply execution declarations.
    """

    # Relationships
    program_config: ProgramConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_thread_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceThreadConfig.programs"
    )
    program_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceProgram.program_config")
