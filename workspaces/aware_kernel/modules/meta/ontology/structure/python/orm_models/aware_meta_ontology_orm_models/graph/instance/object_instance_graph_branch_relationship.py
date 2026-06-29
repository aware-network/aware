from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ObjectInstanceGraphBranchRelationship(ORMModel):
    # Relationships
    target_object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Foreign Keys
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphBranch.object_instance_graph_branch_relationships"
    )
    target_object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphBranchRelationship.target_object_instance_graph_branch"
    )
