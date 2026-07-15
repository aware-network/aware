"""Manifest model describing ObjectProjectionGraph index entries."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["OPGIndexEntry", "OPGIndexManifest"]


class OPGIndexEntry(BaseModel):
    """Single OPG entry keyed by projection hash."""

    model: str = Field(..., description="Fully qualified model name (module.Class)")
    projection_hash: str = Field(..., description="Projection hash for the OPG")
    file: str = Field(..., description="Relative path to the serialized OPG file")


class OPGIndexManifest(BaseModel):
    """Collection of OPG index entries."""

    file: str = Field(..., description="Relative path to index file")
    entries: list[OPGIndexEntry] = Field(default_factory=list)
