from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.thread.thread_config import ThreadConfig
    from aware_experience_ontology_orm_models.environment.environment_experience_program import (
        EnvironmentExperienceProgram,
    )
    from aware_experience_ontology_orm_models.environment.environment_experience_program_apply import (
        EnvironmentExperienceProgramApply,
    )


class EnvironmentExperienceThreadConfig(ORMModel):
    """
    Experience config bridge for one Environment ThreadConfig.
    Contract:
    - Environment owns ThreadConfig topology and hosted projection/layout
    availability.
    - Experience owns thread-scoped programs, program apply declarations, and
    later action/event participation over that stable ThreadConfig.
    - This class never constructs ThreadConfig or runtime Thread instances.
    """

    # Relationships
    thread_config: ThreadConfig | None = Field(default=None)
    programs: list[EnvironmentExperienceProgram] = Field(default_factory=list)
    program_applies: list[EnvironmentExperienceProgramApply] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    position: int | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_process_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProcessConfig.thread_configs"
    )
    thread_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceThreadConfig.thread_config")
