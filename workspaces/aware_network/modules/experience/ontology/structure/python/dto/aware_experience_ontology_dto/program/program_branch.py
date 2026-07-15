from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ProgramBranch(BaseModel):
    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    view_key: str | None = Field(default=None)
