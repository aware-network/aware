from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_history_ontology_dto.lane.lane import Lane
    from aware_meta_ontology_dto.function.function_call import FunctionCall


class ObjectInstanceGraphLane(BaseModel):
    # Relationships
    lane: Lane = Field(description="Lane Identity")
    function_calls: list[FunctionCall] = Field(
        default_factory=list, description="Function-call execution history for this lane."
    )
