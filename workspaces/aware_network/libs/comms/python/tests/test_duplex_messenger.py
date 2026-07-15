from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from aware_comms import (
    DuplexMessenger,
    WsMessageFrame,
    WsMessageFrameType,
)


class DummySender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def __call__(self, payload: str, connection_id: UUID) -> bool:
        self.sent.append((payload, str(connection_id)))
        return True


@pytest.mark.asyncio
async def test_messenger_ack_and_response_flow() -> None:
    sender = DummySender()
    messenger = DuplexMessenger(send_data_fn=sender)
    connection_id = uuid4()
    request_id = uuid4()

    async def responder():
        await asyncio.sleep(0.01)
        ack = WsMessageFrame(
            type=WsMessageFrameType.ACK, data="{}", request_id=request_id
        )
        await messenger.recv(ack, {"result": None})
        response = WsMessageFrame(
            type=WsMessageFrameType.RESPONSE,
            data='{"result": {"value": 5}}',
            request_id=request_id,
        )
        await messenger.recv(response, {"result": {"value": 5}})

    task = asyncio.create_task(responder())
    result = await messenger.send_request(
        request_id=request_id,
        request_data='{"hello":"world"}',
        connection_id=connection_id,
    )
    await task
    assert result == {"value": 5}
    assert messenger.pending_futures == {}


@pytest.mark.asyncio
async def test_messenger_error_flow_sets_exception() -> None:
    sender = DummySender()
    messenger = DuplexMessenger(send_data_fn=sender)
    connection_id = uuid4()
    request_id = uuid4()

    async def responder():
        await asyncio.sleep(0.01)
        error_frame = WsMessageFrame(
            type=WsMessageFrameType.ERROR,
            data='{"message":"boom"}',
            request_id=request_id,
        )
        await messenger.recv(error_frame, {"message": "boom"})

    task = asyncio.create_task(responder())
    result = await messenger.send_request(
        request_id=request_id,
        request_data="{}",
        connection_id=connection_id,
    )
    await task
    assert result is None
    assert messenger.pending_futures == {}
