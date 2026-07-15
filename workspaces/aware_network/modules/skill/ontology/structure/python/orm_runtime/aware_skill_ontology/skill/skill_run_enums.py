from __future__ import annotations

# Standard
from enum import Enum


class SkillRunStatus(Enum):
    failed = "failed"
    queued = "queued"
    running = "running"
    skipped = "skipped"
    succeeded = "succeeded"
