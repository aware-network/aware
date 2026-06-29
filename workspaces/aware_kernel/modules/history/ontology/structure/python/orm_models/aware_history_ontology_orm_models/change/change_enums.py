from __future__ import annotations

# Standard
from enum import Enum


class ChangeDeltaKind(Enum):
    scalar_set = "scalar_set"
    text_patch = "text_patch"


class ChangeType(Enum):
    create = "create"
    delete = "delete"
    update = "update"
