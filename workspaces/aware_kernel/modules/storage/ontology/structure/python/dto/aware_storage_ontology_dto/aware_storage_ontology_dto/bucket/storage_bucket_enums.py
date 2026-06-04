from __future__ import annotations

# Standard
from enum import Enum


class StorageBackend(Enum):
    azure = "azure"
    gcs = "gcs"
    local = "local"
    memory = "memory"
    s3 = "s3"
