from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )
    from aware_experience_ontology_dto.environment.environment_topology_process_seed import (
        EnvironmentTopologyProcessSeed,
    )


class EnvironmentTopologySeed(BaseModel):
    """
    Experience-owned runtime topology seed.
    Purpose:
    - Keep reusable Environment topology config separate from concrete runtime topology.
    - Provide named genesis/entrypoint recipes that can be selected explicitly.
    """

    # Relationships
    environment_experience_profile_config: EnvironmentExperienceProfileConfig | None = Field(default=None)
    process_seeds: list[EnvironmentTopologyProcessSeed] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    title: str | None = Field(default=None)
