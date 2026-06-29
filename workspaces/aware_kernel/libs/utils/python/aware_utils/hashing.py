"""Hash validation helpers for manifest artifacts."""

# @doc-ref: ../../docs/validation.md
# @test-ref: ../../tests/test_validation_hashes.py

from __future__ import annotations

import hashlib
from pathlib import Path

__all__ = ["calculate_sha256", "calculate_sha256_bytes"]


def calculate_sha256(path: Path) -> str:
    """Return the sha256 digest for `path`."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def calculate_sha256_bytes(payload: bytes) -> str:
    """Return the sha256 digest for in-memory payload."""

    digest = hashlib.sha256(payload)
    return f"sha256:{digest.hexdigest()}"
