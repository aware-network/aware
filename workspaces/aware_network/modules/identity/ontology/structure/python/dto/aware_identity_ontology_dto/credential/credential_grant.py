from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.credential.credential_profile_enums import CredentialGrantEffect

# Types
from aware_types import JsonObject


class CredentialGrant(BaseModel):
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
