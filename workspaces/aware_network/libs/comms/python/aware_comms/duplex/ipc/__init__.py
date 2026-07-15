"""Local IPC helpers layered over the transport-neutral duplex protocol."""

from aware_comms.duplex.ipc.codec import DuplexIpcFrameCodec
from aware_comms.duplex.ipc.models import (
    DuplexIpcEndpoint,
    DuplexIpcTransportKind,
)
from aware_comms.duplex.ipc.stdio import StdioDuplexIpcClient
from aware_comms.duplex.ipc.unix import (
    DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES,
    UnixSocketDuplexClient,
    UnixSocketDuplexServer,
)

__all__ = [
    "DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES",
    "DuplexIpcEndpoint",
    "DuplexIpcFrameCodec",
    "DuplexIpcTransportKind",
    "StdioDuplexIpcClient",
    "UnixSocketDuplexClient",
    "UnixSocketDuplexServer",
]
