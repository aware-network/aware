"""Manifest models describing GraphSQL plan metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["GraphSQLManifest"]


class GraphSQLManifest(BaseModel):
    """Metadata for a single GraphSQL plan artifact."""

    file: str = Field(
        ...,
        description="Relative path to the plan artifact when available",
    )
    hash: str = Field(..., description="sha256 hash for the plan artifact")
    status: str = Field(
        default="missing",
        description="Plan availability status (e.g., missing, ready)",
    )
