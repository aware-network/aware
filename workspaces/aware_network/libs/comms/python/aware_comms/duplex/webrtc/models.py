"""Pydantic models for optional WebRTC signaling."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RTCSessionDescriptionInit(BaseModel):
    sdp: str
    type: Literal["offer", "answer", "pranswer", "rollback"]


class RTCIceCandidateInit(BaseModel):
    candidate: str
    sdpMid: str | None = None
    sdpMLineIndex: int | None = None
    usernameFragment: str | None = None


class WsRTCIceCandidateRequest(BaseModel):
    """Bidirectional message for ICE candidates (client/server)."""

    candidate: RTCIceCandidateInit


class WsRTCOfferRequest(BaseModel):
    offer_session_description: RTCSessionDescriptionInit


class WsRTCResponse(BaseModel):
    answer_session_description: RTCSessionDescriptionInit


__all__ = [
    "RTCIceCandidateInit",
    "RTCSessionDescriptionInit",
    "WsRTCIceCandidateRequest",
    "WsRTCOfferRequest",
    "WsRTCResponse",
]
