"""Optional WebRTC server placeholder.

The node currently routes operations over websocket; WebRTC can be introduced
later for streaming use-cases. Keep this import-safe so services can start
without the heavy WebRTC stack installed.
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


class WebRTCServer(BaseModel):
    """Import-safe WebRTC server shim."""

    send_ice_candidates_func: Callable[[RTCIceCandidateInit], Awaitable[None]]

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    async def handle_webrtc_offer(
        self, _session_description: RTCSessionDescriptionInit
    ) -> RTCSessionDescriptionInit:  # pragma: no cover
        _raise_webrtc_missing()

    async def handle_webrtc_ice_candidate(
        self, _candidate: RTCIceCandidateInit
    ) -> None:  # pragma: no cover
        _raise_webrtc_missing()

    async def close(self) -> None:  # pragma: no cover - shim
        return None
