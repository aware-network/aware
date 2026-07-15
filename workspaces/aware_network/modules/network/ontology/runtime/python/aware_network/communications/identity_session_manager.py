"""
Identity session manager (control-plane; in-memory).

This module is **transport-only**:
- No ORM/graph dependencies
- No persistence (SSOT remains OIG commits)

It provides the minimal state required for a canonical node identity flow:
- `identity_challenge`: issue a short-lived challenge for a public key
- `identity_login`: verify a signature over that challenge and mark the websocket
  connection as authenticated
- `whoami`: return the current authenticated session (handled by node router)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import base64
import secrets
from typing import ClassVar, Optional
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from aware_utils.logging import logger


@dataclass(slots=True)
class PendingIdentityChallenge:
    public_key: str
    challenge: str
    expires_at: datetime


@dataclass(slots=True)
class IdentitySession:
    public_key: str
    roles: list[str]
    authenticated_at: datetime
    token_binding: TokenBinding | None = None


@dataclass(slots=True)
class TokenBinding:
    """Transport-scoped token binding for the authenticated connection.

    SSOT for token state (issue/revoke/expiry) is commit-backed in the Identity lane.
    This structure exists only so the node router can enforce context bindings for
    the lifetime of the websocket connection.
    """

    token_id: UUID
    token_type: str
    scopes: list[str]
    context_environment_id: UUID | None
    context_process_id: UUID | None
    context_thread_id: UUID | None
    expires_at: datetime | None = None


def _normalize_b64(value: str) -> str:
    raw = value.strip()
    padding = (-len(raw)) % 4
    if padding:
        raw += "=" * padding
    return raw


def _decode_key_material(value: str) -> bytes:
    raw = value.strip()
    if not raw:
        raise ValueError("Key material cannot be empty")

    # Prefix support: ed25519:<b64|hex>, base64:<...>, b64:<...>, hex:<...>
    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        prefix = prefix.strip().lower()
        rest = rest.strip()
        if prefix in {"ed25519", "base64", "b64"}:
            raw = rest
        elif prefix == "hex":
            try:
                return bytes.fromhex(rest)
            except ValueError as exc:
                raise ValueError("Invalid hex key material") from exc

    # Hex (common for keys/signatures)
    try:
        return bytes.fromhex(raw)
    except ValueError:
        pass

    # Base64 / URL-safe base64
    normalized = _normalize_b64(raw)
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            return decoder(normalized)
        except Exception:
            continue

    raise ValueError("Unsupported key material encoding; expected hex or base64")


def verify_ed25519_signature(*, public_key: str, signature: str, message: str) -> None:
    pub_bytes = _decode_key_material(public_key)
    sig_bytes = _decode_key_material(signature)
    if len(pub_bytes) != 32:
        raise ValueError(f"Invalid Ed25519 public key length: {len(pub_bytes)} (expected 32)")
    if len(sig_bytes) != 64:
        raise ValueError(f"Invalid Ed25519 signature length: {len(sig_bytes)} (expected 64)")

    pub = Ed25519PublicKey.from_public_bytes(pub_bytes)
    try:
        pub.verify(sig_bytes, message.encode("utf-8"))
    except InvalidSignature as exc:
        raise ValueError("Invalid signature") from exc


class IdentitySessionManager:
    """Singleton manager for identity sessions bound to websocket connections."""

    _instance: ClassVar[Optional["IdentitySessionManager"]] = None

    def __init__(self) -> None:
        self._pending_by_connection: dict[UUID, PendingIdentityChallenge] = {}
        self._sessions_by_connection: dict[UUID, IdentitySession] = {}

    @classmethod
    def instance(cls) -> "IdentitySessionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def issue_challenge(
        self,
        *,
        connection_id: UUID,
        public_key: str,
        ttl_s: int = 120,
    ) -> PendingIdentityChallenge:
        now = datetime.now(UTC)
        self._prune_expired(now)
        challenge = secrets.token_urlsafe(32)
        record = PendingIdentityChallenge(
            public_key=public_key,
            challenge=challenge,
            expires_at=now + timedelta(seconds=ttl_s),
        )
        self._pending_by_connection[connection_id] = record
        return record

    def complete_login(
        self,
        *,
        connection_id: UUID,
        public_key: str,
        challenge: str,
        signature: str,
        roles: list[str] | None = None,
    ) -> IdentitySession:
        now = datetime.now(UTC)
        self._prune_expired(now)

        pending = self._pending_by_connection.get(connection_id)
        if pending is None:
            raise ValueError("No pending challenge for this connection")
        if pending.expires_at <= now:
            self._pending_by_connection.pop(connection_id, None)
            raise ValueError("Challenge expired")
        if pending.public_key != public_key:
            raise ValueError("public_key does not match the issued challenge")
        if pending.challenge != challenge:
            raise ValueError("challenge does not match the issued challenge")

        verify_ed25519_signature(public_key=public_key, signature=signature, message=challenge)

        session = IdentitySession(
            public_key=public_key,
            roles=list(roles or []),
            authenticated_at=now,
        )
        self._sessions_by_connection[connection_id] = session
        self._pending_by_connection.pop(connection_id, None)
        return session

    def complete_token_login(
        self,
        *,
        connection_id: UUID,
        public_key: str,
        token_binding: TokenBinding,
        roles: list[str] | None = None,
    ) -> IdentitySession:
        """Complete authentication for a connection using a bearer token."""

        now = datetime.now(UTC)
        session = IdentitySession(
            public_key=public_key,
            roles=list(roles or []),
            authenticated_at=now,
            token_binding=token_binding,
        )
        self._sessions_by_connection[connection_id] = session
        self._pending_by_connection.pop(connection_id, None)
        return session

    def get_session(self, *, connection_id: UUID) -> IdentitySession | None:
        return self._sessions_by_connection.get(connection_id)

    async def disconnect(self, *, connection_id: UUID) -> None:
        self._pending_by_connection.pop(connection_id, None)
        self._sessions_by_connection.pop(connection_id, None)

    def _prune_expired(self, now: datetime) -> None:
        expired: list[UUID] = []
        for cid, pending in self._pending_by_connection.items():
            if pending.expires_at <= now:
                expired.append(cid)
        for cid in expired:
            self._pending_by_connection.pop(cid, None)
        if expired:
            logger.debug("Pruned %d expired identity challenges", len(expired))


__all__ = [
    "IdentitySession",
    "IdentitySessionManager",
    "PendingIdentityChallenge",
    "TokenBinding",
    "verify_ed25519_signature",
]
