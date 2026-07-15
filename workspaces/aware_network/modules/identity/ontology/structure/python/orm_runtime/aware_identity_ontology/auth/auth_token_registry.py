from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
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
    from aware_identity_ontology.auth.auth_token import AuthToken


class AuthTokenRegistry(ORMModel):
    """
    Registry for execution/session tokens.
    Contract:
    - AuthTokenRegistry is scoped to APT execution credentials.
    - Identity-owned API keys and publish credentials use credential.CredentialProfile.
    - Plaintext token material is returned once and never stored in commits.
    """

    # Relationships
    tokens: list[AuthToken] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str = Field(default="v1")

    @classmethod
    async def ensure_registry(cls, key: str = "v1") -> AuthTokenRegistry:
        """
        Ensure the canonical execution-token registry root.

        Contract:
        - Registry id is stable (one per environment).
        - Tokens are APT execution/session credentials.
        - Public Identity credentials are modeled separately by CredentialProfile.
        """

        payload = {"key": key}
        result = await invoke_constructor(orm_class=cls, function_name="ensure_registry", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AuthTokenRegistry):
            return value
        return AuthTokenRegistry.validate_invocation_value(value)

    async def create_token(
        self,
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
        """Materialize an execution/session AuthToken under this registry via parent-path propagation."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="create_token", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.auth.auth_token import AuthToken

        if isinstance(value, AuthToken):
            return value
        return AuthToken.validate_invocation_value(value)

    async def issue_apt_token(
        self,
        actor_id: UUID,
        public_key: str,
        context_environment_id: UUID,
        context_process_id: UUID,
        context_thread_id: UUID,
        label: str | None = None,
        scopes: list[str] = [],
        expires_at: datetime | None = None,
        token_id: UUID | None = None,
        secret_b64url: str | None = None,
    ) -> JsonObject:
        """
        Issue a revocable execution bearer token for an AgentProcessThread (APT).

        Security contract:
        - Returned `token` is plaintext and must be shown once; only its sha256 is stored.
        - `actor_id` must match `public_key` stable-id derivation (anti-claim).
        - Context binding is required (env+process+thread) and must be enforced at transport.
        """

        payload = {
            "actor_id": actor_id,
            "public_key": public_key,
            "context_environment_id": context_environment_id,
            "context_process_id": context_process_id,
            "context_thread_id": context_thread_id,
            "label": label,
            "scopes": scopes,
            "expires_at": expires_at,
            "token_id": token_id,
            "secret_b64url": secret_b64url,
        }
        result = await invoke_instance(orm_model=self, function_name="issue_apt_token", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value


class AuthTokenRegistryEnsureRegistryInput(BaseModel):
    key: str = Field(default="v1")


class AuthTokenRegistryEnsureRegistryOutput(BaseModel):
    value: AuthTokenRegistry


class AuthTokenRegistryCreateTokenInput(BaseModel):
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


class AuthTokenRegistryCreateTokenOutput(BaseModel):
    value: AuthToken


class AuthTokenRegistryIssueAptTokenInput(BaseModel):
    actor_id: UUID
    public_key: str
    context_environment_id: UUID
    context_process_id: UUID
    context_thread_id: UUID
    label: str | None = Field(default=None)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = Field(default=None)
    token_id: UUID | None = Field(default=None)
    secret_b64url: str | None = Field(default=None)


class AuthTokenRegistryIssueAptTokenOutput(BaseModel):
    value: JsonObject


FUNCTIONS = {
    "AuthTokenRegistry": {
        "ensure_registry": {
            "canonical": {
                "name": "ensure_registry",
                "description": "Ensure the canonical execution-token registry root.\n\nContract:\n- Registry id is stable (one per environment).\n- Tokens are APT execution/session credentials.\n- Public Identity credentials are modeled separately by CredentialProfile.",
                "is_constructor": True,
            },
            "input": AuthTokenRegistryEnsureRegistryInput,
            "output": AuthTokenRegistryEnsureRegistryOutput,
        },
        "create_token": {
            "canonical": {
                "name": "create_token",
                "description": "Materialize an execution/session AuthToken under this registry via parent-path propagation.",
                "is_constructor": False,
            },
            "input": AuthTokenRegistryCreateTokenInput,
            "output": AuthTokenRegistryCreateTokenOutput,
        },
        "issue_apt_token": {
            "canonical": {
                "name": "issue_apt_token",
                "description": "Issue a revocable execution bearer token for an AgentProcessThread (APT).\n\nSecurity contract:\n- Returned `token` is plaintext and must be shown once; only its sha256 is stored.\n- `actor_id` must match `public_key` stable-id derivation (anti-claim).\n- Context binding is required (env+process+thread) and must be enforced at transport.",
                "is_constructor": False,
            },
            "input": AuthTokenRegistryIssueAptTokenInput,
            "output": AuthTokenRegistryIssueAptTokenOutput,
        },
    },
}

__all__ = [
    "AuthTokenRegistry",
    "AuthTokenRegistryEnsureRegistryInput",
    "AuthTokenRegistryEnsureRegistryOutput",
    "AuthTokenRegistryCreateTokenInput",
    "AuthTokenRegistryCreateTokenOutput",
    "AuthTokenRegistryIssueAptTokenInput",
    "AuthTokenRegistryIssueAptTokenOutput",
    "FUNCTIONS",
]
