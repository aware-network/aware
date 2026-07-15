"""Line-oriented frame codec for local IPC transports."""

from __future__ import annotations

import json
from typing import cast

from aware_comms.duplex.protocol import DuplexMessageFrame


class DuplexIpcFrameCodec:
    """Encode and decode newline-delimited duplex frames."""

    @staticmethod
    def encode_frame(frame: DuplexMessageFrame) -> bytes:
        return (frame.model_dump_json() + "\n").encode("utf-8")

    @staticmethod
    def decode_frame(payload: bytes | str) -> DuplexMessageFrame:
        raw = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        line = raw.strip()
        if not line:
            raise ValueError("IPC frame payload is empty")
        data = cast(object, json.loads(line))
        if not isinstance(data, dict):
            raise ValueError("IPC frame payload must decode to an object")
        return DuplexMessageFrame.model_validate(data)


__all__ = ["DuplexIpcFrameCodec"]
