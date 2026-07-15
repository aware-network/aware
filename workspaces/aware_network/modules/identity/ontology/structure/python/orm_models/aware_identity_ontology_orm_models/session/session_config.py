from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.session.session import Session
    from aware_identity_ontology_orm_models.session.session_config_actor_config import SessionConfigActorConfig


class SessionConfig(ORMModel):
    """
    Identity-owned reusable actor-session policy.
    Contract:
    - SessionConfig is domain-neutral participation vocabulary.
    - Environment, Experience, Attention, and other providers bridge to it
    instead of owning separate actor-session role lifecycles.
    - ActorConfig remains the reusable actor archetype vocabulary.
    - Concrete sessions and member ActorRole evidence stay Identity-owned.
    """

    # Relationships
    actor_configs: list[SessionConfigActorConfig] = Field(default_factory=list)
    sessions: list[Session] = Field(default_factory=list)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
