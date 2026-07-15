from __future__ import annotations

# Standard
from enum import Enum


class ConnectionRequestStatus(Enum):
    accepted = "accepted"
    pending = "pending"
    rejected = "rejected"
