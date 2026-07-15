from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )
    from aware_experience_ontology_orm_models.environment.environment_topology_process_seed import (
        EnvironmentTopologyProcessSeed,
    )


class EnvironmentTopologySeed(ORMModel):
    """
    Experience-owned runtime topology seed.
    Purpose:
    - Keep reusable Environment topology config separate from concrete runtime topology.
    - Provide named genesis/entrypoint recipes that can be selected explicitly.
    """

    # Relationships
    environment_experience_profile_config: EnvironmentExperienceProfileConfig | None = Field(default=None, exclude=True)
    process_seeds: list[EnvironmentTopologyProcessSeed] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.topology_seeds")
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentTopologySeed.environment_experience_profile_config"
    )
