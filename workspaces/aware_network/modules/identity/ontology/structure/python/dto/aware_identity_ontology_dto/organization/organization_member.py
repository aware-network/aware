from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.organization.organization_enums import OrganizationMemberRole

if TYPE_CHECKING:
    from aware_identity_ontology_dto.identity.identity import Identity


class OrganizationMember(BaseModel):
    # Relationships
    identity: Identity | None = Field(default=None)

    # Attributes
    role: OrganizationMemberRole
