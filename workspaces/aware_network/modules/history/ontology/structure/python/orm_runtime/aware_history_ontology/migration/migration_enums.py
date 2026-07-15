from __future__ import annotations

# Standard
from enum import Enum


class MigrationStatus(Enum):
    applied = "applied"
    failed = "failed"
    pending = "pending"
    validated = "validated"
