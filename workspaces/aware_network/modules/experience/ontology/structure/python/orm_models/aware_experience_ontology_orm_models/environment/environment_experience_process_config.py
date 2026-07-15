from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.process.process_config import ProcessConfig
    from aware_experience_ontology_orm_models.environment.environment_experience_thread_config import (
        EnvironmentExperienceThreadConfig,
    )


class EnvironmentExperienceProcessConfig(ORMModel):
    """
    Experience config bridge for one Environment ProcessConfig.
    Contract:
    - Environment owns the ProcessConfig topology object.
    - Experience owns only the process-level participation config over that
    Environment object.
    - This class never constructs ProcessConfig or runtime Process instances.
    """

    # Relationships
    process_config: ProcessConfig | None = Field(default=None)
    thread_configs: list[EnvironmentExperienceThreadConfig] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    position: int | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.process_configs"
    )
    process_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceProcessConfig.process_config")
