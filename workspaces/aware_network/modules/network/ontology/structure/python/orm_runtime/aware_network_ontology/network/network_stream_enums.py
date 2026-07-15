from __future__ import annotations

# Standard
from enum import Enum


class NetworkStreamControl(Enum):
    close = "close"
    data = "data"
    heartbeat = "heartbeat"
