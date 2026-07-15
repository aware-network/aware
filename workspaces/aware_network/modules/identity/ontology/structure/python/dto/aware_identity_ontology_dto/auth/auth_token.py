from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.auth.auth_token_enums import AuthTokenType


class AuthToken(BaseModel):
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
