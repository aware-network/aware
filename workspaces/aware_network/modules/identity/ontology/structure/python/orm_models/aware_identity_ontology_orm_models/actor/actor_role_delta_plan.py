from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor_role import ActorRole
    from aware_identity_ontology_orm_models.role.role_config import RoleConfig


class ActorRoleDeltaPlan(ORMModel):
    # Relationships
    actor_role: ActorRole | None = Field(default=None, exclude=True)
    to_role_config: RoleConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    actor_role_id: UUID = Field(description="Foreign key for ActorRoleDeltaPlan.actor_role")
    to_role_config_id: UUID = Field(description="Foreign key for ActorRoleDeltaPlan.to_role_config")
