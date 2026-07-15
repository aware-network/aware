from __future__ import annotations

# Standard
from enum import Enum


class SmartContractMemberType(Enum):
    payer = "payer"
    receiver = "receiver"


class SmartContractStatus(Enum):
    active = "active"
    completed = "completed"
    paused = "paused"


class SmartContractType(Enum):
    ownership = "ownership"
    utility = "utility"
