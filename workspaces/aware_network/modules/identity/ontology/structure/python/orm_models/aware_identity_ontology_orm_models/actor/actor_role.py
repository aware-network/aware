from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.role.role import Role


class ActorRole(ORMModel):
    # Relationships
    role: Role | None = Field(default=None, exclude=True)

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for Actor.actor_roles")
    role_id: UUID = Field(description="Foreign key for ActorRole.role")
