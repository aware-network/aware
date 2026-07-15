from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_endpoint(endpoint: str) -> str:
    return endpoint.strip().rstrip("/")


def _resolve_state_root(state_home: str | Path | None = None) -> Path:
    if state_home is not None:
        return Path(state_home).expanduser()
    override = os.environ.get("AWARE_STATE_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".aware_state"


def _normalize_optional_token(raw: Any) -> str | None:
    value = str(raw or "").strip()
    return value or None


def _parse_optional_datetime(raw: Any) -> datetime | None:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


@dataclass(frozen=True, slots=True)
class InterfaceAuthSession:
    endpoint: str
    actor_id: UUID
    public_key: str | None
    method: str
    token_id: UUID | None = None
    token_type: str | None = None
    scopes: tuple[str, ...] = ()
    context_environment_id: UUID | None = None
    context_process_id: UUID | None = None
    context_thread_id: UUID | None = None
    saved_at: datetime | None = None
    path: Path | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "actor_id": str(self.actor_id),
            "public_key": self.public_key,
            "method": self.method,
            "token_id": str(self.token_id) if self.token_id is not None else None,
            "token_type": self.token_type,
            "scopes": list(self.scopes),
            "context_environment_id": (
                str(self.context_environment_id)
                if self.context_environment_id is not None
                else None
            ),
            "context_process_id": (
                str(self.context_process_id)
                if self.context_process_id is not None
                else None
            ),
            "context_thread_id": (
                str(self.context_thread_id)
                if self.context_thread_id is not None
                else None
            ),
            "saved_at": (
                self.saved_at.isoformat()
                if self.saved_at is not None
                else None
            ),
        }

    @classmethod
    def from_json(
        cls,
        payload: dict[str, Any],
        *,
        path: Path | None = None,
    ) -> "InterfaceAuthSession | None":
        endpoint = str(payload.get("endpoint") or "").strip()
        actor_raw = str(payload.get("actor_id") or "").strip()
        method = str(payload.get("method") or "").strip()
        if not endpoint or not actor_raw or not method:
            return None

        token_id_raw = str(payload.get("token_id") or "").strip()
        context_environment_id_raw = str(
            payload.get("context_environment_id") or ""
        ).strip()
        context_process_id_raw = str(payload.get("context_process_id") or "").strip()
        context_thread_id_raw = str(payload.get("context_thread_id") or "").strip()
        scopes_payload = payload.get("scopes")
        scopes: tuple[str, ...] = ()
        if isinstance(scopes_payload, list):
            scopes = tuple(
                str(scope).strip()
                for scope in scopes_payload
                if str(scope).strip()
            )

        try:
            return cls(
                endpoint=endpoint,
                actor_id=UUID(actor_raw),
                public_key=_normalize_optional_token(payload.get("public_key")),
                method=method,
                token_id=UUID(token_id_raw) if token_id_raw else None,
                token_type=_normalize_optional_token(payload.get("token_type")),
                scopes=scopes,
                context_environment_id=(
                    UUID(context_environment_id_raw)
                    if context_environment_id_raw
                    else None
                ),
                context_process_id=(
                    UUID(context_process_id_raw) if context_process_id_raw else None
                ),
                context_thread_id=(
                    UUID(context_thread_id_raw) if context_thread_id_raw else None
                ),
                saved_at=_parse_optional_datetime(payload.get("saved_at")),
                path=path,
            )
        except ValueError:
            return None


_INTERFACE_AUTH_FILENAME = "interface_auth.json"


def interface_auth_path(
    *,
    endpoint: str,
    namespace: str = "cli",
    state_home: str | Path | None = None,
) -> Path:
    endpoint_hash = hashlib.sha256(
        _normalize_endpoint(endpoint).encode("utf-8")
    ).hexdigest()
    return (
        _resolve_state_root(state_home)
        / namespace
        / "auth"
        / endpoint_hash
        / _INTERFACE_AUTH_FILENAME
    )


def save_interface_auth_session(
    auth_session: InterfaceAuthSession,
    *,
    namespace: str = "cli",
    state_home: str | Path | None = None,
) -> InterfaceAuthSession:
    path = interface_auth_path(
        endpoint=auth_session.endpoint,
        namespace=namespace,
        state_home=state_home,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    session = InterfaceAuthSession(
        endpoint=auth_session.endpoint,
        actor_id=auth_session.actor_id,
        public_key=auth_session.public_key,
        method=auth_session.method,
        token_id=auth_session.token_id,
        token_type=auth_session.token_type,
        scopes=auth_session.scopes,
        context_environment_id=auth_session.context_environment_id,
        context_process_id=auth_session.context_process_id,
        context_thread_id=auth_session.context_thread_id,
        saved_at=auth_session.saved_at or _utc_now(),
        path=path,
    )
    path.write_text(
        json.dumps(session.to_json(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return session


def load_interface_auth_session(
    *,
    endpoint: str,
    namespace: str = "cli",
    state_home: str | Path | None = None,
) -> InterfaceAuthSession | None:
    path = interface_auth_path(
        endpoint=endpoint,
        namespace=namespace,
        state_home=state_home,
    )
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return InterfaceAuthSession.from_json(payload, path=path)


async def login_interface_token_attachment(
    *,
    repository_root: Path | None = None,
    endpoint: str | None = None,
    token: str,
    namespace: str = "cli",
    state_home: str | Path | None = None,
) -> InterfaceAuthSession:
    _ = repository_root, endpoint, token, namespace, state_home
    raise RuntimeError(
        "Token login must run through the Interface service transport. "
        "Use aware-interface-service admission or InterfaceTransportSession."
    )


__all__ = [
    "InterfaceAuthSession",
    "interface_auth_path",
    "load_interface_auth_session",
    "login_interface_token_attachment",
    "save_interface_auth_session",
]
