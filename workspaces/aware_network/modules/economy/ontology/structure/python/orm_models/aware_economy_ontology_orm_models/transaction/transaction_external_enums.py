from __future__ import annotations

# Standard
from enum import Enum


class TransactionExternalStatus(Enum):
    disputed = "disputed"
    ignored = "ignored"
    processed = "processed"
    refunded = "refunded"
