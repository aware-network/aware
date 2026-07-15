from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology_orm_models.process.process import Process


class EnvironmentProfile(ORMModel):
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

    # Foreign Keys
    environment_id: UUID = Field(description="Foreign key for Environment.profiles")
    profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfile.profile_config")
