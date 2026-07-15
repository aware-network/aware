from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import (
    CredentialGrantEffect,
    CredentialKind,
    CredentialProfileStatus,
    CredentialReadinessStatus,
    CredentialSecretResolverKind,
    CredentialTargetKind,
    CredentialUsageStatus,
)
from aware_identity_ontology.credential.credential_grant import CredentialGrant
from aware_identity_ontology.credential.credential_profile import CredentialProfile
from aware_identity_ontology.credential.credential_readiness_receipt import CredentialReadinessReceipt
from aware_identity_ontology.credential.credential_secret_material_ref import CredentialSecretMaterialRef
from aware_identity_ontology.credential.credential_usage_receipt import CredentialUsageReceipt

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_credential_profile_id


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


# --- AWARE: USER_IMPORTS END


async def attach_secret_material_ref(
    credential_profile: CredentialProfile,
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
    Attach one external secret material reference to this profile.
    """

    # --- AWARE: LOGIC START attach_secret_material_ref
    if credential_profile.id is None:
        raise ValueError("CredentialProfile.attach_secret_material_ref requires a bound credential_profile.id")
    ref = await CredentialSecretMaterialRef.create_via_credential_profile(
        credential_profile_id=credential_profile.id,
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
    if all(existing.id != ref.id for existing in credential_profile.secret_material_refs):
        credential_profile.secret_material_refs = [
            *credential_profile.secret_material_refs,
            ref,
        ]
    return ref
    # --- AWARE: LOGIC END attach_secret_material_ref


async def grant_scope(
    credential_profile: CredentialProfile,
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
    Attach one canonical scope/capability grant to this profile.
    """

    # --- AWARE: LOGIC START grant_scope
    if credential_profile.id is None:
        raise ValueError("CredentialProfile.grant_scope requires a bound credential_profile.id")
    grant = await CredentialGrant.create_via_credential_profile(
        credential_profile_id=credential_profile.id,
        grant_key=grant_key,
        scope_kind=scope_kind,
        scope_value=scope_value,
        effect=effect,
        operation=operation,
        resource_ref=resource_ref,
        expires_at_utc=expires_at_utc,
        metadata=metadata,
    )
    if all(existing.id != grant.id for existing in credential_profile.grants):
        credential_profile.grants = [*credential_profile.grants, grant]
    return grant
    # --- AWARE: LOGIC END grant_scope


async def record_readiness(
    credential_profile: CredentialProfile,
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
    Attach one resolver/readiness receipt to this profile.
    """

    # --- AWARE: LOGIC START record_readiness
    if credential_profile.id is None:
        raise ValueError("CredentialProfile.record_readiness requires a bound credential_profile.id")
    readiness = await CredentialReadinessReceipt.create_via_credential_profile(
        credential_profile_id=credential_profile.id,
        receipt_key=receipt_key,
        status=status,
        checked_at_utc=checked_at_utc,
        resolver_kind=resolver_kind,
        secret_ref_key=secret_ref_key,
        missing_requirements=list(missing_requirements or []),
        details=details,
        error=error,
    )
    if all(existing.id != readiness.id for existing in credential_profile.readiness_receipts):
        credential_profile.readiness_receipts = [
            *credential_profile.readiness_receipts,
            readiness,
        ]
    return readiness
    # --- AWARE: LOGIC END record_readiness


async def record_usage(
    credential_profile: CredentialProfile,
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
    Attach one credential usage receipt to this profile.
    """

    # --- AWARE: LOGIC START record_usage
    if credential_profile.id is None:
        raise ValueError("CredentialProfile.record_usage requires a bound credential_profile.id")
    usage = await CredentialUsageReceipt.create_via_credential_profile(
        credential_profile_id=credential_profile.id,
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
    if all(existing.id != usage.id for existing in credential_profile.usage_receipts):
        credential_profile.usage_receipts = [
            *credential_profile.usage_receipts,
            usage,
        ]
    return usage
    # --- AWARE: LOGIC END record_usage


async def create_via_identity(
    identity_id: UUID,
    profile_key: str,
    target_kind: CredentialTargetKind = CredentialTargetKind.aware_api,
    credential_kind: CredentialKind = CredentialKind.api_key,
    status: CredentialProfileStatus = CredentialProfileStatus.planned,
    display_name: str | None = None,
    target_name: str | None = None,
    issuer: str | None = None,
    audience: str | None = None,
    external_subject: str | None = None,
    created_at_utc: str | None = None,
    updated_at_utc: str | None = None,
    expires_at_utc: str | None = None,
    revoked_at_utc: str | None = None,
    metadata: JsonObject | None = None,
) -> CredentialProfile:
    """
    Create one credential profile without storing secret material.

    Contract:
    - Parent Identity context is injected by construct propagation.
    - Stable identity is derived from parent Identity plus profile keys.
    - Organization credentials use parent Identity with type=organization.
    """

    # --- AWARE: LOGIC START create_via_identity
    return CredentialProfile(
        id=stable_credential_profile_id(
            identity_id=identity_id,
            profile_key=profile_key,
            target_kind=_enum_value(target_kind),
        ),
        identity_id=identity_id,
        profile_key=profile_key,
        target_kind=target_kind,
        credential_kind=credential_kind,
        status=status,
        display_name=display_name,
        target_name=target_name,
        issuer=issuer,
        audience=audience,
        external_subject=external_subject,
        created_at_utc=created_at_utc,
        updated_at_utc=updated_at_utc,
        expires_at_utc=expires_at_utc,
        revoked_at_utc=revoked_at_utc,
        metadata=metadata,
    )
    # --- AWARE: LOGIC END create_via_identity
