from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import CredentialGrantEffect

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject


class CredentialGrant(ORMModel):
    """
    Capability/scope granted to one credential profile.
    Contract:
    - Grants describe what a credential may be used for.
    - Enforcement happens at service/API boundaries; this object is canonical
    policy metadata and audit context.
    """

    # Attributes
    grant_key: str
    effect: CredentialGrantEffect = Field(default=CredentialGrantEffect.allow)
    scope_kind: str
    scope_value: str
    operation: str | None = Field(default=None)
    resource_ref: str | None = Field(default=None)
    expires_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)

    # Foreign Keys
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.grants")

    @classmethod
    async def create_via_credential_profile(
        cls,
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
        """Create one deterministic credential grant under a CredentialProfile."""

        payload = {
            "credential_profile_id": credential_profile_id,
            "grant_key": grant_key,
            "scope_kind": scope_kind,
            "scope_value": scope_value,
            "effect": effect,
            "operation": operation,
            "resource_ref": resource_ref,
            "expires_at_utc": expires_at_utc,
            "metadata": metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_credential_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CredentialGrant):
            return value
        return CredentialGrant.validate_invocation_value(value)


class CredentialGrantCreateViaCredentialProfileInput(BaseModel):
    credential_profile_id: UUID = Field(description="Foreign key for CredentialProfile.grants")
    grant_key: str
    scope_kind: str
    scope_value: str
    effect: CredentialGrantEffect = Field(default=CredentialGrantEffect.allow)
    operation: str | None = Field(default=None)
    resource_ref: str | None = Field(default=None)
    expires_at_utc: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CredentialGrantCreateViaCredentialProfileOutput(BaseModel):
    value: CredentialGrant


FUNCTIONS = {
    "CredentialGrant": {
        "create_via_credential_profile": {
            "canonical": {
                "name": "create_via_credential_profile",
                "description": "Create one deterministic credential grant under a CredentialProfile.",
                "is_constructor": True,
            },
            "input": CredentialGrantCreateViaCredentialProfileInput,
            "output": CredentialGrantCreateViaCredentialProfileOutput,
        },
    },
}

__all__ = [
    "CredentialGrant",
    "CredentialGrantCreateViaCredentialProfileInput",
    "CredentialGrantCreateViaCredentialProfileOutput",
    "FUNCTIONS",
]
