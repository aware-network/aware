from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.environment.environment_experience_profile import (
        EnvironmentExperienceProfile,
    )
    from aware_experience_ontology_orm_models.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )
    from aware_experience_ontology_orm_models.environment.environment_topology_seed import EnvironmentTopologySeed
    from aware_experience_ontology_orm_models.session.experience_session import ExperienceSession


class EnvironmentExperience(ORMModel):
    """
    Canonical Experience namespace root.
    Purpose:
    - Own one deterministic `fqn_prefix` namespace for experience packages.
    - Scope Experience profile config keys under this root.
    - Keep Environment Environment topology stable and referential-only.
    """

    # Relationships
    profile_configs: list[EnvironmentExperienceProfileConfig] = Field(default_factory=list, exclude=True)
    profiles: list[EnvironmentExperienceProfile] = Field(default_factory=list, exclude=True)
    sessions: list[ExperienceSession] = Field(default_factory=list, exclude=True)
    topology_seeds: list[EnvironmentTopologySeed] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    fqn_prefix: str
    title: str | None = Field(default=None)
