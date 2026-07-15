"""Unix-domain socket transport for duplex IPC."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from aware_comms.duplex.ipc.codec import DuplexIpcFrameCodec
from aware_comms.duplex.ipc.models import (
    DuplexIpcEndpoint,
    DuplexIpcTransportKind,
)
from aware_comms.duplex.protocol import DuplexMessageFrame

FrameHandler = Callable[
    [DuplexMessageFrame],
    Awaitable[DuplexMessageFrame | None],
]

DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES = 64 * 1024 * 1024


class UnixSocketDuplexServer:
    """Minimal newline-delimited duplex server over a Unix-domain socket."""

    def __init__(
        self,
        *,
        endpoint: DuplexIpcEndpoint,
        handle_frame: FrameHandler,
    ) -> None:
        if endpoint.transport is not DuplexIpcTransportKind.UNIX_SOCKET:
            raise ValueError("UnixSocketDuplexServer requires a unix_socket endpoint")
        self._endpoint: DuplexIpcEndpoint = endpoint
        self._handle_frame: FrameHandler = handle_frame
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        if self._server is not None:
            return
        socket_path = Path(self._endpoint.socket_path or "")
        socket_path.parent.mkdir(parents=True, exist_ok=True)
        if socket_path.exists():
            socket_path.unlink()
        self._server = await asyncio.start_unix_server(
            self._handle_connection,
            path=str(socket_path),
            limit=DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES,
        )

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        socket_path = Path(self._endpoint.socket_path or "")
        if socket_path.exists():
            socket_path.unlink()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                frame = DuplexIpcFrameCodec.decode_frame(line)
                response = await self._handle_frame(frame)
                if response is not None:
                    writer.write(DuplexIpcFrameCodec.encode_frame(response))
                    await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


class UnixSocketDuplexClient:
    """Minimal newline-delimited duplex client over a Unix-domain socket."""

    def __init__(self, *, endpoint: DuplexIpcEndpoint) -> None:
        if endpoint.transport is not DuplexIpcTransportKind.UNIX_SOCKET:
            raise ValueError("UnixSocketDuplexClient requires a unix_socket endpoint")
        self._endpoint: DuplexIpcEndpoint = endpoint
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        if self._reader is not None and self._writer is not None:
            return
        self._reader, self._writer = await asyncio.open_unix_connection(
            path=self._endpoint.socket_path or "",
            limit=DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES,
        )

    async def send_frame(self, frame: DuplexMessageFrame) -> None:
        await self.connect()
        writer = self._require_writer()
        writer.write(DuplexIpcFrameCodec.encode_frame(frame))
        await writer.drain()

    async def read_frame(
        self,
        *,
        timeout_s: float | None = None,
    ) -> DuplexMessageFrame:
        await self.connect()
        reader = self._require_reader()
        line = await asyncio.wait_for(reader.readline(), timeout=timeout_s)
        if not line:
            raise RuntimeError("unix IPC socket closed")
        return DuplexIpcFrameCodec.decode_frame(line)

    async def send_and_receive(
        self,
        frame: DuplexMessageFrame,
        *,
        timeout_s: float | None = None,
    ) -> DuplexMessageFrame:
        await self.send_frame(frame)
        return await self.read_frame(timeout_s=timeout_s)

    async def close(self) -> None:
        writer = self._writer
        if writer is None:
            return
        writer.close()
        await writer.wait_closed()
        self._reader = None
        self._writer = None

    def _require_reader(self) -> asyncio.StreamReader:
        if self._reader is None:
            raise RuntimeError("unix IPC client is not connected")
        return self._reader

    def _require_writer(self) -> asyncio.StreamWriter:
        if self._writer is None:
            raise RuntimeError("unix IPC client is not connected")
        return self._writer


__all__ = [
    "DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES",
    "UnixSocketDuplexClient",
    "UnixSocketDuplexServer",
]
