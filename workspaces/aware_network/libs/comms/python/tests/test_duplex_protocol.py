from __future__ import annotations

from aware_comms import (
    DuplexMessageFrame,
    DuplexMessageFrameType,
    WsMessageFrame,
    WsMessageFrameType,
)


def test_duplex_message_frame_roundtrip() -> None:
    frame = DuplexMessageFrame(
        type=DuplexMessageFrameType.REQUEST,
        payload={"ping": "pong"},
    )

    restored = DuplexMessageFrame.model_validate(frame.model_dump())

    assert restored.type is DuplexMessageFrameType.REQUEST
    assert restored.payload == {"ping": "pong"}
    assert restored.data == ""
    assert restored.request_id is None


def test_duplex_message_frame_preserves_legacy_data() -> None:
    frame = DuplexMessageFrame(
        type=DuplexMessageFrameType.REQUEST,
        data='{"ping":"pong"}',
    )

    restored = DuplexMessageFrame.model_validate(frame.model_dump())

    assert restored.type is DuplexMessageFrameType.REQUEST
    assert restored.data == '{"ping":"pong"}'
    assert restored.payload is None


def test_websocket_frame_alias_uses_duplex_contract() -> None:
    frame = WsMessageFrame(
        type=WsMessageFrameType.NOTIFICATION,
        payload={"ready": True},
    )

    assert isinstance(frame, DuplexMessageFrame)
    assert frame.type is DuplexMessageFrameType.NOTIFICATION
    assert frame.model_dump()["type"] == "notification"
    assert frame.payload == {"ready": True}
