from __future__ import annotations

# Standard
from enum import Enum


class IdentityType(Enum):
    agent = "agent"
    human = "human"
    organization = "organization"
    system = "system"
