from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.process.process_config import ProcessConfig
    from aware_experience_ontology_dto.environment.environment_experience_thread_config import (
        EnvironmentExperienceThreadConfig,
    )


class EnvironmentExperienceProcessConfig(BaseModel):
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
