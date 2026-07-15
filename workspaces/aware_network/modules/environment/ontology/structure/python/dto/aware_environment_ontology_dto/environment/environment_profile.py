from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology_dto.process.process import Process


class EnvironmentProfile(BaseModel):
    """
    Applied Environment profile under a concrete Environment.
    Contract:
    - Reusable OS topology config lives on EnvironmentProfileConfig.
    - This object is the concrete Environment application of that config.
    - Runtime Process instances live here; ProcessConfig is only the reusable key.
    - Runtime sessions are Environment-owned and resolve profile provenance
    through selected Process/Thread paths.
    """

    # Relationships
    profile_config: EnvironmentProfileConfig | None = Field(default=None)
    processes: list[Process] = Field(default_factory=list)

    # Attributes
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
