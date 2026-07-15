from __future__ import annotations

# Standard
from enum import Enum


class ContentPackageArtifactStatus(Enum):
    available = "available"
    missing = "missing"
    stale = "stale"
    optional = "optional"
    failed = "failed"
