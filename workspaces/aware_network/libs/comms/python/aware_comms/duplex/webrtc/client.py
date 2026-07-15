"""Optional WebRTC client placeholder.

The canonical websocket protocol does not require WebRTC. This module exists so
internal services can import WebRTC symbols without pulling in heavy
dependencies in minimal installs.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import ClassVar, NoReturn

from pydantic import BaseModel, ConfigDict

from aware_comms.duplex.webrtc.models import (
    RTCIceCandidateInit,
    RTCSessionDescriptionInit,
)


def _raise_webrtc_missing() -> NoReturn:
    raise RuntimeError(
        "WebRTC support is not installed. Install `aiortc` (or `aware-comms[webrtc]` once defined) to enable it."
    )


class WebRTCClient(BaseModel):
    """Import-safe WebRTC client shim.

    When WebRTC dependencies are missing, methods raise a clear runtime error.
    """

    send_ice_candidates_func: Callable[[RTCIceCandidateInit], Awaitable[None]]
    local_track: object | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    async def create_offer(
        self,
    ) -> RTCSessionDescriptionInit:  # pragma: no cover - shim
        _raise_webrtc_missing()

    async def handle_webrtc_response(
        self, _session_description: RTCSessionDescriptionInit
    ) -> None:  # pragma: no cover
        _raise_webrtc_missing()

    async def handle_webrtc_ice_candidate(
        self, _candidate: RTCIceCandidateInit
    ) -> None:  # pragma: no cover
        _raise_webrtc_missing()

    async def close(self) -> None:  # pragma: no cover - shim
        return None
