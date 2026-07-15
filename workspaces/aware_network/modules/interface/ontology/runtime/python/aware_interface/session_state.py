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


def _to_jsonable(value: Any) -> Any:
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return dump(mode="json")
    return value


@dataclass(frozen=True, slots=True)
class PersistedEnvironmentSession:
    actor_id: UUID
    endpoint: str
    environment_id: UUID
    environment_config_id: UUID | None = None
    saved_at: datetime | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "actor_id": str(self.actor_id),
            "endpoint": self.endpoint,
            "environment_id": str(self.environment_id),
            "environment_config_id": (
                str(self.environment_config_id)
                if self.environment_config_id is not None
                else None
            ),
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
        }

    @classmethod
    def from_json(
        cls,
        payload: dict[str, Any],
    ) -> "PersistedEnvironmentSession | None":
        actor_raw = str(payload.get("actor_id") or "").strip()
        endpoint_raw = str(payload.get("endpoint") or "").strip()
        environment_raw = str(payload.get("environment_id") or "").strip()
        if not actor_raw or not endpoint_raw or not environment_raw:
            return None
        config_raw = str(payload.get("environment_config_id") or "").strip()
        try:
            return cls(
                actor_id=UUID(actor_raw),
                endpoint=endpoint_raw,
                environment_id=UUID(environment_raw),
                environment_config_id=UUID(config_raw) if config_raw else None,
                saved_at=_parse_optional_datetime(payload.get("saved_at")),
            )
        except ValueError:
            return None


@dataclass(frozen=True, slots=True)
class PersistedAuthoritySnapshot:
    actor_id: UUID
    endpoint: str
    environment_config_id: UUID
    ocg_id: UUID
    describe_environment_config: Any
    capabilities: Any
    saved_at: datetime | None = None


class InterfaceRuntimeSessionStateStore:
    """Interface runtime local state formerly hidden inside aware-session."""

    def __init__(
        self,
        *,
        state_root: str | Path | None = None,
        namespace: str = "interface",
    ) -> None:
        self._state_root = _resolve_state_root(state_root)
        self._namespace = namespace

    async def aload(
        self,
        *,
        actor_id: UUID,
        endpoint: str,
    ) -> PersistedEnvironmentSession | None:
        payload = self._load_sessions().get(self._key(actor_id=actor_id, endpoint=endpoint))
        if isinstance(payload, dict):
            return PersistedEnvironmentSession.from_json(payload)
        return None

    async def asave(self, session: PersistedEnvironmentSession) -> None:
        sessions = self._load_sessions()
        sessions[self._key(actor_id=session.actor_id, endpoint=session.endpoint)] = (
            session.to_json()
        )
        self._write_sessions(sessions)

    async def aload_latest_authority_snapshot(
        self,
        *,
        actor_id: UUID,
        endpoint: str,
        environment_config_id: UUID,
    ) -> PersistedAuthoritySnapshot | None:
        root = self.authority_root(
            actor_id=actor_id,
            endpoint=endpoint,
            environment_config_id=environment_config_id,
        )
        latest_path = root / "latest.json"
        if not latest_path.exists():
            return None
        try:
            latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if not isinstance(latest_payload, dict):
            return None
        describe_ref = Path(
            str(latest_payload.get("describe_environment_config") or "")
        ).expanduser()
        capabilities_ref = Path(str(latest_payload.get("capabilities") or "")).expanduser()
        ocg_raw = str(latest_payload.get("ocg_id") or "").strip()
        if not ocg_raw or not describe_ref.exists() or not capabilities_ref.exists():
            return None
        try:
            describe_payload = json.loads(describe_ref.read_text(encoding="utf-8"))
            capabilities_payload = json.loads(capabilities_ref.read_text(encoding="utf-8"))
            ocg_id = UUID(ocg_raw)
        except (json.JSONDecodeError, ValueError):
            return None
        return PersistedAuthoritySnapshot(
            actor_id=actor_id,
            endpoint=_normalize_endpoint(endpoint),
            environment_config_id=environment_config_id,
            ocg_id=ocg_id,
            describe_environment_config=describe_payload,
            capabilities=capabilities_payload,
            saved_at=_parse_optional_datetime(latest_payload.get("saved_at")),
        )

    async def asave_authority_snapshot(
        self,
        snapshot: PersistedAuthoritySnapshot,
    ) -> dict[str, str]:
        root = self.authority_root(
            actor_id=snapshot.actor_id,
            endpoint=snapshot.endpoint,
            environment_config_id=snapshot.environment_config_id,
        )
        snapshot_dir = root / str(snapshot.ocg_id)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        describe_path = snapshot_dir / "describe_environment_config.json"
        capabilities_path = snapshot_dir / "capabilities.json"
        describe_path.write_text(
            json.dumps(
                _to_jsonable(snapshot.describe_environment_config),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        capabilities_path.write_text(
            json.dumps(_to_jsonable(snapshot.capabilities), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        latest_path = root / "latest.json"
        saved_at = snapshot.saved_at or _utc_now()
        latest_path.write_text(
            json.dumps(
                {
                    "ocg_id": str(snapshot.ocg_id),
                    "saved_at": saved_at.isoformat(),
                    "describe_environment_config": str(describe_path),
                    "capabilities": str(capabilities_path),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "root": str(root),
            "latest": str(latest_path),
            "describe_environment_config": str(describe_path),
            "capabilities": str(capabilities_path),
        }

    def authority_root(
        self,
        *,
        actor_id: UUID,
        endpoint: str,
        environment_config_id: UUID,
    ) -> Path:
        endpoint_hash = hashlib.sha256(
            _normalize_endpoint(endpoint).encode("utf-8")
        ).hexdigest()
        return (
            self._state_root
            / self._namespace
            / "authority"
            / str(actor_id)
            / endpoint_hash
            / str(environment_config_id)
        )

    def _key(self, *, actor_id: UUID, endpoint: str) -> str:
        return f"{actor_id}@{_normalize_endpoint(endpoint)}"

    def _sessions_path(self) -> Path:
        return self._state_root / self._namespace / "session.json"

    def _load_sessions(self) -> dict[str, Any]:
        path = self._sessions_path()
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if isinstance(payload, dict):
            if isinstance(payload.get("sessions"), dict):
                return dict(payload["sessions"])
            return dict(payload)
        return {}

    def _write_sessions(self, sessions: dict[str, Any]) -> None:
        path = self._sessions_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"sessions": sessions}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


__all__ = [
    "InterfaceRuntimeSessionStateStore",
    "PersistedAuthoritySnapshot",
    "PersistedEnvironmentSession",
]
