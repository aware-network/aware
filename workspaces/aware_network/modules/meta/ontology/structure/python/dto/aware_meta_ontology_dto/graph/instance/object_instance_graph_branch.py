from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_history_ontology_dto.branch.branch import Branch
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch_relationship import (
        ObjectInstanceGraphBranchRelationship,
    )
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_lane import ObjectInstanceGraphLane


class ObjectInstanceGraphBranch(BaseModel):
    """A Meta pointer to Branch to link Lane->Commit to ObjectInstanceGraphLanes with Meta Representation at ObjectInstanceGraph level."""

    # Relationships
    branch: Branch = Field(description="Branch Identity")
    object_instance_graph_lanes: list[ObjectInstanceGraphLane] = Field(
        default_factory=list, description="Projection Lanes"
    )
    object_instance_graph_branch_relationships: list[ObjectInstanceGraphBranchRelationship] = Field(
        default_factory=list, description="Branch Relationships"
    )
