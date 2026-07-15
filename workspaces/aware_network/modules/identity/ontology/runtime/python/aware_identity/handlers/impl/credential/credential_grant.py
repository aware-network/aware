from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import CredentialGrantEffect
from aware_identity_ontology.credential.credential_grant import CredentialGrant

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_credential_grant_id


# --- AWARE: USER_IMPORTS END


async def create_via_credential_profile(
    credential_profile_id: UUID,
    grant_key: str,
    scope_kind: str,
    scope_value: str,
    effect: CredentialGrantEffect = CredentialGrantEffect.allow,
    operation: str | None = None,
    resource_ref: str | None = None,
    expires_at_utc: str | None = None,
    metadata: JsonObject | None = None,
) -> CredentialGrant:
    """
    Create one deterministic credential grant under a CredentialProfile.
    """

    # --- AWARE: LOGIC START create_via_credential_profile
    return CredentialGrant(
        id=stable_credential_grant_id(
            credential_profile_id=credential_profile_id,
            grant_key=grant_key,
            scope_kind=scope_kind,
            scope_value=scope_value,
        ),
        credential_profile_id=credential_profile_id,
        grant_key=grant_key,
        scope_kind=scope_kind,
        scope_value=scope_value,
        effect=effect,
        operation=operation,
        resource_ref=resource_ref,
        expires_at_utc=expires_at_utc,
        metadata=metadata,
    )
    # --- AWARE: LOGIC END create_via_credential_profile
