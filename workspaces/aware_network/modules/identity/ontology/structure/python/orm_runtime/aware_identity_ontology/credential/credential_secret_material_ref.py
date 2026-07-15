from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import CredentialSecretResolverKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject


class CredentialSecretMaterialRef(ORMModel):
    """
    Reference to secret material held outside canonical commits.
    Contract:
    - Secret values are never stored here.
    - `secret_name` is the resolver key, not the secret value.
    - `fingerprint_sha256` may record a digest of the external material when the
    resolver can calculate one without exposing the material.
    """

    # Attributes
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

    # Foreign Keys
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.secret_material_refs")

    @classmethod
    async def create_via_credential_profile(
        cls,
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
        """Create one external secret material reference without storing the secret."""

        payload = {
            "credential_profile_id": credential_profile_id,
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
        result = await invoke_constructor(orm_class=cls, function_name="create_via_credential_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CredentialSecretMaterialRef):
            return value
        return CredentialSecretMaterialRef.validate_invocation_value(value)


class CredentialSecretMaterialRefCreateViaCredentialProfileInput(BaseModel):
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.secret_material_refs")
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


class CredentialSecretMaterialRefCreateViaCredentialProfileOutput(BaseModel):
    value: CredentialSecretMaterialRef


FUNCTIONS = {
    "CredentialSecretMaterialRef": {
        "create_via_credential_profile": {
            "canonical": {
                "name": "create_via_credential_profile",
                "description": "Create one external secret material reference without storing the secret.",
                "is_constructor": True,
            },
            "input": CredentialSecretMaterialRefCreateViaCredentialProfileInput,
            "output": CredentialSecretMaterialRefCreateViaCredentialProfileOutput,
        },
    },
}

__all__ = [
    "CredentialSecretMaterialRef",
    "CredentialSecretMaterialRefCreateViaCredentialProfileInput",
    "CredentialSecretMaterialRefCreateViaCredentialProfileOutput",
    "FUNCTIONS",
]
