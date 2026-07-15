"""Optional WebRTC helpers for aware-comms.

The websocket protocol is the default transport; WebRTC support is provided as
best-effort helpers that remain importable even when heavy dependencies (aiortc)
are not installed.
"""

from aware_comms.duplex.webrtc.client import WebRTCClient
from aware_comms.duplex.webrtc.models import (
    RTCIceCandidateInit,
    RTCSessionDescriptionInit,
    WsRTCIceCandidateRequest,
    WsRTCOfferRequest,
    WsRTCResponse,
)
from aware_comms.duplex.webrtc.server import WebRTCServer

__all__ = [
    "RTCIceCandidateInit",
    "RTCSessionDescriptionInit",
    "WsRTCIceCandidateRequest",
    "WsRTCOfferRequest",
    "WsRTCResponse",
    "WebRTCClient",
    "WebRTCServer",
]
