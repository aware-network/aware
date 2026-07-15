from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import CredentialUsageStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

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

    @classmethod
    async def create_via_credential_profile(
        cls,
        credential_profile_id: UUID,
        receipt_key: str,
        status: CredentialUsageStatus,
        operation: str,
        used_at_utc: str | None = None,
        target_ref: str | None = None,
        secret_ref_key: str | None = None,
        request_ref: str | None = None,
        receipt: JsonObject | None = None,
        error: str | None = None,
    ) -> CredentialUsageReceipt:
        """Create one credential usage receipt without exposing secret material."""

        payload = {
            "credential_profile_id": credential_profile_id,
            "receipt_key": receipt_key,
            "status": status,
            "operation": operation,
            "used_at_utc": used_at_utc,
            "target_ref": target_ref,
            "secret_ref_key": secret_ref_key,
            "request_ref": request_ref,
            "receipt": receipt,
            "error": error,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_credential_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CredentialUsageReceipt):
            return value
        return CredentialUsageReceipt.validate_invocation_value(value)


class CredentialUsageReceiptCreateViaCredentialProfileInput(BaseModel):
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.usage_receipts")
    receipt_key: str
    status: CredentialUsageStatus
    operation: str
    used_at_utc: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    secret_ref_key: str | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)


class CredentialUsageReceiptCreateViaCredentialProfileOutput(BaseModel):
    value: CredentialUsageReceipt


FUNCTIONS = {
    "CredentialUsageReceipt": {
        "create_via_credential_profile": {
            "canonical": {
                "name": "create_via_credential_profile",
                "description": "Create one credential usage receipt without exposing secret material.",
                "is_constructor": True,
            },
            "input": CredentialUsageReceiptCreateViaCredentialProfileInput,
            "output": CredentialUsageReceiptCreateViaCredentialProfileOutput,
        },
    },
}

__all__ = [
    "CredentialUsageReceipt",
    "CredentialUsageReceiptCreateViaCredentialProfileInput",
    "CredentialUsageReceiptCreateViaCredentialProfileOutput",
    "FUNCTIONS",
]
