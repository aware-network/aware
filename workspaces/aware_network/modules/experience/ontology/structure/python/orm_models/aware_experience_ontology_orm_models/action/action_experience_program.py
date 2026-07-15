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


class ActionExperienceProgram(ORMModel):
    # Relationships
    program_config: ProgramConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    action_experience_id: UUID = Field(description="Foreign key for ActionExperience.action_experience_programs")
    program_config_id: UUID = Field(description="Foreign key for ActionExperienceProgram.program_config")
