from __future__ import annotations

# Standard
from enum import Enum


class MemoryWorkingItemKind(Enum):
    attention = "attention"
    content = "content"
    event = "event"
    tool = "tool"
