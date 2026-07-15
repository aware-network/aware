from __future__ import annotations

# Standard
from enum import Enum


class PriorityLevel(Enum):
    critical = "critical"
    high = "high"
    low = "low"
    medium = "medium"
    urgent = "urgent"
