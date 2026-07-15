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
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class ThreadObjectInstanceGraphBranch(BaseModel):
    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(
        default=None,
        description="Cross-OPG: target lane branch id for resolving `object_instance_graph_branch`.\nWhy:\n- `object_instance_graph_branch_id` (OIGB id) is stable but not invertible, so the UI\ncannot derive the OIGI lane branch id from it.\n- Runtime sets this from the domain lane HEAD `object_instance_graph_id` (commit-first).\nHard rule:\n- This must never encode `projection_hash` (internal lane coordinate).",
    )

    # Attributes
    is_active: bool = Field(default=True)
    title: str | None = Field(default=None)
