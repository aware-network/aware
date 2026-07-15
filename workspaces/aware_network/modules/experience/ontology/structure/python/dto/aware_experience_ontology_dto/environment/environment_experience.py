from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.environment.environment_experience_profile import EnvironmentExperienceProfile
    from aware_experience_ontology_dto.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )
    from aware_experience_ontology_dto.environment.environment_topology_seed import EnvironmentTopologySeed
    from aware_experience_ontology_dto.session.experience_session import ExperienceSession


class EnvironmentExperience(BaseModel):
    """
    Canonical Experience namespace root.
    Purpose:
    - Own one deterministic `fqn_prefix` namespace for experience packages.
    - Scope Experience profile config keys under this root.
    - Keep Environment Environment topology stable and referential-only.
    """

    # Relationships
    profile_configs: list[EnvironmentExperienceProfileConfig] = Field(default_factory=list)
    profiles: list[EnvironmentExperienceProfile] = Field(default_factory=list)
    sessions: list[ExperienceSession] = Field(default_factory=list)
    topology_seeds: list[EnvironmentTopologySeed] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    fqn_prefix: str
    title: str | None = Field(default=None)
