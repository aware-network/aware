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
    from aware_api_ontology.api.api_call import ApiCall
    from aware_reactivity_ontology.action.action_feedback import ActionFeedback


class ActionExecution(ORMModel):
    # Relationships
    action_feedback: list[ActionFeedback] = Field(default_factory=list, exclude=True)
    api_call: ApiCall | None = Field(default=None)

    # Attributes
    execution_context: JsonObject = Field(default_factory=JsonObject)
    execution_key: str = Field(default="primary")
    executor_ref: str | None = Field(default=None)
    result_info: str | None = Field(default=None)
    status: ActionExecutionStatus = Field(default=ActionExecutionStatus.created)

    # Foreign Keys
    action_intent_id: UUID = Field(description="Foreign key for ActionIntent.action_executions")
    api_call_id: UUID | None = Field(default=None, description="Foreign key for ActionExecution.api_call")

    async def add_feedback(
        self,
        sequence: int,
        stage: ActionFeedbackStage,
        status: ActionFeedbackStatus,
        created_at_unix_ms: int = 0,
        message: str | None = None,
        payload: JsonObject = {},
        payload_class_config_id: UUID | None = None,
        api_call_stream_event_id: UUID | None = None,
    ) -> ActionFeedback:
        """
        Append one lifecycle feedback record for this execution.

        Contract:
        - Feedback is lifecycle envelope. Stream payload content lives once on
          `ApiCallStreamEvent.event_model`; this row only references that API
          receipt when feedback is stream-derived.
        """

        payload = {
            "sequence": sequence,
            "stage": stage,
            "status": status,
            "created_at_unix_ms": created_at_unix_ms,
            "message": message,
            "payload": payload,
            "payload_class_config_id": payload_class_config_id,
            "api_call_stream_event_id": api_call_stream_event_id,
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
        api_call_id: UUID | None = None,
        result_info: str | None = None,
    ) -> ActionExecution:
        """
        Create commit-backed action execution promise/correlation evidence.

        Contract:
        - This is one fulfillment attempt for one ActionIntent.
        - Executions are retries/re-dispatch attempts, not orchestration steps.
        - Deterministic id is derived from action intent and execution key.
        - `api_call` links to the API ingress receipt when this attempt crosses
          the API boundary. Each execution correlates to at most one ApiCall.
        """

        payload = {
            "action_intent_id": action_intent_id,
            "execution_key": execution_key,
            "status": status,
            "execution_context": execution_context,
            "executor_ref": executor_ref,
            "api_call_id": api_call_id,
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
    api_call_stream_event_id: UUID | None = Field(default=None)


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
    api_call_id: UUID | None = Field(default=None)
    result_info: str | None = Field(default=None)


class ActionExecutionCreateViaActionIntentOutput(BaseModel):
    value: ActionExecution


FUNCTIONS = {
    "ActionExecution": {
        "add_feedback": {
            "canonical": {
                "name": "add_feedback",
                "description": "Append one lifecycle feedback record for this execution.\n\nContract:\n- Feedback is lifecycle envelope. Stream payload content lives once on\n  `ApiCallStreamEvent.event_model`; this row only references that API\n  receipt when feedback is stream-derived.",
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
                "description": "Create commit-backed action execution promise/correlation evidence.\n\nContract:\n- This is one fulfillment attempt for one ActionIntent.\n- Executions are retries/re-dispatch attempts, not orchestration steps.\n- Deterministic id is derived from action intent and execution key.\n- `api_call` links to the API ingress receipt when this attempt crosses\n  the API boundary. Each execution correlates to at most one ApiCall.",
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
