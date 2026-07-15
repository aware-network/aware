"""Manifest model describing per-language OCG node-to-path mappings."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OCGNodePathEntry(BaseModel):
    """Deterministic mapping from an OCG node and top-level entity to a file path."""

    node_id: str = Field(...)
    node_type: str = Field(...)
    entity_id: str = Field(...)
    relative_path: str = Field(...)


class OCGNodePathsManifest(BaseModel):
    """Bundle of node path entries for a single language."""

    language: str = Field(...)
    nodes: list[OCGNodePathEntry] = Field(default_factory=list)


__all__ = ["OCGNodePathEntry", "OCGNodePathsManifest"]
