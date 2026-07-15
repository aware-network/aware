from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.actor.actor_enums import ActorType

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor_config_role_config import ActorConfigRoleConfig


class ActorConfig(BaseModel):
    """
    Identity-owned ActorConfig policy archetype.
    Contract:
    - ActorConfig is reusable admission vocabulary, not Experience-local truth.
    - Environment and Experience consume ActorConfig to describe which actor
    archetypes may enter a scope.
    - Identity owns the RoleConfig bundle and later resolves concrete ActorRole
    truth through admission services.
    """

    # Relationships
    role_configs: list[ActorConfigRoleConfig] = Field(default_factory=list)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    type: ActorType | None = Field(default=None)
