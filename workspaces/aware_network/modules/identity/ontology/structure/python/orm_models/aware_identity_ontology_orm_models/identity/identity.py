from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.identity.identity_enums import IdentityType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.credential.credential_profile import CredentialProfile
    from aware_identity_ontology_orm_models.human.human import Human
    from aware_identity_ontology_orm_models.identity.identity_pattern import IdentityPattern
    from aware_identity_ontology_orm_models.identity.identity_profile import IdentityProfile
    from aware_identity_ontology_orm_models.organization.organization import Organization


class Identity(ORMModel):
    # Relationships
    human: Human | None = Field(default=None, exclude=True)
    organization: Organization | None = Field(default=None, exclude=True)
    identity_patterns: list[IdentityPattern] = Field(default_factory=list, exclude=True)
    identity_profile: IdentityProfile | None = Field(default=None, exclude=True)
    credential_profiles: list[CredentialProfile] = Field(default_factory=list, exclude=True)

    # Attributes
    public_key: str
    type: IdentityType

    # Foreign Keys
    human_id: UUID | None = Field(default=None, description="Foreign key for Identity.human")
    organization_id: UUID | None = Field(default=None, description="Foreign key for Identity.organization")
    identity_profile_id: UUID | None = Field(default=None, description="Foreign key for Identity.identity_profile")
