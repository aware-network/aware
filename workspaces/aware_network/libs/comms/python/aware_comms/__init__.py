"""Public communications utilities for AWARE clients.

`aware_comms` owns raw websocket/duplex/IPC transport primitives only. Product
DTOs live in their generated API/service packages and should be imported there.
"""

from __future__ import annotations

from aware_comms.duplex.websocket.models import (
    WsMessageFrameType,
    WsMessageFrame,
    WsConnectionConfig,
)
from aware_comms.duplex.protocol import (
    DuplexMessageFrameType,
    DuplexMessageFrame,
)
from aware_comms.duplex.ipc import (
    DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES,
    DuplexIpcEndpoint,
    DuplexIpcFrameCodec,
    DuplexIpcTransportKind,
    StdioDuplexIpcClient,
    UnixSocketDuplexClient,
    UnixSocketDuplexServer,
)
from aware_comms.duplex.websocket.registry import (
    WsConnection,
    WsConnectionRegistry,
    ws_registry,
)
from aware_comms.duplex.base import DuplexSide, DuplexBase
from aware_comms.duplex.messenger import (
    DuplexMessenger,
    DuplexFuture,
    DuplexFutureStatus,
)
from aware_comms.duplex.duplex import Duplex
from aware_comms.duplex.client import DuplexClient

__all__ = [
    "DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES",
    "DuplexIpcEndpoint",
    "DuplexIpcFrameCodec",
    "DuplexIpcTransportKind",
    "StdioDuplexIpcClient",
    "UnixSocketDuplexClient",
    "UnixSocketDuplexServer",
    "DuplexMessageFrameType",
    "DuplexMessageFrame",
    "WsMessageFrameType",
    "WsMessageFrame",
    "WsConnectionConfig",
    "WsConnection",
    "WsConnectionRegistry",
    "ws_registry",
    "DuplexMessenger",
    "DuplexFuture",
    "DuplexFutureStatus",
    "DuplexBase",
    "DuplexSide",
    "Duplex",
    "DuplexClient",
]
