from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class CredentialProfileSetupRequest(BaseModel):
    """
    Public DTOs for Identity-owned credential profile setup.
    Contract:
    - Credential profiles belong to Identity; organizations are Identity records.
    - Secret material is never carried in these DTOs.
    - Secret values live in external resolvers and are referenced only by metadata.
    """

    # Attributes
    identity_id: UUID
    profile_key: str
    target_kind: str = Field(default="aware_api")
    credential_kind: str = Field(default="api_key")
    status: str = Field(default="planned")
    display_name: str | None = Field(default=None)
    target_name: str | None = Field(default=None)
    issuer: str | None = Field(default=None)
    audience: str | None = Field(default=None)
    external_subject: str | None = Field(default=None)
    created_at_utc: str | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)
    expires_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)
    secret_ref_key: str
    resolver_kind: str = Field(default="env_var")
    secret_name: str
    locator: str | None = Field(default=None)
    username_hint: str | None = Field(default=None)
    material_hint: str | None = Field(default=None)
    fingerprint_sha256: str | None = Field(default=None)
    secret_created_at_utc: str | None = Field(default=None)
    secret_rotated_at_utc: str | None = Field(default=None)
    secret_metadata: JsonObject | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    source: str | None = Field(default=None)


class CredentialProfileSetupReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    identity_id: UUID
    credential_profile_id: UUID
    secret_material_ref_id: UUID
    profile_key: str
    target_kind: str
    secret_ref_key: str
    resolver_kind: str
    secret_name: str
    raw_secret_stored: bool = Field(default=False)
    info: str | None = Field(default=None)


class CredentialReadinessCheckRequest(BaseModel):
    # Attributes
    identity_id: UUID
    credential_profile_id: UUID | None = Field(default=None)
    profile_key: str | None = Field(default=None)
    target_kind: str = Field(default="aware_api")
    receipt_key: str | None = Field(default=None)
    resolver_kind: str = Field(default="env_var")
    secret_ref_key: str
    secret_name: str | None = Field(default=None)
    checked_at_utc: str | None = Field(default=None)
    require_non_empty: bool = Field(default=True)
    details: JsonObject | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    source: str | None = Field(default=None)


class CredentialReadinessCheckReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    identity_id: UUID
    credential_profile_id: UUID
    readiness_receipt_id: UUID
    profile_key: str | None = Field(default=None)
    target_kind: str | None = Field(default=None)
    receipt_key: str
    status: str
    available: bool = Field(default=False)
    resolver_kind: str
    secret_ref_key: str
    secret_name: str | None = Field(default=None)
    checked_at_utc: str | None = Field(default=None)
    missing_requirements: list[str] = Field(default_factory=list)
    credential_handle: JsonObject | None = Field(default=None)
    raw_secret_returned: bool = Field(default=False)
    info: str | None = Field(default=None)
