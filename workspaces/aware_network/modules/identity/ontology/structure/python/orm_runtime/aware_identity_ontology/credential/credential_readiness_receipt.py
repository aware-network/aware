from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import (
    CredentialReadinessStatus,
    CredentialSecretResolverKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

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

    @classmethod
    async def create_via_credential_profile(
        cls,
        credential_profile_id: UUID,
        receipt_key: str,
        status: CredentialReadinessStatus,
        checked_at_utc: str | None = None,
        resolver_kind: CredentialSecretResolverKind | None = None,
        secret_ref_key: str | None = None,
        missing_requirements: list[str] = [],
        details: JsonObject | None = None,
        error: str | None = None,
    ) -> CredentialReadinessReceipt:
        """Create one credential readiness receipt without exposing secret material."""

        payload = {
            "credential_profile_id": credential_profile_id,
            "receipt_key": receipt_key,
            "status": status,
            "checked_at_utc": checked_at_utc,
            "resolver_kind": resolver_kind,
            "secret_ref_key": secret_ref_key,
            "missing_requirements": missing_requirements,
            "details": details,
            "error": error,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_credential_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CredentialReadinessReceipt):
            return value
        return CredentialReadinessReceipt.validate_invocation_value(value)


class CredentialReadinessReceiptCreateViaCredentialProfileInput(BaseModel):
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.readiness_receipts")
    receipt_key: str
    status: CredentialReadinessStatus
    checked_at_utc: str | None = Field(default=None)
    resolver_kind: CredentialSecretResolverKind | None = Field(default=None)
    secret_ref_key: str | None = Field(default=None)
    missing_requirements: list[str] = Field(default_factory=list)
    details: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)


class CredentialReadinessReceiptCreateViaCredentialProfileOutput(BaseModel):
    value: CredentialReadinessReceipt


FUNCTIONS = {
    "CredentialReadinessReceipt": {
        "create_via_credential_profile": {
            "canonical": {
                "name": "create_via_credential_profile",
                "description": "Create one credential readiness receipt without exposing secret material.",
                "is_constructor": True,
            },
            "input": CredentialReadinessReceiptCreateViaCredentialProfileInput,
            "output": CredentialReadinessReceiptCreateViaCredentialProfileOutput,
        },
    },
}

__all__ = [
    "CredentialReadinessReceipt",
    "CredentialReadinessReceiptCreateViaCredentialProfileInput",
    "CredentialReadinessReceiptCreateViaCredentialProfileOutput",
    "FUNCTIONS",
]
