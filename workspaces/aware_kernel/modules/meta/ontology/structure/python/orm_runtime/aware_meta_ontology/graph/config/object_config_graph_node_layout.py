from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class ObjectConfigGraphNodeLayout(ORMModel):
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

    # Foreign Keys
    object_config_graph_node_id: UUID = Field(description="Foreign key for ObjectConfigGraphNode.layouts")


FUNCTIONS = {
    "ObjectConfigGraphNodeLayout": {},
}

__all__ = [
    "ObjectConfigGraphNodeLayout",
    "FUNCTIONS",
]
