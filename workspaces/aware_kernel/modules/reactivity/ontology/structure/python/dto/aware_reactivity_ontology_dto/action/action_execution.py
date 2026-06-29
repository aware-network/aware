from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.action.action_enums import ActionExecutionStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.action.action_feedback import ActionFeedback


class ActionExecution(BaseModel):
    # Relationships
    action_feedback: list[ActionFeedback] = Field(default_factory=list)

    # Attributes
    execution_context: JsonObject = Field(default_factory=JsonObject)
    execution_key: str = Field(default="primary")
    executor_ref: str | None = Field(default=None)
    result_info: str | None = Field(default=None)
    status: ActionExecutionStatus = Field(default=ActionExecutionStatus.created)
