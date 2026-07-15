from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.credential.credential_profile_enums import (
    CredentialReadinessStatus,
    CredentialSecretResolverKind,
)

# Types
from aware_types import JsonObject


class CredentialReadinessReceipt(BaseModel):
    """
    Readiness check result for one credential profile.
    Contract:
    - Records whether a resolver can locate usable material.
    - Does not include the secret value or one-time token text.
    """

    # Attributes
    receipt_key: str
    status: CredentialReadinessStatus
    checked_at_utc: str | None = Field(default=None)
    resolver_kind: CredentialSecretResolverKind | None = Field(default=None)
    secret_ref_key: str | None = Field(default=None)
    missing_requirements: list[str] = Field(default_factory=list)
    details: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)
