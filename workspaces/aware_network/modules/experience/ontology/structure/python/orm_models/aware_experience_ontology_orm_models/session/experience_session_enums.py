from __future__ import annotations

# Standard
from enum import Enum


class ExperienceSessionState(Enum):
    active = "active"
    suspended = "suspended"
    closed = "closed"
