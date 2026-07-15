from __future__ import annotations

# Standard
from enum import Enum


class ActorFocusLevelType(Enum):
    """Coarse actor-facing attention priority bucket."""

    critical = "critical"
    high = "high"
    low = "low"
    medium = "medium"
    none = "none"


class ActorFocusRequestStatus(Enum):
    accepted = "accepted"
    expired = "expired"
    pending = "pending"
    rejected = "rejected"
