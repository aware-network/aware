from __future__ import annotations

# Standard
from enum import Enum


class ReservationStatus(Enum):
    cancelled = "cancelled"
    executed = "executed"
    expired = "expired"
    pending = "pending"
    settled = "settled"
