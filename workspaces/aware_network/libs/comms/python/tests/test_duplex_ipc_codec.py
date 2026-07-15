from __future__ import annotations

from aware_comms import (
    DuplexIpcEndpoint,
    DuplexIpcFrameCodec,
    DuplexIpcTransportKind,
    DuplexMessageFrame,
    DuplexMessageFrameType,
)


def test_ipc_endpoint_stdio_factory() -> None:
    endpoint = DuplexIpcEndpoint.stdio(command=["python3", "-m", "echo"])

    assert endpoint.transport is DuplexIpcTransportKind.STDIO
    assert endpoint.command == ["python3", "-m", "echo"]
    assert endpoint.socket_path is None


def test_ipc_endpoint_unix_factory() -> None:
    endpoint = DuplexIpcEndpoint.unix_socket(socket_path="/tmp/aware.sock")

    assert endpoint.transport is DuplexIpcTransportKind.UNIX_SOCKET
    assert endpoint.socket_path == "/tmp/aware.sock"
    assert endpoint.command == []


def test_ipc_frame_codec_roundtrip() -> None:
    frame = DuplexMessageFrame(
        type=DuplexMessageFrameType.REQUEST,
        payload={"hello": "world"},
    )

    restored = DuplexIpcFrameCodec.decode_frame(DuplexIpcFrameCodec.encode_frame(frame))

    assert restored == frame


def test_ipc_frame_codec_roundtrip_preserves_legacy_data() -> None:
    frame = DuplexMessageFrame(
        type=DuplexMessageFrameType.REQUEST,
        data='{"hello":"world"}',
    )

    restored = DuplexIpcFrameCodec.decode_frame(DuplexIpcFrameCodec.encode_frame(frame))

    assert restored == frame
    assert restored.payload is None
