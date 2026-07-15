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
from aware_reactivity_ontology.action.action_enums import ActionStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology.action.action_config import ActionConfig


class Action(ORMModel):
    # Relationships
    config: ActionConfig | None = Field(default=None, exclude=True)

    # Attributes
    execution_context: JsonObject = Field(default_factory=JsonObject)
    result_info: str | None = Field(default=None)
    status: ActionStatus = Field(default=ActionStatus.requested)

    # Foreign Keys
    event_id: UUID = Field(description="Foreign key for Event.actions")
    config_id: UUID = Field(description="Foreign key for Action.config")

    async def set_status(self, status: ActionStatus, result_info: str | None = None) -> None:
        """Update runtime action status after execution handling."""

        payload = {"status": status, "result_info": result_info}
        await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        return None

    @classmethod
    async def create_via_event(
        cls,
        event_id: UUID,
        config_id: UUID,
        status: ActionStatus = ActionStatus.requested,
        execution_context: JsonObject = {},
    ) -> Action:
        """Create runtime action evidence for a raised event."""

        payload = {
            "event_id": event_id,
            "config_id": config_id,
            "status": status,
            "execution_context": execution_context,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_event", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Action):
            return value
        return Action.validate_invocation_value(value)


class ActionSetStatusInput(BaseModel):
    status: ActionStatus
    result_info: str | None = Field(default=None)


class ActionSetStatusOutput(BaseModel):
    pass


class ActionCreateViaEventInput(BaseModel):
    event_id: UUID = Field(description="Foreign key for Event.actions")
    config_id: UUID
    status: ActionStatus = Field(default=ActionStatus.requested)
    execution_context: JsonObject = Field(default_factory=JsonObject)


class ActionCreateViaEventOutput(BaseModel):
    value: Action


FUNCTIONS = {
    "Action": {
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Update runtime action status after execution handling.",
                "is_constructor": False,
            },
            "input": ActionSetStatusInput,
            "output": ActionSetStatusOutput,
        },
        "create_via_event": {
            "canonical": {
                "name": "create_via_event",
                "description": "Create runtime action evidence for a raised event.",
                "is_constructor": True,
            },
            "input": ActionCreateViaEventInput,
            "output": ActionCreateViaEventOutput,
        },
    },
}

__all__ = [
    "Action",
    "ActionSetStatusInput",
    "ActionSetStatusOutput",
    "ActionCreateViaEventInput",
    "ActionCreateViaEventOutput",
    "FUNCTIONS",
]
