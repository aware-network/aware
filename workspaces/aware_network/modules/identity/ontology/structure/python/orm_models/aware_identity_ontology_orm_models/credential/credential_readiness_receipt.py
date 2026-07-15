from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.credential.credential_profile_enums import (
    CredentialReadinessStatus,
    CredentialSecretResolverKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class CredentialReadinessReceipt(ORMModel):
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

    # Foreign Keys
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.readiness_receipts")
