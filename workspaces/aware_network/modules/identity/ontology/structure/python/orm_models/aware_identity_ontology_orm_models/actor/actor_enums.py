from __future__ import annotations

# Standard
from enum import Enum


class ActorType(Enum):
    agent_process_thread = "agent_process_thread"
    human = "human"
    organization = "organization"
    system = "system"
