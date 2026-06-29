from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Reactivity Ontology
from aware_reactivity_ontology.action.action_enums import (
    ActionExecutionStatus,
    ActionFeedbackStage,
    ActionFeedbackStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology.action.action_feedback import ActionFeedback


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

    async def add_feedback(
        self,
        sequence: int,
        stage: ActionFeedbackStage,
        status: ActionFeedbackStatus,
        created_at_unix_ms: int = 0,
        message: str | None = None,
        payload: JsonObject = {},
        payload_class_config_id: UUID | None = None,
    ) -> ActionFeedback:
        """Append one lifecycle feedback record for this execution."""

        payload = {
            "sequence": sequence,
            "stage": stage,
            "status": status,
            "created_at_unix_ms": created_at_unix_ms,
            "message": message,
            "payload": payload,
            "payload_class_config_id": payload_class_config_id,
        }
        result = await invoke_instance(orm_model=self, function_name="add_feedback", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.action.action_feedback import ActionFeedback

        if isinstance(value, ActionFeedback):
            return value
        return ActionFeedback.validate_invocation_value(value)

    async def set_status(self, status: ActionExecutionStatus, result_info: str | None = None) -> None:
        """Update execution status after service fulfillment progress."""

        payload = {"status": status, "result_info": result_info}
        await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        return None

    @classmethod
    async def create_via_action_intent(
        cls,
        action_intent_id: UUID,
        execution_key: str = "primary",
        status: ActionExecutionStatus = ActionExecutionStatus.created,
        execution_context: JsonObject = {},
        executor_ref: str | None = None,
        result_info: str | None = None,
    ) -> ActionExecution:
        """
        Create commit-backed action execution promise/correlation evidence.

        Contract:
        - This is the canonical "service accepted or will decide on fulfillment" record.
        - Deterministic id is derived from action intent and execution key.
        """

        payload = {
            "action_intent_id": action_intent_id,
            "execution_key": execution_key,
            "status": status,
            "execution_context": execution_context,
            "executor_ref": executor_ref,
            "result_info": result_info,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_action_intent", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionExecution):
            return value
        return ActionExecution.validate_invocation_value(value)


class ActionExecutionAddFeedbackInput(BaseModel):
    sequence: int
    stage: ActionFeedbackStage
    status: ActionFeedbackStatus
    created_at_unix_ms: int = Field(default=0)
    message: str | None = Field(default=None)
    payload: JsonObject = Field(default_factory=JsonObject)
    payload_class_config_id: UUID | None = Field(default=None)


class ActionExecutionAddFeedbackOutput(BaseModel):
    value: ActionFeedback


class ActionExecutionSetStatusInput(BaseModel):
    status: ActionExecutionStatus
    result_info: str | None = Field(default=None)


class ActionExecutionSetStatusOutput(BaseModel):
    pass


class ActionExecutionCreateViaActionIntentInput(BaseModel):
    action_intent_id: UUID = Field(description="Foreign key for ActionIntent.action_executions")
    execution_key: str = Field(default="primary")
    status: ActionExecutionStatus = Field(default=ActionExecutionStatus.created)
    execution_context: JsonObject = Field(default_factory=JsonObject)
    executor_ref: str | None = Field(default=None)
    result_info: str | None = Field(default=None)


class ActionExecutionCreateViaActionIntentOutput(BaseModel):
    value: ActionExecution


FUNCTIONS = {
    "ActionExecution": {
        "add_feedback": {
            "canonical": {
                "name": "add_feedback",
                "description": "Append one lifecycle feedback record for this execution.",
                "is_constructor": False,
            },
            "input": ActionExecutionAddFeedbackInput,
            "output": ActionExecutionAddFeedbackOutput,
        },
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Update execution status after service fulfillment progress.",
                "is_constructor": False,
            },
            "input": ActionExecutionSetStatusInput,
            "output": ActionExecutionSetStatusOutput,
        },
        "create_via_action_intent": {
            "canonical": {
                "name": "create_via_action_intent",
                "description": 'Create commit-backed action execution promise/correlation evidence.\n\nContract:\n- This is the canonical "service accepted or will decide on fulfillment" record.\n- Deterministic id is derived from action intent and execution key.',
                "is_constructor": True,
            },
            "input": ActionExecutionCreateViaActionIntentInput,
            "output": ActionExecutionCreateViaActionIntentOutput,
        },
    },
}

__all__ = [
    "ActionExecution",
    "ActionExecutionAddFeedbackInput",
    "ActionExecutionAddFeedbackOutput",
    "ActionExecutionSetStatusInput",
    "ActionExecutionSetStatusOutput",
    "ActionExecutionCreateViaActionIntentInput",
    "ActionExecutionCreateViaActionIntentOutput",
    "FUNCTIONS",
]
