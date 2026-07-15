from pydantic import BaseModel
from typing import Literal, Optional


class WsMessageAck(BaseModel):
    """Used to acknowledge the receipt of a request"""

    details: Optional[str] = None


class WsMessageError(BaseModel):
    """Used to indicate an error occurred during request processing"""

    type: Literal["invalid_message", "authentication", "disconnected", "http", "unexpected"]
    message: str


class WsMessageStandardResponse(BaseModel):
    """Used to indicate a standard response to a request"""

    details: Optional[str] = None
    error: Optional[str] = None
