from __future__ import annotations

import asyncio
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from aware_node_service.http_api.auth import get_current_actor_id
from aware_utils.logging import logger


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _pairing_ttl_s() -> int:
    raw = (os.environ.get("AWARE_PAIRING_TTL_S") or "").strip()
    if not raw:
        return 10 * 60
    try:
        value = int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid AWARE_PAIRING_TTL_S={raw!r}") from exc
    return max(15, value)


def _device_code_bytes() -> int:
    raw = (os.environ.get("AWARE_PAIRING_DEVICE_CODE_BYTES") or "").strip()
    if not raw:
        return 32
    try:
        value = int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid AWARE_PAIRING_DEVICE_CODE_BYTES={raw!r}") from exc
    return max(16, value)


def _user_code_length() -> int:
    raw = (os.environ.get("AWARE_PAIRING_USER_CODE_LEN") or "").strip()
    if not raw:
        return 8
    try:
        value = int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid AWARE_PAIRING_USER_CODE_LEN={raw!r}") from exc
    return max(6, min(12, value))


_USER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no I/O/0/1


def _format_user_code(code: str) -> str:
    raw = "".join(ch for ch in (code or "").upper() if ch.isalnum())
    if len(raw) <= 4:
        return raw
    # Standard UX: XXXX-XXXX (or longer, but keep a single separator).
    return raw[:4] + "-" + raw[4:]


def _generate_user_code() -> str:
    length = _user_code_length()
    code = "".join(secrets.choice(_USER_CODE_ALPHABET) for _ in range(length))
    return _format_user_code(code)


def _normalize_user_code(code: str) -> str:
    return "".join(ch for ch in (code or "").upper() if ch in _USER_CODE_ALPHABET)


def _generate_device_code() -> str:
    # OAuth device-code style: high entropy, url-safe, never user-facing.
    return secrets.token_urlsafe(_device_code_bytes())


def _max_ciphertext_bytes() -> int:
    raw = (os.environ.get("AWARE_PAIRING_MAX_CIPHERTEXT_BYTES") or "").strip()
    if not raw:
        return 16 * 1024
    try:
        value = int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid AWARE_PAIRING_MAX_CIPHERTEXT_BYTES={raw!r}") from exc
    return max(1024, value)


@dataclass(slots=True)
class _PairingRecord:
    pairing_id: UUID
    device_code: str
    user_code: str
    created_at: datetime
    expires_at: datetime
    client_pubkey: str
    client_label: str | None
    status: str  # pending|approved|denied|consumed (consumed is internal-only)
    approved_by_actor_id: UUID | None = None
    trusted_pubkey: str | None = None
    ciphertext_b64: str | None = None


class _PairingStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._by_device_code: dict[str, _PairingRecord] = {}
        self._device_code_by_user_code: dict[str, str] = {}

    async def clear(self) -> None:
        async with self._lock:
            self._by_device_code.clear()
            self._device_code_by_user_code.clear()

    async def _prune_expired_locked(self, now: datetime) -> None:
        expired = [
            device_code
            for device_code, rec in self._by_device_code.items()
            if rec.expires_at <= now
        ]
        for device_code in expired:
            rec = self._by_device_code.pop(device_code, None)
            if rec is None:
                continue
            normalized = _normalize_user_code(rec.user_code)
            self._device_code_by_user_code.pop(normalized, None)

    async def start(
        self, *, client_pubkey: str, client_label: str | None
    ) -> _PairingRecord:
        now = _utcnow()
        ttl = timedelta(seconds=_pairing_ttl_s())

        async with self._lock:
            await self._prune_expired_locked(now)

            device_code = _generate_device_code()
            while device_code in self._by_device_code:
                device_code = _generate_device_code()

            user_code = _generate_user_code()
            normalized = _normalize_user_code(user_code)
            while normalized in self._device_code_by_user_code:
                user_code = _generate_user_code()
                normalized = _normalize_user_code(user_code)

            rec = _PairingRecord(
                pairing_id=uuid4(),
                device_code=device_code,
                user_code=user_code,
                created_at=now,
                expires_at=now + ttl,
                client_pubkey=client_pubkey,
                client_label=client_label,
                status="pending",
            )
            self._by_device_code[device_code] = rec
            self._device_code_by_user_code[normalized] = device_code
            return rec

    async def inspect(self, *, user_code: str) -> _PairingRecord | None:
        now = _utcnow()
        normalized = _normalize_user_code(user_code)
        if not normalized:
            return None

        async with self._lock:
            await self._prune_expired_locked(now)
            device_code = self._device_code_by_user_code.get(normalized)
            if device_code is None:
                return None
            return self._by_device_code.get(device_code)

    async def complete(
        self,
        *,
        user_code: str,
        approved_by_actor_id: UUID,
        trusted_pubkey: str | None,
        ciphertext_b64: str | None,
        decision: str,
    ) -> _PairingRecord | None:
        now = _utcnow()
        normalized = _normalize_user_code(user_code)
        if not normalized:
            return None

        async with self._lock:
            await self._prune_expired_locked(now)
            device_code = self._device_code_by_user_code.get(normalized)
            if device_code is None:
                return None
            rec = self._by_device_code.get(device_code)
            if rec is None:
                return None

            if rec.status in {"approved", "denied", "consumed"}:
                # Idempotent: return current state.
                return rec

            if decision == "deny":
                rec.status = "denied"
                rec.approved_by_actor_id = approved_by_actor_id
                return rec

            if decision != "approve":
                raise ValueError(f"Unsupported decision={decision!r}")

            if trusted_pubkey is None or not trusted_pubkey.strip():
                raise ValueError("trusted_pubkey is required for approval")
            if ciphertext_b64 is None or not ciphertext_b64.strip():
                raise ValueError("ciphertext_b64 is required for approval")
            if len(ciphertext_b64.encode("utf-8")) > _max_ciphertext_bytes():
                raise ValueError("ciphertext_b64 too large")

            rec.status = "approved"
            rec.approved_by_actor_id = approved_by_actor_id
            rec.trusted_pubkey = trusted_pubkey
            rec.ciphertext_b64 = ciphertext_b64
            return rec

    async def poll(self, *, device_code: str) -> _PairingRecord | None:
        now = _utcnow()
        normalized_device_code = (device_code or "").strip()
        if not normalized_device_code:
            return None

        async with self._lock:
            await self._prune_expired_locked(now)
            rec = self._by_device_code.get(normalized_device_code)
            if rec is None:
                return None

            if rec.status == "approved":
                # One-shot delivery. The ciphertext is E2E so replay isn't fatal,
                # but one-shot delivery reduces accidental reuse.
                normalized_user = _normalize_user_code(rec.user_code)
                self._device_code_by_user_code.pop(normalized_user, None)
                self._by_device_code.pop(normalized_device_code, None)
                return rec
            return rec


_PAIRING_STORE = _PairingStore()


class PairingStartRequest(BaseModel):
    client_pubkey: str = Field(
        ..., description="Ephemeral X25519 public key (encoding defined by clients)."
    )
    client_label: str | None = Field(
        default=None, description="Optional client device label (for UI display)."
    )


class PairingStartResponse(BaseModel):
    pairing_id: UUID
    device_code: str
    user_code: str
    expires_at: str
    poll_interval_s: int = 2


class PairingInspectRequest(BaseModel):
    user_code: str


class PairingInspectResponse(BaseModel):
    pairing_id: UUID
    status: str
    client_pubkey: str
    client_label: str | None = None
    expires_at: str


class PairingCompleteRequest(BaseModel):
    user_code: str
    decision: str = Field(
        default="approve",
        description="approve|deny",
        pattern="^(approve|deny)$",
    )
    trusted_pubkey: str | None = None
    ciphertext_b64: str | None = None


class PairingCompleteResponse(BaseModel):
    pairing_id: UUID
    status: str
    expires_at: str


class PairingPollResponse(BaseModel):
    pairing_id: UUID
    status: str
    expires_at: str
    trusted_pubkey: str | None = None
    ciphertext_b64: str | None = None
    approved_by_actor_id: UUID | None = None
    poll_interval_s: int = 2


pairing_router = APIRouter()


@pairing_router.post("/auth/pairing/start", response_model=PairingStartResponse)
async def pairing_start(request: PairingStartRequest) -> PairingStartResponse:
    client_pubkey = (request.client_pubkey or "").strip()
    if not client_pubkey:
        raise HTTPException(status_code=400, detail="client_pubkey is required")

    rec = await _PAIRING_STORE.start(
        client_pubkey=client_pubkey,
        client_label=(request.client_label or "").strip() or None,
    )
    logger.info(
        "pairing.start pairing_id=%s expires_at=%s",
        rec.pairing_id,
        rec.expires_at.isoformat(),
    )
    return PairingStartResponse(
        pairing_id=rec.pairing_id,
        device_code=rec.device_code,
        user_code=rec.user_code,
        expires_at=rec.expires_at.isoformat().replace("+00:00", "Z"),
    )


@pairing_router.post(
    "/auth/pairing/inspect",
    response_model=PairingInspectResponse,
)
async def pairing_inspect(
    request: PairingInspectRequest,
    actor_id: UUID = Depends(get_current_actor_id),
) -> PairingInspectResponse:
    rec = await _PAIRING_STORE.inspect(user_code=request.user_code)
    if rec is None:
        raise HTTPException(status_code=404, detail="Unknown or expired pairing code")
    logger.info(
        "pairing.inspect pairing_id=%s requested_by=%s status=%s",
        rec.pairing_id,
        actor_id,
        rec.status,
    )
    return PairingInspectResponse(
        pairing_id=rec.pairing_id,
        status=rec.status,
        client_pubkey=rec.client_pubkey,
        client_label=rec.client_label,
        expires_at=rec.expires_at.isoformat().replace("+00:00", "Z"),
    )


@pairing_router.post(
    "/auth/pairing/complete",
    response_model=PairingCompleteResponse,
)
async def pairing_complete(
    request: PairingCompleteRequest,
    actor_id: UUID = Depends(get_current_actor_id),
) -> PairingCompleteResponse:
    decision = (request.decision or "").strip().lower()
    try:
        rec = await _PAIRING_STORE.complete(
            user_code=request.user_code,
            approved_by_actor_id=actor_id,
            trusted_pubkey=(request.trusted_pubkey or "").strip() or None,
            ciphertext_b64=(request.ciphertext_b64 or "").strip() or None,
            decision=decision,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if rec is None:
        raise HTTPException(status_code=404, detail="Unknown or expired pairing code")

    logger.info(
        "pairing.complete pairing_id=%s requested_by=%s decision=%s status=%s",
        rec.pairing_id,
        actor_id,
        decision,
        rec.status,
    )
    return PairingCompleteResponse(
        pairing_id=rec.pairing_id,
        status=rec.status,
        expires_at=rec.expires_at.isoformat().replace("+00:00", "Z"),
    )


@pairing_router.get("/auth/pairing/poll", response_model=PairingPollResponse)
async def pairing_poll(device_code: str) -> PairingPollResponse:
    rec = await _PAIRING_STORE.poll(device_code=device_code)
    if rec is None:
        raise HTTPException(status_code=404, detail="Unknown or expired device_code")
    # `poll()` consumes approved records, so only "approved" returns ciphertext.
    return PairingPollResponse(
        pairing_id=rec.pairing_id,
        status=rec.status,
        expires_at=rec.expires_at.isoformat().replace("+00:00", "Z"),
        trusted_pubkey=rec.trusted_pubkey,
        ciphertext_b64=rec.ciphertext_b64,
        approved_by_actor_id=rec.approved_by_actor_id,
    )


async def _reset_pairing_store_for_tests() -> None:  # pragma: no cover
    await _PAIRING_STORE.clear()


__all__ = ["pairing_router"]
