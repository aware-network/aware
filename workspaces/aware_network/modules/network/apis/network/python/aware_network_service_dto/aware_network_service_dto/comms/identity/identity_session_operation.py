from __future__ import annotations

# Standard
from typing import Literal
from uuid import UUID

# Third-party
from pydantic import Field

# Network Service Dto
from aware_network_service_dto.comms.models.network_node import (
    NetworkNodeOperationRequest,
    NetworkNodeOperationResponse,
)


class IdentityChallengeRequest(NetworkNodeOperationRequest):
    """
    Identity session operations for the Network Node control-plane (DTO-only).
    These operations are routed via:
    `NetworkOperation(type=NETWORK_NODE) -> NetworkNodeOperation(request/response)`.
    NOTE:
    - Discriminator tags are declared here to avoid network -> identity deps.
    - These variants live here to keep identity/session concerns isolated from
    environment provisioning concerns.
    Security:
    - These DTOs are transport-only. The node MUST treat returned artifacts
    (challenge, roles, etc.) as non-SSOT and enforce identity + authorization
    on stateful operations (e.g. provisioning, commits, publishes).
    v0:
    - `identity_challenge` returns a nonce-like `challenge` string.
    - `identity_login` completes authentication using a signature over that
    challenge (exact signature scheme is node policy).
    - `whoami` returns the currently-bound identity session for the active
    websocket connection.
    Request a challenge nonce for identity authentication.
    The client signs the returned `challenge` with its private key and submits it
    via `IdentityLoginRequest`.
    """

    # Discriminator Tag
    operation: Literal["identity_challenge"] = "identity_challenge"

    # Attributes
    public_key: str


class IdentityChallengeResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["identity_challenge"] = "identity_challenge"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    public_key: str
    challenge: str
    expires_at: str | None = Field(default=None)


class IdentityLoginRequest(NetworkNodeOperationRequest):
    """Complete identity authentication using the issued challenge."""

    # Discriminator Tag
    operation: Literal["identity_login"] = "identity_login"

    # Attributes
    public_key: str
    challenge: str
    signature: str


class IdentityLoginResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["identity_login"] = "identity_login"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    public_key: str
    roles: list[str] = Field(default_factory=list)


class TokenLoginRequest(NetworkNodeOperationRequest):
    """
    Authenticate via a revocable bearer token (e.g. APT token).
    This is intended for external agents/tools that cannot safely hold an Ed25519
    private key but still need a revocable credential.
    """

    # Discriminator Tag
    operation: Literal["token_login"] = "token_login"

    # Attributes
    token: str


class TokenLoginResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["token_login"] = "token_login"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    public_key: str | None = Field(default=None)
    roles: list[str] = Field(default_factory=list)
    token_id: UUID | None = Field(default=None)
    token_type: str | None = Field(default=None)
    scopes: list[str] = Field(default_factory=list)
    context_environment_id: UUID | None = Field(default=None)
    context_process_id: UUID | None = Field(default=None)
    context_thread_id: UUID | None = Field(default=None)
    expires_at: str | None = Field(default=None)


class WhoamiRequest(NetworkNodeOperationRequest):
    """Return the node's view of the current identity session bound to this websocket connection."""

    # Discriminator Tag
    operation: Literal["whoami"] = "whoami"


class WhoamiResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["whoami"] = "whoami"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    authenticated: bool
    public_key: str | None = Field(default=None)
    roles: list[str] = Field(default_factory=list)
    interface_session_id: UUID | None = Field(default=None)
    interface_id: UUID | None = Field(default=None)
    last_seen_at: str | None = Field(default=None)
