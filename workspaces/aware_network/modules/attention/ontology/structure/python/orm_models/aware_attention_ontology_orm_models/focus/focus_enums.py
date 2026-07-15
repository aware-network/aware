from __future__ import annotations

# Standard
from enum import Enum


class FocusScopeRequestStatus(Enum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"
    rejected = "rejected"
