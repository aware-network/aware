from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import CredentialSecretResolverKind
from aware_identity_ontology.credential.credential_secret_material_ref import CredentialSecretMaterialRef

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_credential_secret_material_ref_id


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


# --- AWARE: USER_IMPORTS END


async def create_via_credential_profile(
    credential_profile_id: UUID,
    secret_ref_key: str,
    resolver_kind: CredentialSecretResolverKind,
    secret_name: str,
    locator: str | None = None,
    username_hint: str | None = None,
    material_hint: str | None = None,
    fingerprint_sha256: str | None = None,
    created_at_utc: str | None = None,
    rotated_at_utc: str | None = None,
    metadata: JsonObject | None = None,
) -> CredentialSecretMaterialRef:
    """
    Create one external secret material reference without storing the secret.
    """

    # --- AWARE: LOGIC START create_via_credential_profile
    return CredentialSecretMaterialRef(
        id=stable_credential_secret_material_ref_id(
            credential_profile_id=credential_profile_id,
            secret_ref_key=secret_ref_key,
            resolver_kind=_enum_value(resolver_kind),
        ),
        credential_profile_id=credential_profile_id,
        secret_ref_key=secret_ref_key,
        resolver_kind=resolver_kind,
        secret_name=secret_name,
        locator=locator,
        username_hint=username_hint,
        material_hint=material_hint,
        fingerprint_sha256=fingerprint_sha256,
        created_at_utc=created_at_utc,
        rotated_at_utc=rotated_at_utc,
        metadata=metadata,
    )
    # --- AWARE: LOGIC END create_via_credential_profile
