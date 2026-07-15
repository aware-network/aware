from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from aware_interface_sdk.transport import (
    InterfaceTransportProfile,
    InterfaceTransportSession,
)


def _normalize_endpoint(endpoint: str) -> str:
    return endpoint.strip().rstrip("/")


class InterfaceAttachmentStore:
    """Tiny Interface SDK local store for interface ids only.

    Runtime/bootstrap/environment state belongs to Interface service/runtime
    ports, not the public Interface SDK attachment package.
    """

    def __init__(self, *, state_root: Path, namespace: str) -> None:
        self._state_root = state_root
        self._namespace = namespace

    def load_interface_id(self, *, actor_id: UUID, endpoint: str) -> UUID | None:
        interfaces = self._load_interfaces()
        raw = interfaces.get(self._key(actor_id=actor_id, endpoint=endpoint))
        if isinstance(raw, str) and raw.strip():
            try:
                return UUID(raw.strip())
            except ValueError:
                return None
        return None

    async def aload_interface_id(self, *, actor_id: UUID, endpoint: str) -> UUID | None:
        return self.load_interface_id(actor_id=actor_id, endpoint=endpoint)

    def save_interface_id(
        self,
        *,
        actor_id: UUID,
        endpoint: str,
        interface_id: UUID,
    ) -> None:
        interfaces = self._load_interfaces()
        interfaces[self._key(actor_id=actor_id, endpoint=endpoint)] = str(interface_id)
        self._write_interfaces(interfaces)

    async def asave_interface_id(
        self,
        *,
        actor_id: UUID,
        endpoint: str,
        interface_id: UUID,
    ) -> None:
        self.save_interface_id(
            actor_id=actor_id,
            endpoint=endpoint,
            interface_id=interface_id,
        )

    def _key(self, *, actor_id: UUID, endpoint: str) -> str:
        return f"{actor_id}@{_normalize_endpoint(endpoint)}"

    def _interfaces_path(self) -> Path:
        return self._state_root / self._namespace / "interfaces.json"

    def _load_interfaces(self) -> dict[str, Any]:
        path = self._interfaces_path()
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if isinstance(payload, dict):
            if isinstance(payload.get("interfaces"), dict):
                return dict(payload["interfaces"])
            return dict(payload)
        return {}

    def _write_interfaces(self, interfaces: dict[str, Any]) -> None:
        path = self._interfaces_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"interfaces": interfaces}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


@dataclass(frozen=True, slots=True)
class InterfaceAttachment:
    """Concrete Interface attachment owned by `aware-interface-sdk`."""

    client: Any
    store: InterfaceAttachmentStore
    transport_session: InterfaceTransportSession
    interface_id: UUID
    endpoint: str

    async def persist_interface_id_for_actor(
        self,
        *,
        actor_id: UUID,
        endpoint: str | None = None,
    ) -> None:
        await self.store.asave_interface_id(
            actor_id=actor_id,
            endpoint=endpoint or self.endpoint,
            interface_id=self.interface_id,
        )


async def create_interface_attachment(
    *,
    client: Any,
    state_home: Path,
    namespace: str,
    endpoint: str,
    host_label: str,
    capabilities: tuple[str, ...],
    persist_interface_id: bool,
) -> InterfaceAttachment:
    store = InterfaceAttachmentStore(state_root=state_home, namespace=namespace)
    actor_id = getattr(client.config, "actor_id")
    interface_id = await store.aload_interface_id(actor_id=actor_id, endpoint=endpoint)
    if interface_id is None:
        interface_id = uuid4()
        if persist_interface_id:
            await store.asave_interface_id(
                actor_id=actor_id,
                endpoint=endpoint,
                interface_id=interface_id,
            )
    transport_session = InterfaceTransportSession(
        client=client,
        profile=InterfaceTransportProfile.create(
            interface_id=interface_id,
            session_label=host_label,
            capabilities=capabilities,
        ),
    )
    return InterfaceAttachment(
        client=client,
        store=store,
        transport_session=transport_session,
        interface_id=interface_id,
        endpoint=endpoint,
    )


__all__ = [
    "InterfaceAttachment",
    "InterfaceAttachmentStore",
    "InterfaceTransportProfile",
    "create_interface_attachment",
]
