"""Manifest model describing per-language overlay snapshot metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["OverlayManifest"]


class OverlayManifest(BaseModel):
    """Metadata for a single language overlay payload."""

    language: str = Field(..., description="CodeLanguage value for the overlay")
    file: str = Field(..., description="Relative path to overlay artifact")
    hash: str = Field(..., description="sha256 hash of the overlay contents")
    source: str | None = Field(
        default=None,
        description="Optional original path (e.g., .aware/overlays/<id>/CodeLanguage.X.json)",
    )
