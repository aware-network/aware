"""Transport-neutral duplex protocol models."""

from __future__ import annotations

from enum import Enum
from typing import TypeAlias
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

JsonValue: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    # Keep the transport alias deliberately shallow; service DTOs validate
    # concrete payloads at their own boundary.
    | list[object]
    | dict[str, object]
)


class DuplexMessageFrameType(str, Enum):
    """Frame types supported by the transport-neutral duplex protocol."""

    REQUEST = "request"
    RESPONSE = "response"
    ACK = "ack"
    ERROR = "error"
    NOTIFICATION = "notification"


class DuplexMessageFrame(BaseModel):
    """Envelope for duplex messages independent of the concrete transport."""

    id: UUID = Field(default_factory=uuid4)
    type: DuplexMessageFrameType
    data: str = ""
    payload: JsonValue = None
    request_id: UUID | None = None


__all__ = ["DuplexMessageFrame", "DuplexMessageFrameType", "JsonValue"]
