from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor_config_role_config import ActorConfigRoleConfig
    from aware_identity_ontology_dto.actor.actor_role import ActorRole


class ProgramActorRole(BaseModel):
    """
    Runtime role attribution edge under one ProgramActor.
    Contract:
    - Stores the role snapshot used by runtime invoke attribution.
    - Links role eligibility provenance through Identity ActorConfigRoleConfig.
    """

    # Relationships
    actor_role: ActorRole | None = Field(default=None)
    actor_config_role_config: ActorConfigRoleConfig | None = Field(default=None)
