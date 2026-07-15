from __future__ import annotations

from pathlib import Path

import pytest

from aware_comms import (
    DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES,
    DuplexIpcEndpoint,
    DuplexMessageFrame,
    DuplexMessageFrameType,
    UnixSocketDuplexClient,
    UnixSocketDuplexServer,
)


def test_unix_ipc_default_frame_limit_supports_workspace_materialize_deltas() -> None:
    assert DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES >= 64 * 1024 * 1024


@pytest.mark.asyncio
async def test_unix_ipc_roundtrip(tmp_path: Path) -> None:
    socket_path = tmp_path / "aware-comms.sock"
    endpoint = DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))

    async def handle_frame(frame: DuplexMessageFrame) -> DuplexMessageFrame:
        return DuplexMessageFrame(
            type=DuplexMessageFrameType.RESPONSE,
            payload=frame.payload,
            request_id=frame.id,
        )

    server = UnixSocketDuplexServer(
        endpoint=endpoint,
        handle_frame=handle_frame,
    )
    client = UnixSocketDuplexClient(endpoint=endpoint)

    await server.start()
    try:
        request = DuplexMessageFrame(
            type=DuplexMessageFrameType.REQUEST,
            payload={"value": 5},
        )
        response = await client.send_and_receive(request, timeout_s=2.0)
    finally:
        await client.close()
        await server.close()

    assert response.type is DuplexMessageFrameType.RESPONSE
    assert response.request_id == request.id
    assert response.payload == {"value": 5}
    assert response.data == ""


@pytest.mark.asyncio
async def test_unix_ipc_roundtrip_allows_large_single_frame(tmp_path: Path) -> None:
    socket_path = tmp_path / "aware-comms-large.sock"
    endpoint = DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))
    payload = "x" * (128 * 1024)

    async def handle_frame(frame: DuplexMessageFrame) -> DuplexMessageFrame:
        return DuplexMessageFrame(
            type=DuplexMessageFrameType.RESPONSE,
            data=frame.data,
            request_id=frame.id,
        )

    server = UnixSocketDuplexServer(
        endpoint=endpoint,
        handle_frame=handle_frame,
    )
    client = UnixSocketDuplexClient(endpoint=endpoint)

    await server.start()
    try:
        request = DuplexMessageFrame(
            type=DuplexMessageFrameType.REQUEST,
            data=payload,
        )
        response = await client.send_and_receive(request, timeout_s=2.0)
    finally:
        await client.close()
        await server.close()

    assert response.type is DuplexMessageFrameType.RESPONSE
    assert response.request_id == request.id
    assert response.data == payload
