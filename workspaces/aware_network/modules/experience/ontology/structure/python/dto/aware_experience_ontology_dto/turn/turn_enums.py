from __future__ import annotations

# Standard
from enum import Enum


class TurnExecutionState(Enum):
    accepted = "accepted"
    running = "running"
    terminal = "terminal"


class TurnExecutionTerminalStatus(Enum):
    cancelled = "cancelled"
    dead_letter = "dead_letter"
    failed = "failed"
    skipped = "skipped"
    succeeded = "succeeded"
