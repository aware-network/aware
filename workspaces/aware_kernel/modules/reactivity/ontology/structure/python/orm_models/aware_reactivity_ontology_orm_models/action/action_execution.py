from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.action.action_enums import ActionExecutionStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.action.action_feedback import ActionFeedback


class ActionExecution(ORMModel):
    # Relationships
    action_feedback: list[ActionFeedback] = Field(default_factory=list, exclude=True)

    # Attributes
    execution_context: JsonObject = Field(default_factory=JsonObject)
    execution_key: str = Field(default="primary")
    executor_ref: str | None = Field(default=None)
    result_info: str | None = Field(default=None)
    status: ActionExecutionStatus = Field(default=ActionExecutionStatus.created)

    # Foreign Keys
    action_intent_id: UUID = Field(description="Foreign key for ActionIntent.action_executions")
