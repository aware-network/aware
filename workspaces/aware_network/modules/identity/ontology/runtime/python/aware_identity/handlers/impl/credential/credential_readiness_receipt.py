from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import (
    CredentialReadinessStatus,
    CredentialSecretResolverKind,
)
from aware_identity_ontology.credential.credential_readiness_receipt import CredentialReadinessReceipt

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_credential_readiness_receipt_id


# --- AWARE: USER_IMPORTS END


async def create_via_credential_profile(
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
    """
    Create one credential readiness receipt without exposing secret material.
    """

    # --- AWARE: LOGIC START create_via_credential_profile
    return CredentialReadinessReceipt(
        id=stable_credential_readiness_receipt_id(
            credential_profile_id=credential_profile_id,
            receipt_key=receipt_key,
        ),
        credential_profile_id=credential_profile_id,
        receipt_key=receipt_key,
        status=status,
        checked_at_utc=checked_at_utc,
        resolver_kind=resolver_kind,
        secret_ref_key=secret_ref_key,
        missing_requirements=list(missing_requirements or []),
        details=details,
        error=error,
    )
    # --- AWARE: LOGIC END create_via_credential_profile
