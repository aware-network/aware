from __future__ import annotations

# Standard
from enum import Enum


class ApiViewStreamMode(Enum):
    snapshot = "snapshot"
    snapshot_delta = "snapshot_delta"
    live = "live"
