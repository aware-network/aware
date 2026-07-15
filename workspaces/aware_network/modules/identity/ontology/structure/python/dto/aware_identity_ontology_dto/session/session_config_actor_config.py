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
    from aware_identity_ontology_dto.actor.actor_config import ActorConfig


class SessionConfigActorConfig(BaseModel):
    """
    ActorConfig participation policy edge under a SessionConfig.
    Contract:
    - Parent constructor is SessionConfig.
    - Points to Identity ActorConfig vocabulary.
    - Does not grant access or create a concrete member.
    """

    # Relationships
    actor_config: ActorConfig | None = Field(default=None)

    # Attributes
    status: str = Field(default="active")
    purpose: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
