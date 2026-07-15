from __future__ import annotations

import sys

import pytest

from aware_comms import (
    DuplexIpcEndpoint,
    DuplexMessageFrame,
    DuplexMessageFrameType,
    StdioDuplexIpcClient,
)


@pytest.mark.asyncio
async def test_stdio_ipc_client_roundtrip() -> None:
    endpoint = DuplexIpcEndpoint.stdio(
        command=[
            sys.executable,
            "-c",
            (
                "import sys\n"
                "for line in sys.stdin:\n"
                "    sys.stdout.write(line)\n"
                "    sys.stdout.flush()\n"
            ),
        ]
    )
    client = StdioDuplexIpcClient(endpoint=endpoint)

    try:
        frame = DuplexMessageFrame(
            type=DuplexMessageFrameType.NOTIFICATION,
            data='{"ready":true}',
        )
        response = await client.send_and_receive(frame, timeout_s=2.0)
    finally:
        await client.close()

    assert response == frame
