from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.auth.auth_token_enums import AuthTokenType

# Orm
from aware_orm.models.orm_model import ORMModel


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
