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
from aware_orm.runtime.invocation import invoke_constructor

# Reactivity Ontology
from aware_reactivity_ontology.action.action_enums import (
    ActionFeedbackStage,
    ActionFeedbackStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance


class ActionFeedback(ORMModel):
    # Relationships
    payload_model: InlineValueInstance | None = Field(default=None)

    # Attributes
    created_at_unix_ms: int = Field(default=0)
    message: str | None = Field(default=None)
    payload: JsonObject = Field(
        default_factory=JsonObject,
        description="Deprecated compatibility payload mirror.\nCanonical typed feedback payload truth is `payload_model`, whose\nClassConfig is resolved from the bound endpoint stream event config.",
    )
    sequence: int
    stage: ActionFeedbackStage
    status: ActionFeedbackStatus

    # Foreign Keys
    action_execution_id: UUID = Field(description="Foreign key for ActionExecution.action_feedback")
    payload_model_id: UUID | None = Field(default=None, description="Foreign key for ActionFeedback.payload_model")

    @classmethod
    async def create_via_action_execution(
        cls,
        action_execution_id: UUID,
        sequence: int,
        stage: ActionFeedbackStage,
        status: ActionFeedbackStatus,
        created_at_unix_ms: int = 0,
        message: str | None = None,
        payload: JsonObject = {},
        payload_class_config_id: UUID | None = None,
    ) -> ActionFeedback:
        """
        Create commit-backed lifecycle feedback evidence for one action execution.

        Contract:
        - This is append-only feedback truth under an ActionExecution.
        - Deterministic id is derived from action execution and sequence.
        - `payload_model` is typed stream feedback payload evidence. Its
          ClassConfig is supplied by the Experience/API resolver; Reactivity
          remains API-agnostic.
        - `payload` is deprecated compatibility metadata only.
        """

        payload = {
            "action_execution_id": action_execution_id,
            "sequence": sequence,
            "stage": stage,
            "status": status,
            "created_at_unix_ms": created_at_unix_ms,
            "message": message,
            "payload": payload,
            "payload_class_config_id": payload_class_config_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_action_execution", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionFeedback):
            return value
        return ActionFeedback.validate_invocation_value(value)


class ActionFeedbackCreateViaActionExecutionInput(BaseModel):
    action_execution_id: UUID = Field(description="Foreign key for ActionExecution.action_feedback")
    sequence: int
    stage: ActionFeedbackStage
    status: ActionFeedbackStatus
    created_at_unix_ms: int = Field(default=0)
    message: str | None = Field(default=None)
    payload: JsonObject = Field(default_factory=JsonObject)
    payload_class_config_id: UUID | None = Field(default=None)


class ActionFeedbackCreateViaActionExecutionOutput(BaseModel):
    value: ActionFeedback


FUNCTIONS = {
    "ActionFeedback": {
        "create_via_action_execution": {
            "canonical": {
                "name": "create_via_action_execution",
                "description": "Create commit-backed lifecycle feedback evidence for one action execution.\n\nContract:\n- This is append-only feedback truth under an ActionExecution.\n- Deterministic id is derived from action execution and sequence.\n- `payload_model` is typed stream feedback payload evidence. Its\n  ClassConfig is supplied by the Experience/API resolver; Reactivity\n  remains API-agnostic.\n- `payload` is deprecated compatibility metadata only.",
                "is_constructor": True,
            },
            "input": ActionFeedbackCreateViaActionExecutionInput,
            "output": ActionFeedbackCreateViaActionExecutionOutput,
        },
    },
}

__all__ = [
    "ActionFeedback",
    "ActionFeedbackCreateViaActionExecutionInput",
    "ActionFeedbackCreateViaActionExecutionOutput",
    "FUNCTIONS",
]
