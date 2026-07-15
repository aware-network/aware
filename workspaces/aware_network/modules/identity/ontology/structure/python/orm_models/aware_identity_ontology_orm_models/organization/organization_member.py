from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.organization.organization_enums import OrganizationMemberRole

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.identity.identity import Identity


class OrganizationMember(ORMModel):
    # Relationships
    identity: Identity | None = Field(default=None, exclude=True)

    # Attributes
    role: OrganizationMemberRole

    # Foreign Keys
    organization_id: UUID = Field(description="Foreign key for Organization.members")
    identity_id: UUID = Field(description="Foreign key for OrganizationMember.identity")
