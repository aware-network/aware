from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.auth.auth_token import AuthToken

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from datetime import timezone
from uuid import uuid4

from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity.context import current_actor_id
from aware_identity_ontology.auth.auth_token_enums import AuthTokenType

# --- AWARE: USER_IMPORTS END


async def revoke(auth_token: AuthToken) -> AuthToken:
    """
    Revoke this token.

    Contract:
    - Mutate-self-only: may only update this token instance.
    - Idempotent: revoking an already revoked token is a no-op.
    """

    # --- AWARE: LOGIC START revoke
    caller_id = current_actor_id()
    if caller_id != auth_token.actor_id and caller_id != auth_token.issued_by_actor_id:
        raise PermissionError("Only the token owner may revoke this token")

    if auth_token.revoked_at is not None:
        return auth_token

    auth_token.revoked_at = datetime.now(timezone.utc)
    return auth_token
    # --- AWARE: LOGIC END revoke


async def create_apt_via_auth_token_registry(
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

    # --- AWARE: LOGIC START create_apt_via_auth_token_registry
    if current_actor_id() != actor_id:
        raise PermissionError("actor_id must match the current actor")

    # v1: self-minted tokens only (issuer == subject).
    if issued_by_actor_id != actor_id:
        raise PermissionError("issued_by_actor_id must match actor_id")

    canonical_pub, _ = canonicalize_ed25519_public_key(public_key)

    normalized_sha256 = (sha256 or "").strip().lower()
    if len(normalized_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_sha256):
        raise ValueError("sha256 must be 64 hex characters (SHA256(secret) hex)")

    normalized_label = label.strip() if isinstance(label, str) else None
    if normalized_label == "":
        normalized_label = None

    normalized_scopes: list[str] = []
    seen_scopes: set[str] = set()
    for raw in scopes or []:
        scope = str(raw).strip()
        if not scope:
            continue
        key = scope.casefold()
        if key in seen_scopes:
            continue
        seen_scopes.add(key)
        normalized_scopes.append(scope)

    resolved_issued_at = issued_at
    if getattr(resolved_issued_at, "tzinfo", None) is None:
        resolved_issued_at = resolved_issued_at.replace(tzinfo=timezone.utc)

    resolved_expires_at = expires_at
    if resolved_expires_at is not None and getattr(resolved_expires_at, "tzinfo", None) is None:
        resolved_expires_at = resolved_expires_at.replace(tzinfo=timezone.utc)
    if resolved_expires_at is not None and resolved_expires_at <= resolved_issued_at:
        raise ValueError("expires_at must be after issued_at")

    resolved_token_id = token_id or uuid4()

    return AuthToken(
        id=resolved_token_id,
        token_type=AuthTokenType.apt,
        actor_id=actor_id,
        public_key=canonical_pub,
        issued_by_actor_id=issued_by_actor_id,
        issued_at=resolved_issued_at,
        label=normalized_label,
        scopes=normalized_scopes,
        context_environment_id=context_environment_id,
        context_process_id=context_process_id,
        context_thread_id=context_thread_id,
        expires_at=resolved_expires_at,
        revoked_at=None,
        sha256=normalized_sha256,
        auth_token_registry_id=auth_token_registry_id,
    )
    # --- AWARE: LOGIC END create_apt_via_auth_token_registry
