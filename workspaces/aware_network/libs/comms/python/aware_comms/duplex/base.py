"""Base classes for aware-comms duplex connections."""

from __future__ import annotations

import logging
from enum import Enum
from typing import ClassVar, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictStr

from aware_comms.duplex.webrtc.models import (
    RTCIceCandidateInit,
    WsRTCIceCandidateRequest,
    WsRTCOfferRequest,
    WsRTCResponse,
)

logger = logging.getLogger(__name__)

WS_T = TypeVar("WS_T")
WRTC_T = TypeVar("WRTC_T")


class DuplexSide(Enum):
    CLIENT = "client"
    SERVER = "server"

    @property
    def opposite(self) -> "DuplexSide":
        return DuplexSide.SERVER if self is DuplexSide.CLIENT else DuplexSide.CLIENT


class DuplexBase(BaseModel, Generic[WS_T, WRTC_T]):
    """Base helper that stores websocket connections per duplex instance.

    WebRTC support is optional: consumers may ignore `wrtc_connections` entirely.
    The signaling helpers are kept import-safe (the concrete WebRTC implementation
    can live behind optional dependencies).
    """

    client_type: StrictStr
    server_type: StrictStr
    side: DuplexSide

    ws_connections: dict[UUID, WS_T] = Field(default_factory=dict)
    wrtc_connections: dict[UUID, WRTC_T] = Field(default_factory=dict)

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def get_net_endpoint(self) -> str:
        endpoint = f"{self.client_type}/{self.server_type}"
        logger.debug(
            "Computed net endpoint for %s -> %s: %s",
            self.client_type,
            self.server_type,
            endpoint,
        )
        return endpoint

    def get_ws_connection(self, connection_id: UUID) -> WS_T | None:
        return self.ws_connections.get(connection_id)

    def get_wrtc_connection(self, connection_id: UUID) -> WRTC_T | None:
        return self.wrtc_connections.get(connection_id)

    async def _send_data(self, data: str, connection_id: UUID) -> bool:
        """Implement websocket send logic."""
        del data, connection_id
        raise NotImplementedError("_send_data must be implemented by subclasses")

    async def disconnect(self, connection_id: UUID) -> None:
        """Close and remove the websocket connection."""
        del connection_id
        raise NotImplementedError("disconnect must be implemented by subclasses")

    async def handle_data(self, connection_id: UUID, data: dict[str, object]) -> None:
        """Handle incoming websocket payloads."""
        del connection_id, data
        raise NotImplementedError("handle_data must be implemented by subclasses")

    # ----------------------------
    # Optional WebRTC signaling
    # ----------------------------
    async def send_ice_candidate(
        self, connection_id: UUID, candidate: RTCIceCandidateInit
    ) -> None:
        """Send a WebRTC ICE candidate over the underlying transport."""
        del connection_id, candidate
        raise NotImplementedError(
            "send_ice_candidate must be implemented by subclasses"
        )

    async def handle_wrtc_connection_messages(
        self, request: WsRTCOfferRequest | WsRTCResponse, connection_id: UUID
    ) -> BaseModel | None:
        """Handle WebRTC offer/answer messages (override where supported)."""
        del request, connection_id
        raise NotImplementedError(
            "handle_wrtc_connection_messages must be implemented by subclasses"
        )

    async def handle_webrtc_request(
        self,
        request: WsRTCOfferRequest | WsRTCIceCandidateRequest | WsRTCResponse,
        connection_id: UUID,
    ) -> BaseModel | None:
        """Handle incoming WebRTC signaling messages (offer/answer + ICE)."""
        if isinstance(request, WsRTCIceCandidateRequest):
            await self.handle_webrtc_ice_candidate(request, connection_id)
            return None
        return await self.handle_wrtc_connection_messages(request, connection_id)

    async def handle_webrtc_ice_candidate(
        self, candidate: WsRTCIceCandidateRequest, connection_id: UUID
    ) -> None:
        """Handle incoming WebRTC ICE candidate."""
        logger.info("Processing WebRTC ICE candidate from %s", connection_id)
        wrtc = self.wrtc_connections.get(connection_id)
        if wrtc is None:
            raise ValueError(f"No WebRTC handler found for connection {connection_id}")
        handle = getattr(wrtc, "handle_webrtc_ice_candidate", None)
        if handle is None:
            raise NotImplementedError("WebRTC handler does not support ICE candidates")
        await handle(candidate.candidate)


__all__ = ["DuplexBase", "DuplexSide", "WS_T", "WRTC_T"]
