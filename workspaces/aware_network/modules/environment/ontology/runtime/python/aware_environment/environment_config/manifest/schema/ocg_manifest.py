"""Manifest model describing canonical ObjectConfigGraph snapshot metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["OCGSnapshotManifest"]


class OCGSnapshotManifest(BaseModel):
    """Canonical OCG snapshot descriptor stored in `environment.manifest.json`.

    Attributes:
        canonical_id: UUID string identifying the canonical ObjectConfigGraph.
        hash: sha256 hash of the serialized snapshot artifact.
        semantic_hash: Stable semantic hash of the canonical OCG (graph hash).
        snapshot: Relative path to the snapshot payload (msgpack/JSON).
    """

    canonical_id: str = Field(..., description="UUID for the canonical OCG")
    hash: str = Field(..., description="sha256 hash of the snapshot contents")
    semantic_hash: str | None = Field(
        default=None,
        description="Stable semantic hash of the canonical OCG (graph hash; independent of snapshot serialization).",
    )
    snapshot: str = Field(..., description="Relative path to the OCG snapshot artifact")
