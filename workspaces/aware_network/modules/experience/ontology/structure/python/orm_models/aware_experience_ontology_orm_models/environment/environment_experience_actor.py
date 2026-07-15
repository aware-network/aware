from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor_config import ActorConfig


class EnvironmentExperienceActorConfig(ORMModel):
    # Relationships
    actor_config: ActorConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.actors"
    )
    actor_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceActorConfig.actor_config")
