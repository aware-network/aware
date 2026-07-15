"""Manifest model describing per-language OCG node -> path mappings.

SSOT: emitted by materialization stages to make cross-package imports deterministic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["OCGNodePathEntry", "OCGNodePathsManifest"]


class OCGNodePathEntry(BaseModel):
    """
    Deterministic mapping from an OCG *node* (and its top-level entity) to a relative path.

    Notes:
    - Graph/ORM agnostic: no code sections, no code_id.
    - Path is relative to the language package root (e.g. for Dart: inside `lib/` without the prefix).
    """

    node_id: str = Field(..., description="ObjectConfigGraphNode UUID")
    node_type: str = Field(..., description="ObjectConfigGraphNodeType value")
    entity_id: str = Field(
        ..., description="Top-level entity UUID (ClassConfig/EnumConfig/FunctionConfig)"
    )
    relative_path: str = Field(
        ..., description="Relative path (POSIX) to the owning file"
    )


class OCGNodePathsManifest(BaseModel):
    """Bundle of node path entries for a single language."""

    language: str = Field(..., description="CodeLanguage value")
    nodes: list[OCGNodePathEntry] = Field(default_factory=list)
