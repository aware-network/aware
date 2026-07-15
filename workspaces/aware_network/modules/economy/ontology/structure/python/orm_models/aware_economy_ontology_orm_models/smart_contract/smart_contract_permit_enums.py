from __future__ import annotations

# Standard
from enum import Enum


class SmartContractPermitStatus(Enum):
    active = "active"
    expired = "expired"
    paused = "paused"
    revoked = "revoked"
