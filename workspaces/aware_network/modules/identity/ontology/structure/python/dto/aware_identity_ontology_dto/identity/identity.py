from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.identity.identity_enums import IdentityType

if TYPE_CHECKING:
    from aware_identity_ontology_dto.credential.credential_profile import CredentialProfile
    from aware_identity_ontology_dto.human.human import Human
    from aware_identity_ontology_dto.identity.identity_pattern import IdentityPattern
    from aware_identity_ontology_dto.identity.identity_profile import IdentityProfile
    from aware_identity_ontology_dto.organization.organization import Organization


class Identity(BaseModel):
    # Relationships
    human: Human | None = Field(default=None)
    organization: Organization | None = Field(default=None)
    identity_patterns: list[IdentityPattern] = Field(default_factory=list)
    identity_profile: IdentityProfile | None = Field(default=None)
    credential_profiles: list[CredentialProfile] = Field(default_factory=list)

    # Attributes
    public_key: str
    type: IdentityType
