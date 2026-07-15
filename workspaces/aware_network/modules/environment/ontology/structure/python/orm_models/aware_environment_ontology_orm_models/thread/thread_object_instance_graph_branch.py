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
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class ThreadObjectInstanceGraphBranch(ORMModel):
    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(
        default=None,
        exclude=True,
        description="Cross-OPG: target lane branch id for resolving `object_instance_graph_branch`.\nWhy:\n- `object_instance_graph_branch_id` (OIGB id) is stable but not invertible, so the UI\ncannot derive the OIGI lane branch id from it.\n- Runtime sets this from the domain lane HEAD `object_instance_graph_id` (commit-first).\nHard rule:\n- This must never encode `projection_hash` (internal lane coordinate).",
    )

    # Attributes
    is_active: bool = Field(default=True)
    title: str | None = Field(default=None)

    # Foreign Keys
    thread_id: UUID = Field(description="Foreign key for Thread.thread_object_instance_graph_branches")
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ThreadObjectInstanceGraphBranch.object_instance_graph_branch"
    )
    object_instance_graph_identity_id: UUID | None = Field(
        default=None, description="Foreign key for ThreadObjectInstanceGraphBranch.object_instance_graph_identity"
    )
