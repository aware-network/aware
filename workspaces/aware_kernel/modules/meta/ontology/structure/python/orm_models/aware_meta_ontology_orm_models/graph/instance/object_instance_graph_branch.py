from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.branch.branch import Branch
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch_relationship import (
        ObjectInstanceGraphBranchRelationship,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_lane import ObjectInstanceGraphLane


class ObjectInstanceGraphBranch(ORMModel):
    """A Meta pointer to Branch to link Lane->Commit to ObjectInstanceGraphLanes with Meta Representation at ObjectInstanceGraph level."""

    # Relationships
    branch: Branch = Field(description="Branch Identity")
    object_instance_graph_lanes: list[ObjectInstanceGraphLane] = Field(
        default_factory=list, description="Projection Lanes"
    )
    object_instance_graph_branch_relationships: list[ObjectInstanceGraphBranchRelationship] = Field(
        default_factory=list, description="Branch Relationships"
    )

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_branches"
    )
    branch_id: UUID | None = Field(default=None, description="Foreign key for ObjectInstanceGraphBranch.branch")
