"""Process stdio transport for duplex IPC."""

from __future__ import annotations

import asyncio
from asyncio.subprocess import Process

from aware_comms.duplex.ipc.codec import DuplexIpcFrameCodec
from aware_comms.duplex.ipc.models import (
    DuplexIpcEndpoint,
    DuplexIpcTransportKind,
)
from aware_comms.duplex.protocol import DuplexMessageFrame


class StdioDuplexIpcClient:
    """Local subprocess IPC client using newline-delimited duplex frames."""

    def __init__(self, *, endpoint: DuplexIpcEndpoint) -> None:
        if endpoint.transport is not DuplexIpcTransportKind.STDIO:
            raise ValueError("StdioDuplexIpcClient requires a stdio endpoint")
        self._endpoint: DuplexIpcEndpoint = endpoint
        self._process: Process | None = None
        self._stderr_task: asyncio.Task[bytes] | None = None

    async def start(self) -> None:
        if self._process is not None:
            return
        self._process = await asyncio.create_subprocess_exec(
            *self._endpoint.command,
            cwd=self._endpoint.working_directory,
            env=self._endpoint.environment or None,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stderr = self._process.stderr
        if stderr is not None:
            self._stderr_task = asyncio.create_task(stderr.read())

    async def send_frame(self, frame: DuplexMessageFrame) -> None:
        await self.start()
        process = self._require_process()
        stdin = process.stdin
        if stdin is None:
            raise RuntimeError("stdio IPC process has no stdin")
        stdin.write(DuplexIpcFrameCodec.encode_frame(frame))
        await stdin.drain()

    async def read_frame(
        self,
        *,
        timeout_s: float | None = None,
    ) -> DuplexMessageFrame:
        await self.start()
        process = self._require_process()
        stdout = process.stdout
        if stdout is None:
            raise RuntimeError("stdio IPC process has no stdout")
        line = await asyncio.wait_for(stdout.readline(), timeout=timeout_s)
        if not line:
            raise RuntimeError("stdio IPC process closed stdout")
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
        process = self._process
        if process is None:
            return

        stdin = process.stdin
        if stdin is not None and not stdin.is_closing():
            stdin.close()
            await stdin.wait_closed()

        if process.returncode is None:
            process.terminate()
        _ = await process.wait()

        if self._stderr_task is not None:
            await self._stderr_task

        self._stderr_task = None
        self._process = None

    def _require_process(self) -> Process:
        if self._process is None:
            raise RuntimeError("stdio IPC process is not started")
        return self._process


__all__ = ["StdioDuplexIpcClient"]
