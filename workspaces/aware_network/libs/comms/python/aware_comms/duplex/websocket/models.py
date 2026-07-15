"""Compatibility models for websocket transport over the duplex protocol."""

from __future__ import annotations

from pydantic import BaseModel, Field

from aware_comms.duplex.protocol import (
    DuplexMessageFrame,
    DuplexMessageFrameType,
)


WsMessageFrameType = DuplexMessageFrameType
WsMessageFrame = DuplexMessageFrame


class WsConnectionConfig(BaseModel):
    """Configuration describing how two applications connect via websocket."""

    requires_auth: bool = Field(default=False)
    enable_ws: bool = Field(default=True)
    enable_webrtc: bool = Field(default=False)
    internal: bool = Field(default=True)


__all__ = ["WsConnectionConfig", "WsMessageFrame", "WsMessageFrameType"]
