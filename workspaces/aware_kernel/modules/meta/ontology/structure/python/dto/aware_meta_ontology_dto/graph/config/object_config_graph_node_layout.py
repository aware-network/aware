from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ObjectConfigGraphNodeLayout(BaseModel):
    """
    Layout metadata for an ObjectConfigGraphNode.
    This keeps canonical ordering + file placement deterministic without
    coupling OCGs to code sections.
    """

    # Attributes
    layout_kind: str = Field(default="aware", description='Layout kind identifier (canonical default: "aware").')
    relative_path: str = Field(description="Relative path within the canonical source layout (POSIX).")
    source_position: int | None = Field(
        default=None, description="Optional byte offset within the source file for deterministic ordering."
    )
