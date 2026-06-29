from __future__ import annotations

# Standard
from enum import Enum


class ApiCallOutcomeStatus(Enum):
    failed = "failed"
    succeeded = "succeeded"
