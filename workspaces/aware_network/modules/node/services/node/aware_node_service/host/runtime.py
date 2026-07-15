from __future__ import annotations

import asyncio
import contextlib
import os
from time import monotonic
from typing import TYPE_CHECKING

import uvicorn

if TYPE_CHECKING:
    from aware_node_service.app import NetworkNodeApp


async def serve_node_runtime(
    *, node_app: "NetworkNodeApp", host: str, port: int
) -> None:
    app = node_app.create_app()
    server = uvicorn.Server(
        uvicorn.Config(
            app=app,
            host=host,
            port=port,
        )
    )
    serve_task = asyncio.create_task(server.serve())

    try:
        await wait_for_local_port_ready(
            port=port, timeout_s=float(os.getenv("AWARE_NODE_BOOT_TIMEOUT_S", "30"))
        )
        await serve_task
    finally:
        if not serve_task.done():
            serve_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await serve_task


async def wait_for_local_port_ready(*, port: int, timeout_s: float) -> None:
    deadline = monotonic() + max(timeout_s, 1.0)
    while monotonic() < deadline:
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(
                b"GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
            )
            await writer.drain()
            head = await reader.read(128)
            writer.close()
            await writer.wait_closed()
            if b"200" in head.split(b"\r\n", 1)[0]:
                return
        except Exception:
            await asyncio.sleep(0.2)
    raise TimeoutError(
        f"Node HTTP server did not become ready on http://127.0.0.1:{port}/health within {timeout_s:.1f}s"
    )


__all__ = [
    "serve_node_runtime",
    "wait_for_local_port_ready",
]
