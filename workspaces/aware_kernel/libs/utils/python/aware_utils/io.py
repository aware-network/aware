"""IO helpers shared by Aware tooling modules."""

from __future__ import annotations

from pathlib import Path

__all__ = ["ensure_directory"]


def ensure_directory(path: Path) -> Path:
    """Ensure `path` exists and return it."""

    path.mkdir(parents=True, exist_ok=True)
    return path
