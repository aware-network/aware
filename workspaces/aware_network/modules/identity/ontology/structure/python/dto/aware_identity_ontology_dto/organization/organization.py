from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor import Actor
    from aware_identity_ontology_dto.organization.organization_member import OrganizationMember


class Organization(BaseModel):
    # Relationships
    actor: Actor | None = Field(default=None)
    members: list[OrganizationMember] = Field(default_factory=list)
