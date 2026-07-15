from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.auth.auth_token import AuthToken
from aware_identity_ontology.auth.auth_token_registry import AuthTokenRegistry

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
import base64
import hashlib
import secrets
from datetime import timezone
from uuid import uuid4

from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity.context import current_actor_id, current_invocation_context
from aware_identity_ontology.stable_ids import (
    stable_actor_id,
    stable_auth_token_registry_id,
    stable_identity_id,
)

# --- AWARE: USER_IMPORTS END


async def ensure_registry(key: str = "v1") -> AuthTokenRegistry:
    """
    Ensure the canonical execution-token registry root.

    Contract:
    - Registry id is stable (one per environment).
    - Tokens are APT execution/session credentials.
    - Public Identity credentials are modeled separately by CredentialProfile.
    """

    # --- AWARE: LOGIC START ensure_registry
    return AuthTokenRegistry(id=stable_auth_token_registry_id())
    # --- AWARE: LOGIC END ensure_registry


async def create_token(
    auth_token_registry: AuthTokenRegistry,
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
    Materialize an execution/session AuthToken under this registry via parent-path propagation.
    """

    # --- AWARE: LOGIC START create_token
    if auth_token_registry.id is None:
        raise ValueError("AuthTokenRegistry.create_token requires a bound registry.id")

    token_obj = await AuthToken.create_apt_via_auth_token_registry(
        auth_token_registry_id=auth_token_registry.id,
        actor_id=actor_id,
        public_key=public_key,
        issued_by_actor_id=issued_by_actor_id,
        issued_at=issued_at,
        context_environment_id=context_environment_id,
        context_process_id=context_process_id,
        context_thread_id=context_thread_id,
        sha256=sha256,
        label=label,
        scopes=scopes,
        expires_at=expires_at,
        token_id=token_id,
    )
    if all(existing.id != token_obj.id for existing in auth_token_registry.tokens):
        auth_token_registry.tokens.append(token_obj)
    return token_obj
    # --- AWARE: LOGIC END create_token


async def issue_apt_token(
    auth_token_registry: AuthTokenRegistry,
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

    # --- AWARE: LOGIC START issue_apt_token
    if auth_token_registry.id is None:
        raise ValueError("AuthTokenRegistry.issue_apt_token requires a bound registry.id")

    actor_id = actor_id if isinstance(actor_id, UUID) else UUID(str(actor_id))
    context_environment_id = (
        context_environment_id if isinstance(context_environment_id, UUID) else UUID(str(context_environment_id))
    )
    context_process_id = context_process_id if isinstance(context_process_id, UUID) else UUID(str(context_process_id))
    context_thread_id = context_thread_id if isinstance(context_thread_id, UUID) else UUID(str(context_thread_id))
    token_id = token_id if token_id is None or isinstance(token_id, UUID) else UUID(str(token_id))

    if actor_id != current_actor_id():
        raise PermissionError("actor_id must match the current actor")

    # Bind token issuance to the active invocation context so callers can't mint
    # a token for a different env/process/thread without switching context.
    ctx = current_invocation_context()
    if ctx.environment_id != context_environment_id:
        raise PermissionError("context_environment_id must match current environment")
    if ctx.process_id != context_process_id:
        raise PermissionError("context_process_id must match current process")
    if ctx.thread_id != context_thread_id:
        raise PermissionError("context_thread_id must match current thread")

    canonical_pub, _key_bytes = canonicalize_ed25519_public_key(public_key)
    matches_actor = False
    for identity_type_value in ("human", "agent", "organization", "system"):
        identity_id = stable_identity_id(
            public_key=canonical_pub,
            type=identity_type_value,
        )
        if stable_actor_id(identity_id=identity_id) == actor_id:
            matches_actor = True
            break
    if not matches_actor:
        raise PermissionError("actor_id does not match public key (anti-claim)")

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

    now = datetime.now(timezone.utc)
    resolved_expires_at = expires_at
    if resolved_expires_at is not None and getattr(resolved_expires_at, "tzinfo", None) is None:
        resolved_expires_at = resolved_expires_at.replace(tzinfo=timezone.utc)
    if resolved_expires_at is not None and resolved_expires_at <= now:
        raise ValueError("expires_at must be in the future")

    resolved_token_id = token_id or uuid4()

    for existing in auth_token_registry.tokens:
        if existing.id == resolved_token_id:
            raise ValueError("token_id already exists in this registry")

    raw_secret = (secret_b64url or "").strip() if secret_b64url is not None else ""
    secret_bytes: bytes
    if raw_secret:
        padding = "=" * (-len(raw_secret) % 4)
        try:
            secret_bytes = base64.urlsafe_b64decode(raw_secret + padding)
        except Exception as exc:
            raise ValueError("secret_b64url must be base64url") from exc
    else:
        secret_bytes = secrets.token_bytes(32)
        raw_secret = base64.urlsafe_b64encode(secret_bytes).rstrip(b"=").decode("ascii")

    if len(secret_bytes) < 16:
        raise ValueError("token secret too short (min 16 bytes)")

    sha256_hex = hashlib.sha256(secret_bytes).hexdigest()
    token_str = f"aware_apt_{resolved_token_id}.{raw_secret}"

    token_obj = await AuthToken.create_apt_via_auth_token_registry(
        auth_token_registry_id=auth_token_registry.id,
        actor_id=actor_id,
        public_key=canonical_pub,
        issued_by_actor_id=actor_id,
        issued_at=now,
        context_environment_id=context_environment_id,
        context_process_id=context_process_id,
        context_thread_id=context_thread_id,
        sha256=sha256_hex,
        label=normalized_label,
        scopes=normalized_scopes,
        expires_at=resolved_expires_at,
        token_id=resolved_token_id,
    )
    auth_token_registry.tokens.append(token_obj)

    def _iso(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if getattr(dt, "tzinfo", None) is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    return {
        "token_id": str(resolved_token_id),
        "token_type": "apt",
        "token": token_str,
        "actor_id": str(actor_id),
        "public_key": canonical_pub,
        "issued_at": _iso(now),
        "label": normalized_label,
        "scopes": list(normalized_scopes),
        "context_environment_id": str(context_environment_id),
        "context_process_id": str(context_process_id),
        "context_thread_id": str(context_thread_id),
        "expires_at": _iso(resolved_expires_at),
    }
    # --- AWARE: LOGIC END issue_apt_token
