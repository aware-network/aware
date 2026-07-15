from __future__ import annotations

# Standard
from enum import Enum


class AccessLevelType(Enum):
    admin = "admin"
    read = "read"
    write = "write"


class VisibilityType(Enum):
    private = "private"
    public = "public"
