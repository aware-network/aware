from __future__ import annotations

# Standard
from enum import Enum


class WindowActiveLayoutMode(Enum):
    follow_thread_active = "follow_thread_active"
    pinned = "pinned"
    override = "override"
