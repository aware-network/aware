from __future__ import annotations

# Standard
from enum import Enum


class ProcessStatus(Enum):
    cancelled = "cancelled"
    finished_failed = "finished_failed"
    finished_succeeded = "finished_succeeded"
    initializing = "initializing"
    paused = "paused"
    pending = "pending"
    running = "running"
    terminated = "terminated"
    terminating = "terminating"
