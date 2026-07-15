from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor import Actor
    from aware_identity_ontology_orm_models.organization.organization_member import OrganizationMember


class Organization(ORMModel):
    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)
    members: list[OrganizationMember] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for Organization.actor")
