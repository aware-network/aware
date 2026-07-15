"""Deprecated duplex base module (compatibility wrapper).

`aware_network.communications.duplex` historically owned the duplex base types.
The canonical transport primitives now live in `aware_comms` so both public SDKs
and internal services share a single implementation.
"""

from aware_comms.duplex.base import DuplexBase as NetworkDuplexBase
from aware_comms.duplex.base import DuplexSide, WS_T, WRTC_T
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
    "DuplexSide",
    "NetworkDuplexBase",
    "RTCIceCandidateInit",
    "RTCSessionDescriptionInit",
    "WS_T",
    "WRTC_T",
    "WebRTCClient",
    "WebRTCServer",
    "WsRTCIceCandidateRequest",
    "WsRTCOfferRequest",
    "WsRTCResponse",
]
