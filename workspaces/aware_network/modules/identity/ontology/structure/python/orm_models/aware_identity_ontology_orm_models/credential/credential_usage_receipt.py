from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.credential.credential_profile_enums import CredentialUsageStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class CredentialUsageReceipt(ORMModel):
    """
    Usage receipt for one credential profile.
    Contract:
    - Records credential use for API calls, publication, deployment, or service
    operations.
    - Stores operation receipts and target refs, never the resolved secret.
    """

    # Attributes
    receipt_key: str
    status: CredentialUsageStatus
    operation: str
    used_at_utc: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    secret_ref_key: str | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)

    # Foreign Keys
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.usage_receipts")
