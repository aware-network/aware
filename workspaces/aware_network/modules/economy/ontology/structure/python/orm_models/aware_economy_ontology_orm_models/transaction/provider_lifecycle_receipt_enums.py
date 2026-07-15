from __future__ import annotations

# Standard
from enum import Enum


class ProviderLifecycleEventKind(Enum):
    chargeback = "chargeback"
    dispute = "dispute"
    dispute_release = "dispute_release"
    refund = "refund"


class ProviderLifecycleStatus(Enum):
    applied = "applied"
    held = "held"
    released = "released"
