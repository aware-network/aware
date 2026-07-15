from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.lane.lane import Lane
    from aware_meta_ontology_orm_models.function.function_call import FunctionCall


class ObjectInstanceGraphLane(ORMModel):
    # Relationships
    lane: Lane = Field(description="Lane Identity")
    function_calls: list[FunctionCall] = Field(
        default_factory=list, description="Function-call execution history for this lane."
    )

    # Foreign Keys
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphBranch.object_instance_graph_lanes"
    )
    lane_id: UUID | None = Field(default=None, description="Foreign key for ObjectInstanceGraphLane.lane")
