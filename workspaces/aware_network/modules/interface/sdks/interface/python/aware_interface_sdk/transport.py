from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Iterable, Protocol
from uuid import UUID, uuid4

from aware_network_service_dto.comms.models.network_node import (
    InterfaceSessionHeartbeatResponse,
    InterfaceSessionRegisterRequest,
    InterfaceSessionRegisterResponse,
)
from aware_network_service_dto.comms.identity.identity_session_operation import (
    TokenLoginResponse,
    WhoamiResponse,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_capabilities(values: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        token = str(value).strip()
        if not token or token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class InterfaceTransportProfile:
    interface_id: UUID
    interface_session_id: UUID
    session_label: str
    capabilities: tuple[str, ...] = ()
    protocol_version: int = 1

    @classmethod
    def create(
        cls,
        *,
        interface_id: UUID,
        session_label: str,
        capabilities: Iterable[str] = (),
        interface_session_id: UUID | None = None,
        protocol_version: int = 1,
    ) -> "InterfaceTransportProfile":
        label = session_label.strip()
        if not label:
            raise ValueError("session_label is required")
        return cls(
            interface_id=interface_id,
            interface_session_id=interface_session_id or uuid4(),
            session_label=label,
            capabilities=_normalize_capabilities(capabilities),
            protocol_version=protocol_version,
        )

    def to_api_profile(self) -> InterfaceSessionRegisterRequest:
        return InterfaceSessionRegisterRequest(
            interface_id=self.interface_id,
            interface_session_id=self.interface_session_id,
            session_label=self.session_label,
            capabilities=[*self.capabilities],
            protocol_version=self.protocol_version,
        )


@dataclass(frozen=True, slots=True)
class InterfaceTransportBindingState:
    actor_id: UUID
    interface_id: UUID
    interface_session_id: UUID
    session_label: str
    capabilities: tuple[str, ...]
    protocol_version: int
    interface_identity_network_node_id: UUID | None = None
    interface_session_network_binding_id: UUID | None = None
    last_seen_at: str | None = None


class InterfaceTransportClient(Protocol):
    config: object

    async def ensure_interface_session_registered(
        self,
        *,
        profile: InterfaceSessionRegisterRequest,
    ) -> InterfaceSessionRegisterResponse: ...

    async def token_login(self, *, token: str) -> TokenLoginResponse: ...

    async def heartbeat_interface_session(
        self,
        *,
        profile: InterfaceSessionRegisterRequest,
        timestamp: str,
    ) -> InterfaceSessionHeartbeatResponse: ...

    async def whoami(self) -> WhoamiResponse: ...

    async def close(self) -> None: ...


class InterfaceTransportSession:
    """Interface transport lifecycle over Node interface-session operations."""

    def __init__(
        self,
        *,
        client: InterfaceTransportClient,
        profile: InterfaceTransportProfile,
    ) -> None:
        self._client = client
        self._profile = profile
        self._binding: InterfaceTransportBindingState | None = None

    @property
    def client(self) -> InterfaceTransportClient:
        return self._client

    @property
    def profile(self) -> InterfaceTransportProfile:
        return self._profile

    @property
    def binding(self) -> InterfaceTransportBindingState | None:
        return self._binding

    async def ensure_registered(self) -> InterfaceTransportBindingState:
        actor_id = getattr(self._client.config, "actor_id")
        profile = self._profile.to_api_profile()
        profile.actor_id = actor_id
        response = await self._client.ensure_interface_session_registered(
            profile=profile,
        )
        binding = InterfaceTransportBindingState(
            actor_id=actor_id,
            interface_id=response.interface_id,
            interface_session_id=response.interface_session_id,
            session_label=self._profile.session_label,
            capabilities=self._profile.capabilities,
            protocol_version=response.protocol_version,
            interface_identity_network_node_id=(
                response.interface_identity_network_node_id
            ),
            interface_session_network_binding_id=(
                response.interface_session_network_binding_id
            ),
            last_seen_at=response.last_seen_at,
        )
        self._binding = binding
        return binding

    async def login_with_token(self, *, token: str) -> TokenLoginResponse:
        if self._binding is None:
            await self.ensure_registered()
        response = await self._client.token_login(token=token)
        actor_id = getattr(response, "actor_id", None)
        if actor_id is not None and self._binding is not None:
            self._binding = replace(self._binding, actor_id=actor_id)
        return response

    async def heartbeat(
        self,
        *,
        timestamp: str | None = None,
    ) -> InterfaceSessionHeartbeatResponse:
        response = await self._client.heartbeat_interface_session(
            profile=self._profile.to_api_profile(),
            timestamp=timestamp or _utc_now_iso(),
        )
        if self._binding is None:
            await self.ensure_registered()
        if self._binding is not None:
            self._binding = replace(
                self._binding,
                last_seen_at=response.last_seen_at,
            )
        return response

    async def whoami(self) -> WhoamiResponse:
        response = await self._client.whoami()
        if self._binding is not None:
            actor_id = response.actor_id or self._binding.actor_id
            self._binding = replace(
                self._binding,
                actor_id=actor_id,
                last_seen_at=response.last_seen_at or self._binding.last_seen_at,
            )
        return response

    async def close(self) -> None:
        await self._client.close()
        self._binding = None


__all__ = [
    "InterfaceTransportBindingState",
    "InterfaceTransportClient",
    "InterfaceTransportProfile",
    "InterfaceTransportSession",
]
