from __future__ import annotations

# Standard
from enum import Enum


class ExternalAppStatus(Enum):
    active = "active"
    error = "error"
    inactive = "inactive"
    revoked = "revoked"
