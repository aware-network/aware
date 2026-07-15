from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.credential.credential_profile_enums import CredentialGrantEffect

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class CredentialGrant(ORMModel):
    """
    Capability/scope granted to one credential profile.
    Contract:
    - Grants describe what a credential may be used for.
    - Enforcement happens at service/API boundaries; this object is canonical
    policy metadata and audit context.
    """

    # Attributes
    grant_key: str
    effect: CredentialGrantEffect = Field(default=CredentialGrantEffect.allow)
    scope_kind: str
    scope_value: str
    operation: str | None = Field(default=None)
    resource_ref: str | None = Field(default=None)
    expires_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)

    # Foreign Keys
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.grants")
