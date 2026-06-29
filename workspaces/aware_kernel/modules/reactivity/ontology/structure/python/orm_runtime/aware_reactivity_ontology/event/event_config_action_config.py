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

if TYPE_CHECKING:
    from aware_reactivity_ontology.action.action_config import ActionConfig


class EventConfigActionConfig(ORMModel):
    # Relationships
    action_config: ActionConfig | None = Field(default=None, exclude=True)

    # Attributes
    continue_on_fail: bool = Field(default=True)
    execution_order: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    priority: int = Field(default=0)

    # Foreign Keys
    event_config_id: UUID = Field(description="Foreign key for EventConfig.event_config_action_configs")
    action_config_id: UUID = Field(description="Foreign key for EventConfigActionConfig.action_config")

    @classmethod
    async def create_via_event_config(
        cls,
        event_config_id: UUID,
        action_config_id: UUID,
        execution_order: int = 0,
        priority: int = 0,
        is_enabled: bool = True,
        is_required: bool = False,
        continue_on_fail: bool = True,
    ) -> EventConfigActionConfig:
        """Create a canonical event-to-action binding policy node."""

        payload = {
            "event_config_id": event_config_id,
            "action_config_id": action_config_id,
            "execution_order": execution_order,
            "priority": priority,
            "is_enabled": is_enabled,
            "is_required": is_required,
            "continue_on_fail": continue_on_fail,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_event_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EventConfigActionConfig):
            return value
        return EventConfigActionConfig.validate_invocation_value(value)


class EventConfigActionConfigCreateViaEventConfigInput(BaseModel):
    event_config_id: UUID = Field(description="Foreign key for EventConfig.event_config_action_configs")
    action_config_id: UUID
    execution_order: int = Field(default=0)
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    continue_on_fail: bool = Field(default=True)


class EventConfigActionConfigCreateViaEventConfigOutput(BaseModel):
    value: EventConfigActionConfig


FUNCTIONS = {
    "EventConfigActionConfig": {
        "create_via_event_config": {
            "canonical": {
                "name": "create_via_event_config",
                "description": "Create a canonical event-to-action binding policy node.",
                "is_constructor": True,
            },
            "input": EventConfigActionConfigCreateViaEventConfigInput,
            "output": EventConfigActionConfigCreateViaEventConfigOutput,
        },
    },
}

__all__ = [
    "EventConfigActionConfig",
    "EventConfigActionConfigCreateViaEventConfigInput",
    "EventConfigActionConfigCreateViaEventConfigOutput",
    "FUNCTIONS",
]
