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


class ObjectInstanceGraphBranchRelationship(BaseModel):
    # Relationships
    target_object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
