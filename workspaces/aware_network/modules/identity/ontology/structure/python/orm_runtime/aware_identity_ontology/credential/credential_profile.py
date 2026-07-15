from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

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

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.credential.credential_grant import CredentialGrant
    from aware_identity_ontology.credential.credential_readiness_receipt import CredentialReadinessReceipt
    from aware_identity_ontology.credential.credential_secret_material_ref import CredentialSecretMaterialRef
    from aware_identity_ontology.credential.credential_usage_receipt import CredentialUsageReceipt


class CredentialProfile(ORMModel):
    """
    Identity-owned credential authority for API keys, publish credentials, and
    external auth rails.
    Contract:
    - This is the public credential/API key model for Identity.
    - Secret material is represented only through CredentialSecretMaterialRef.
    - A profile is contained by Identity; organizations are Identity instances.
    - Parent identity context is propagated by construct traversal.
    """

    # Relationships
    secret_material_refs: list[CredentialSecretMaterialRef] = Field(default_factory=list, exclude=True)
    grants: list[CredentialGrant] = Field(default_factory=list, exclude=True)
    readiness_receipts: list[CredentialReadinessReceipt] = Field(default_factory=list, exclude=True)
    usage_receipts: list[CredentialUsageReceipt] = Field(default_factory=list, exclude=True)

    # Attributes
    profile_key: str
    target_kind: CredentialTargetKind = Field(default=CredentialTargetKind.aware_api)
    credential_kind: CredentialKind = Field(default=CredentialKind.api_key)
    status: CredentialProfileStatus = Field(default=CredentialProfileStatus.planned)
    display_name: str | None = Field(default=None)
    target_name: str | None = Field(default=None)
    issuer: str | None = Field(default=None)
    audience: str | None = Field(default=None)
    external_subject: str | None = Field(default=None)
    created_at_utc: str | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)
    expires_at_utc: str | None = Field(default=None)
    revoked_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)

    # Foreign Keys
    identity_id: UUID = Field(description="Foreign key for Identity.credential_profiles")

    async def attach_secret_material_ref(
        self,
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
        """Attach one external secret material reference to this profile."""

        payload = {
            "secret_ref_key": secret_ref_key,
            "resolver_kind": resolver_kind,
            "secret_name": secret_name,
            "locator": locator,
            "username_hint": username_hint,
            "material_hint": material_hint,
            "fingerprint_sha256": fingerprint_sha256,
            "created_at_utc": created_at_utc,
            "rotated_at_utc": rotated_at_utc,
            "metadata": metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_secret_material_ref", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.credential.credential_secret_material_ref import CredentialSecretMaterialRef

        if isinstance(value, CredentialSecretMaterialRef):
            return value
        return CredentialSecretMaterialRef.validate_invocation_value(value)

    async def grant_scope(
        self,
        grant_key: str,
        scope_kind: str,
        scope_value: str,
        effect: CredentialGrantEffect = CredentialGrantEffect.allow,
        operation: str | None = None,
        resource_ref: str | None = None,
        expires_at_utc: str | None = None,
        metadata: JsonObject | None = None,
    ) -> CredentialGrant:
        """Attach one canonical scope/capability grant to this profile."""

        payload = {
            "grant_key": grant_key,
            "scope_kind": scope_kind,
            "scope_value": scope_value,
            "effect": effect,
            "operation": operation,
            "resource_ref": resource_ref,
            "expires_at_utc": expires_at_utc,
            "metadata": metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="grant_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.credential.credential_grant import CredentialGrant

        if isinstance(value, CredentialGrant):
            return value
        return CredentialGrant.validate_invocation_value(value)

    async def record_readiness(
        self,
        receipt_key: str,
        status: CredentialReadinessStatus,
        checked_at_utc: str | None = None,
        resolver_kind: CredentialSecretResolverKind | None = None,
        secret_ref_key: str | None = None,
        missing_requirements: list[str] = [],
        details: JsonObject | None = None,
        error: str | None = None,
    ) -> CredentialReadinessReceipt:
        """Attach one resolver/readiness receipt to this profile."""

        payload = {
            "receipt_key": receipt_key,
            "status": status,
            "checked_at_utc": checked_at_utc,
            "resolver_kind": resolver_kind,
            "secret_ref_key": secret_ref_key,
            "missing_requirements": missing_requirements,
            "details": details,
            "error": error,
        }
        result = await invoke_instance(orm_model=self, function_name="record_readiness", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.credential.credential_readiness_receipt import CredentialReadinessReceipt

        if isinstance(value, CredentialReadinessReceipt):
            return value
        return CredentialReadinessReceipt.validate_invocation_value(value)

    async def record_usage(
        self,
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
        """Attach one credential usage receipt to this profile."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="record_usage", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.credential.credential_usage_receipt import CredentialUsageReceipt

        if isinstance(value, CredentialUsageReceipt):
            return value
        return CredentialUsageReceipt.validate_invocation_value(value)

    @classmethod
    async def create_via_identity(
        cls,
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

        payload = {
            "identity_id": identity_id,
            "profile_key": profile_key,
            "target_kind": target_kind,
            "credential_kind": credential_kind,
            "status": status,
            "display_name": display_name,
            "target_name": target_name,
            "issuer": issuer,
            "audience": audience,
            "external_subject": external_subject,
            "created_at_utc": created_at_utc,
            "updated_at_utc": updated_at_utc,
            "expires_at_utc": expires_at_utc,
            "revoked_at_utc": revoked_at_utc,
            "metadata": metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_identity", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CredentialProfile):
            return value
        return CredentialProfile.validate_invocation_value(value)


class CredentialProfileAttachSecretMaterialRefInput(BaseModel):
    secret_ref_key: str
    resolver_kind: CredentialSecretResolverKind
    secret_name: str
    locator: str | None = Field(default=None)
    username_hint: str | None = Field(default=None)
    material_hint: str | None = Field(default=None)
    fingerprint_sha256: str | None = Field(default=None)
    created_at_utc: str | None = Field(default=None)
    rotated_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CredentialProfileAttachSecretMaterialRefOutput(BaseModel):
    value: CredentialSecretMaterialRef


class CredentialProfileGrantScopeInput(BaseModel):
    grant_key: str
    scope_kind: str
    scope_value: str
    effect: CredentialGrantEffect = Field(default=CredentialGrantEffect.allow)
    operation: str | None = Field(default=None)
    resource_ref: str | None = Field(default=None)
    expires_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CredentialProfileGrantScopeOutput(BaseModel):
    value: CredentialGrant


class CredentialProfileRecordReadinessInput(BaseModel):
    receipt_key: str
    status: CredentialReadinessStatus
    checked_at_utc: str | None = Field(default=None)
    resolver_kind: CredentialSecretResolverKind | None = Field(default=None)
    secret_ref_key: str | None = Field(default=None)
    missing_requirements: list[str] = Field(default_factory=list)
    details: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)


class CredentialProfileRecordReadinessOutput(BaseModel):
    value: CredentialReadinessReceipt


class CredentialProfileRecordUsageInput(BaseModel):
    receipt_key: str
    status: CredentialUsageStatus
    operation: str
    used_at_utc: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    secret_ref_key: str | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)


class CredentialProfileRecordUsageOutput(BaseModel):
    value: CredentialUsageReceipt


class CredentialProfileCreateViaIdentityInput(BaseModel):
    identity_id: UUID = Field(description="Foreign key for Identity.credential_profiles")
    profile_key: str
    target_kind: CredentialTargetKind = Field(default=CredentialTargetKind.aware_api)
    credential_kind: CredentialKind = Field(default=CredentialKind.api_key)
    status: CredentialProfileStatus = Field(default=CredentialProfileStatus.planned)
    display_name: str | None = Field(default=None)
    target_name: str | None = Field(default=None)
    issuer: str | None = Field(default=None)
    audience: str | None = Field(default=None)
    external_subject: str | None = Field(default=None)
    created_at_utc: str | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)
    expires_at_utc: str | None = Field(default=None)
    revoked_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CredentialProfileCreateViaIdentityOutput(BaseModel):
    value: CredentialProfile


FUNCTIONS = {
    "CredentialProfile": {
        "attach_secret_material_ref": {
            "canonical": {
                "name": "attach_secret_material_ref",
                "description": "Attach one external secret material reference to this profile.",
                "is_constructor": False,
            },
            "input": CredentialProfileAttachSecretMaterialRefInput,
            "output": CredentialProfileAttachSecretMaterialRefOutput,
        },
        "grant_scope": {
            "canonical": {
                "name": "grant_scope",
                "description": "Attach one canonical scope/capability grant to this profile.",
                "is_constructor": False,
            },
            "input": CredentialProfileGrantScopeInput,
            "output": CredentialProfileGrantScopeOutput,
        },
        "record_readiness": {
            "canonical": {
                "name": "record_readiness",
                "description": "Attach one resolver/readiness receipt to this profile.",
                "is_constructor": False,
            },
            "input": CredentialProfileRecordReadinessInput,
            "output": CredentialProfileRecordReadinessOutput,
        },
        "record_usage": {
            "canonical": {
                "name": "record_usage",
                "description": "Attach one credential usage receipt to this profile.",
                "is_constructor": False,
            },
            "input": CredentialProfileRecordUsageInput,
            "output": CredentialProfileRecordUsageOutput,
        },
        "create_via_identity": {
            "canonical": {
                "name": "create_via_identity",
                "description": "Create one credential profile without storing secret material.\n\nContract:\n- Parent Identity context is injected by construct propagation.\n- Stable identity is derived from parent Identity plus profile keys.\n- Organization credentials use parent Identity with type=organization.",
                "is_constructor": True,
            },
            "input": CredentialProfileCreateViaIdentityInput,
            "output": CredentialProfileCreateViaIdentityOutput,
        },
    },
}

__all__ = [
    "CredentialProfile",
    "CredentialProfileAttachSecretMaterialRefInput",
    "CredentialProfileAttachSecretMaterialRefOutput",
    "CredentialProfileGrantScopeInput",
    "CredentialProfileGrantScopeOutput",
    "CredentialProfileRecordReadinessInput",
    "CredentialProfileRecordReadinessOutput",
    "CredentialProfileRecordUsageInput",
    "CredentialProfileRecordUsageOutput",
    "CredentialProfileCreateViaIdentityInput",
    "CredentialProfileCreateViaIdentityOutput",
    "FUNCTIONS",
]
