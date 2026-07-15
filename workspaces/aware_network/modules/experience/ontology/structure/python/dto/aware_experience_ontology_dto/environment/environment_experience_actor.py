from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor_config import ActorConfig


class EnvironmentExperienceActorConfig(BaseModel):
    # Relationships
    actor_config: ActorConfig | None = Field(default=None)
