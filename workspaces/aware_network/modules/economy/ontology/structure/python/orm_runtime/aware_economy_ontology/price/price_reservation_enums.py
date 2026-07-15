from __future__ import annotations

# Standard
from enum import Enum


class PriceReservationStatus(Enum):
    cancelled = "cancelled"
    reserved = "reserved"
    settled = "settled"
