from __future__ import annotations

# Standard
from enum import Enum


class CommitStatus(Enum):
    applied = "applied"
    conflicted = "conflicted"
    local = "local"
    pending_sync = "pending_sync"
    rejected = "rejected"
