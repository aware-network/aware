from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor_role import ActorRole
    from aware_identity_ontology_dto.role.role_config import RoleConfig


class ActorRoleDeltaPlan(BaseModel):
    # Relationships
    actor_role: ActorRole | None = Field(default=None)
    to_role_config: RoleConfig | None = Field(default=None)
