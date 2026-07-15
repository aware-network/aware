from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.auth.auth_token_enums import AuthTokenType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)


class AuthToken(ORMModel):
    """
    Execution/session token for an AgentProcessThread.
    Contract:
    - This rail is bound to env/process/thread execution context.
    - Public Identity/API credentials are modeled by credential.CredentialProfile.
    - Plaintext token material is never stored in commits.
    """

    # Attributes
    token_type: AuthTokenType
    actor_id: UUID
    public_key: str
    issued_by_actor_id: UUID
    issued_at: datetime
    label: str | None = Field(default=None)
    scopes: list[str] = Field(default_factory=list)
    context_environment_id: UUID | None = Field(
        default=None, description="Context binding (v1: APT tokens bind to env+process+thread)."
    )
    context_process_id: UUID | None = Field(default=None)
    context_thread_id: UUID | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)
    sha256: str = Field(description="SHA256(secret) hex. Plaintext secret is never stored in commits.")

    # Foreign Keys
    auth_token_registry_id: UUID = Field(description="Foreign key for AuthTokenRegistry.tokens")

    async def revoke(self) -> AuthToken:
        """
        Revoke this token.

        Contract:
        - Mutate-self-only: may only update this token instance.
        - Idempotent: revoking an already revoked token is a no-op.
        """

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="revoke", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AuthToken):
            return value
        return AuthToken.validate_invocation_value(value)

    @classmethod
    async def create_apt_via_auth_token_registry(
        cls,
        auth_token_registry_id: UUID,
        actor_id: UUID,
        public_key: str,
        issued_by_actor_id: UUID,
        issued_at: datetime,
        context_environment_id: UUID,
        context_process_id: UUID,
        context_thread_id: UUID,
        sha256: str,
        label: str | None = None,
        scopes: list[str] = [],
        expires_at: datetime | None = None,
        token_id: UUID | None = None,
    ) -> AuthToken:
        """
        Create a new APT (AgentProcessThread) auth token.

        Contract:
        - Parent `AuthTokenRegistry` ownership is propagated by constructor path
        (`_via_auth_token_registry`).
        - `token_id` is random by default; may be provided for deterministic tests.
        - `sha256` is SHA256(secret) hex; plaintext secret is never stored in commits.
        - Context binding is required (env+process+thread) and enforced at transport.
        """

        payload = {
            "auth_token_registry_id": auth_token_registry_id,
            "actor_id": actor_id,
            "public_key": public_key,
            "issued_by_actor_id": issued_by_actor_id,
            "issued_at": issued_at,
            "context_environment_id": context_environment_id,
            "context_process_id": context_process_id,
            "context_thread_id": context_thread_id,
            "sha256": sha256,
            "label": label,
            "scopes": scopes,
            "expires_at": expires_at,
            "token_id": token_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_apt_via_auth_token_registry", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AuthToken):
            return value
        return AuthToken.validate_invocation_value(value)


class AuthTokenRevokeInput(BaseModel):
    pass


class AuthTokenRevokeOutput(BaseModel):
    value: AuthToken


class AuthTokenCreateAptViaAuthTokenRegistryInput(BaseModel):
    auth_token_registry_id: UUID = Field(description="Foreign key for AuthTokenRegistry.tokens")
    actor_id: UUID
    public_key: str
    issued_by_actor_id: UUID
    issued_at: datetime
    context_environment_id: UUID
    context_process_id: UUID
    context_thread_id: UUID
    sha256: str
    label: str | None = Field(default=None)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = Field(default=None)
    token_id: UUID | None = Field(default=None)


class AuthTokenCreateAptViaAuthTokenRegistryOutput(BaseModel):
    value: AuthToken


FUNCTIONS = {
    "AuthToken": {
        "revoke": {
            "canonical": {
                "name": "revoke",
                "description": "Revoke this token.\n\nContract:\n- Mutate-self-only: may only update this token instance.\n- Idempotent: revoking an already revoked token is a no-op.",
                "is_constructor": False,
            },
            "input": AuthTokenRevokeInput,
            "output": AuthTokenRevokeOutput,
        },
        "create_apt_via_auth_token_registry": {
            "canonical": {
                "name": "create_apt_via_auth_token_registry",
                "description": "Create a new APT (AgentProcessThread) auth token.\n\nContract:\n- Parent `AuthTokenRegistry` ownership is propagated by constructor path (`_via_auth_token_registry`).\n- `token_id` is random by default; may be provided for deterministic tests.\n- `sha256` is SHA256(secret) hex; plaintext secret is never stored in commits.\n- Context binding is required (env+process+thread) and enforced at transport.",
                "is_constructor": True,
            },
            "input": AuthTokenCreateAptViaAuthTokenRegistryInput,
            "output": AuthTokenCreateAptViaAuthTokenRegistryOutput,
        },
    },
}

__all__ = [
    "AuthToken",
    "AuthTokenRevokeInput",
    "AuthTokenRevokeOutput",
    "AuthTokenCreateAptViaAuthTokenRegistryInput",
    "AuthTokenCreateAptViaAuthTokenRegistryOutput",
    "FUNCTIONS",
]
