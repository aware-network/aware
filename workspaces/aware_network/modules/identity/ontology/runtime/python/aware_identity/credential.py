from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
from typing import cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_identity.meta_runtime import IdentityMetaRuntimeLaneBinder
from aware_identity_ontology.credential.credential_profile import CredentialProfile
from aware_identity_ontology.identity.identity import Identity
from aware_identity_ontology.stable_ids import (
    stable_credential_profile_id,
    stable_credential_readiness_receipt_id,
    stable_credential_secret_material_ref_id,
)


@dataclass(frozen=True, slots=True)
class IdentityCredentialOperationContext:
    actor_id: UUID


@dataclass(frozen=True, slots=True)
class IdentityCredentialRuntimeContext:
    lane_binder: IdentityMetaRuntimeLaneBinder


@dataclass(frozen=True, slots=True)
class CredentialProfileSetupRuntimeRequest:
    identity_id: UUID
    profile_key: str
    target_kind: str = "aware_api"
    credential_kind: str = "api_key"
    status: str = "planned"
    display_name: str | None = None
    target_name: str | None = None
    issuer: str | None = None
    audience: str | None = None
    external_subject: str | None = None
    created_at_utc: str | None = None
    updated_at_utc: str | None = None
    expires_at_utc: str | None = None
    metadata: JsonObject | None = None
    secret_ref_key: str = "default"
    resolver_kind: str = "env_var"
    secret_name: str = ""
    locator: str | None = None
    username_hint: str | None = None
    material_hint: str | None = None
    fingerprint_sha256: str | None = None
    secret_created_at_utc: str | None = None
    secret_rotated_at_utc: str | None = None
    secret_metadata: JsonObject | None = None
    request_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CredentialProfileSetupRuntimeReceipt:
    request_id: UUID | None
    identity_id: UUID
    credential_profile_id: UUID
    secret_material_ref_id: UUID
    profile_key: str
    target_kind: str
    secret_ref_key: str
    resolver_kind: str
    secret_name: str
    raw_secret_stored: bool
    info: str


@dataclass(frozen=True, slots=True)
class CredentialReadinessCheckRuntimeRequest:
    identity_id: UUID
    secret_ref_key: str
    credential_profile_id: UUID | None = None
    profile_key: str | None = None
    target_kind: str = "aware_api"
    receipt_key: str | None = None
    resolver_kind: str = "env_var"
    secret_name: str | None = None
    checked_at_utc: str | None = None
    require_non_empty: bool = True
    details: JsonObject | None = None
    request_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CredentialReadinessCheckRuntimeReceipt:
    request_id: UUID | None
    identity_id: UUID
    credential_profile_id: UUID
    readiness_receipt_id: UUID
    profile_key: str | None
    target_kind: str | None
    receipt_key: str
    status: str
    available: bool
    resolver_kind: str
    secret_ref_key: str
    secret_name: str | None
    checked_at_utc: str
    missing_requirements: list[str]
    credential_handle: JsonObject
    raw_secret_returned: bool
    info: str


def resolve_identity_credential_runtime_context(
    *,
    lane_binder: IdentityMetaRuntimeLaneBinder,
) -> IdentityCredentialRuntimeContext:
    return IdentityCredentialRuntimeContext(lane_binder=lane_binder)


async def setup_credential_profile(
    *,
    runtime_context: IdentityCredentialRuntimeContext,
    operation_context: IdentityCredentialOperationContext,
    request: CredentialProfileSetupRuntimeRequest,
) -> CredentialProfileSetupRuntimeReceipt:
    credential_profile_id = stable_credential_profile_id(
        identity_id=request.identity_id,
        profile_key=request.profile_key,
        target_kind=request.target_kind,
    )
    secret_material_ref_id = stable_credential_secret_material_ref_id(
        credential_profile_id=credential_profile_id,
        secret_ref_key=request.secret_ref_key,
        resolver_kind=request.resolver_kind,
    )
    lane = runtime_context.lane_binder.bind(
        projection="Identity",
        branch_id=request.identity_id,
        actor_id=operation_context.actor_id,
    )
    identity = _identity_ref(request.identity_id)
    with lane.activate():
        credential_profile = await identity.create_credential_profile(
            profile_key=request.profile_key,
            target_kind=request.target_kind,
            credential_kind=request.credential_kind,
            status=request.status,
            display_name=request.display_name,
            target_name=request.target_name,
            issuer=request.issuer,
            audience=request.audience,
            external_subject=request.external_subject,
            created_at_utc=request.created_at_utc,
            updated_at_utc=request.updated_at_utc,
            expires_at_utc=request.expires_at_utc,
            metadata=request.metadata,
        )
        await credential_profile.attach_secret_material_ref(
            secret_ref_key=request.secret_ref_key,
            resolver_kind=request.resolver_kind,
            secret_name=request.secret_name,
            locator=request.locator,
            username_hint=request.username_hint,
            material_hint=request.material_hint,
            fingerprint_sha256=request.fingerprint_sha256,
            created_at_utc=request.secret_created_at_utc,
            rotated_at_utc=request.secret_rotated_at_utc,
            metadata=request.secret_metadata,
        )
    if credential_profile.id != credential_profile_id:
        raise ValueError(
            "identity.create_credential_profile returned an unexpected credential "
            + f"profile id: expected={credential_profile_id} actual={credential_profile.id}"
        )
    return CredentialProfileSetupRuntimeReceipt(
        request_id=request.request_id,
        identity_id=request.identity_id,
        credential_profile_id=credential_profile_id,
        secret_material_ref_id=secret_material_ref_id,
        profile_key=request.profile_key,
        target_kind=request.target_kind,
        secret_ref_key=request.secret_ref_key,
        resolver_kind=request.resolver_kind,
        secret_name=request.secret_name,
        raw_secret_stored=False,
        info="identity credential profile setup completed",
    )


async def check_credential_readiness(
    *,
    runtime_context: IdentityCredentialRuntimeContext,
    operation_context: IdentityCredentialOperationContext,
    request: CredentialReadinessCheckRuntimeRequest,
) -> CredentialReadinessCheckRuntimeReceipt:
    credential_profile_id = _resolve_credential_profile_id(request=request)
    receipt_key = request.receipt_key or _default_readiness_receipt_key(
        target_kind=request.target_kind,
        profile_key=request.profile_key,
        secret_ref_key=request.secret_ref_key,
    )
    checked_at_utc = request.checked_at_utc or _utc_now()
    resolution = _resolve_secret_availability(request=request)
    details = _readiness_details(
        request=request,
        resolution=resolution,
    )
    readiness_receipt_id = stable_credential_readiness_receipt_id(
        credential_profile_id=credential_profile_id,
        receipt_key=receipt_key,
    )
    lane = runtime_context.lane_binder.bind(
        projection="Identity",
        branch_id=request.identity_id,
        actor_id=operation_context.actor_id,
    )
    credential_profile = _credential_profile_ref(
        credential_profile_id=credential_profile_id,
        identity_id=request.identity_id,
        profile_key=request.profile_key,
        target_kind=request.target_kind,
    )
    with lane.activate():
        readiness_receipt = await credential_profile.record_readiness(
            receipt_key=receipt_key,
            status=resolution.status,
            checked_at_utc=checked_at_utc,
            resolver_kind=request.resolver_kind,
            secret_ref_key=request.secret_ref_key,
            missing_requirements=resolution.missing_requirements,
            details=details,
            error=resolution.error,
        )
    if readiness_receipt.id != readiness_receipt_id:
        raise ValueError(
            "credential_profile.record_readiness returned an unexpected receipt id: "
            + f"expected={readiness_receipt_id} actual={readiness_receipt.id}"
        )
    return CredentialReadinessCheckRuntimeReceipt(
        request_id=request.request_id,
        identity_id=request.identity_id,
        credential_profile_id=credential_profile_id,
        readiness_receipt_id=readiness_receipt_id,
        profile_key=request.profile_key,
        target_kind=request.target_kind,
        receipt_key=receipt_key,
        status=resolution.status,
        available=resolution.available,
        resolver_kind=request.resolver_kind,
        secret_ref_key=request.secret_ref_key,
        secret_name=request.secret_name,
        checked_at_utc=checked_at_utc,
        missing_requirements=resolution.missing_requirements,
        credential_handle=_credential_handle(
            credential_profile_id=credential_profile_id,
            request=request,
        ),
        raw_secret_returned=False,
        info="identity credential readiness checked",
    )


@dataclass(frozen=True, slots=True)
class _SecretAvailabilityResolution:
    status: str
    available: bool
    missing_requirements: list[str]
    error: str | None = None


def _resolve_credential_profile_id(
    *,
    request: CredentialReadinessCheckRuntimeRequest,
) -> UUID:
    if request.credential_profile_id is not None:
        return request.credential_profile_id
    if not request.profile_key:
        raise ValueError(
            "Credential readiness check requires credential_profile_id or profile_key."
        )
    return stable_credential_profile_id(
        identity_id=request.identity_id,
        profile_key=request.profile_key,
        target_kind=request.target_kind,
    )


def _default_readiness_receipt_key(
    *,
    target_kind: str,
    profile_key: str | None,
    secret_ref_key: str,
) -> str:
    profile_part = profile_key or "credential_profile"
    return f"{target_kind}.{profile_part}.{secret_ref_key}.readiness"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _resolve_secret_availability(
    *,
    request: CredentialReadinessCheckRuntimeRequest,
) -> _SecretAvailabilityResolution:
    resolver_kind = request.resolver_kind.strip()
    if resolver_kind == "no_secret":
        return _SecretAvailabilityResolution(
            status="ready",
            available=True,
            missing_requirements=[],
        )
    if resolver_kind != "env_var":
        return _SecretAvailabilityResolution(
            status="blocked",
            available=False,
            missing_requirements=[f"resolver_kind:{resolver_kind}"],
            error="credential resolver readiness is not supported",
        )
    if not request.secret_name:
        return _SecretAvailabilityResolution(
            status="missing",
            available=False,
            missing_requirements=["secret_name"],
            error="env_var credential readiness requires secret_name",
        )
    if request.secret_name not in os.environ:
        return _SecretAvailabilityResolution(
            status="missing",
            available=False,
            missing_requirements=[request.secret_name],
        )
    if request.require_non_empty and os.environ.get(request.secret_name) == "":
        return _SecretAvailabilityResolution(
            status="missing",
            available=False,
            missing_requirements=[request.secret_name],
            error="env_var credential is empty",
        )
    return _SecretAvailabilityResolution(
        status="ready",
        available=True,
        missing_requirements=[],
    )


def _readiness_details(
    *,
    request: CredentialReadinessCheckRuntimeRequest,
    resolution: _SecretAvailabilityResolution,
) -> JsonObject:
    details: dict[str, object] = dict(request.details or {})
    details.update(
        {
            "resolver_kind": request.resolver_kind,
            "secret_ref_key": request.secret_ref_key,
            "secret_name": request.secret_name,
            "available": resolution.available,
            "raw_secret_returned": False,
        }
    )
    return cast(JsonObject, details)


def _credential_handle(
    *,
    credential_profile_id: UUID,
    request: CredentialReadinessCheckRuntimeRequest,
) -> JsonObject:
    return cast(
        JsonObject,
        {
            "identity_id": str(request.identity_id),
            "credential_profile_id": str(credential_profile_id),
            "resolver_kind": request.resolver_kind,
            "secret_ref_key": request.secret_ref_key,
            "secret_name": request.secret_name,
        },
    )


def _identity_ref(identity_id: UUID) -> Identity:
    return Identity.model_construct(id=identity_id)


def _credential_profile_ref(
    *,
    credential_profile_id: UUID,
    identity_id: UUID,
    profile_key: str | None,
    target_kind: str,
) -> CredentialProfile:
    return CredentialProfile.model_construct(
        id=credential_profile_id,
        identity_id=identity_id,
        profile_key=profile_key or "",
        target_kind=target_kind,
    )
