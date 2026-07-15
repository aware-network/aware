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
    from aware_identity_ontology_orm_models.actor.actor_config import ActorConfig


class SessionConfigActorConfig(ORMModel):
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

    # Foreign Keys
    session_config_id: UUID = Field(description="Foreign key for SessionConfig.actor_configs")
    actor_config_id: UUID = Field(description="Foreign key for SessionConfigActorConfig.actor_config")
