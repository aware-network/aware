from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import CredentialUsageStatus
from aware_identity_ontology.credential.credential_usage_receipt import CredentialUsageReceipt

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_credential_usage_receipt_id


# --- AWARE: USER_IMPORTS END


async def create_via_credential_profile(
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
    """
    Create one credential usage receipt without exposing secret material.
    """

    # --- AWARE: LOGIC START create_via_credential_profile
    return CredentialUsageReceipt(
        id=stable_credential_usage_receipt_id(
            credential_profile_id=credential_profile_id,
            receipt_key=receipt_key,
        ),
        credential_profile_id=credential_profile_id,
        receipt_key=receipt_key,
        status=status,
        operation=operation,
        used_at_utc=used_at_utc,
        target_ref=target_ref,
        secret_ref_key=secret_ref_key,
        request_ref=request_ref,
        receipt=receipt,
        error=error,
    )
    # --- AWARE: LOGIC END create_via_credential_profile
