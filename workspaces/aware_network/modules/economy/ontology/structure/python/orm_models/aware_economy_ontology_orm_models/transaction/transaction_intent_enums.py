from __future__ import annotations

# Standard
from enum import Enum


class TransactionIntentStatus(Enum):
    canceled = "canceled"
    confirmed = "confirmed"
    created = "created"
    pending = "pending"
