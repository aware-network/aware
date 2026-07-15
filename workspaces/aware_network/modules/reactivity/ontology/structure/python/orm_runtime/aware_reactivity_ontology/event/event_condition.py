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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology.condition.condition import Condition
    from aware_reactivity_ontology.event.event_config_condition_config import EventConfigConditionConfig


class EventCondition(ORMModel):
    # Relationships
    condition: Condition | None = Field(default=None, exclude=True)
    config: EventConfigConditionConfig | None = Field(default=None, exclude=True)

    # Attributes
    evaluation_context: JsonObject = Field(default_factory=JsonObject)
    matched: bool = Field(default=True)

    # Foreign Keys
    event_id: UUID = Field(description="Foreign key for Event.event_conditions")
    condition_id: UUID = Field(description="Foreign key for EventCondition.condition")
    config_id: UUID = Field(description="Foreign key for EventCondition.config")

    @classmethod
    async def create_via_event(
        cls,
        event_id: UUID,
        condition_id: UUID,
        config_id: UUID,
        matched: bool = True,
        evaluation_context: JsonObject = {},
    ) -> EventCondition:
        """Create canonical condition-match evidence for a raised event."""

        payload = {
            "event_id": event_id,
            "condition_id": condition_id,
            "config_id": config_id,
            "matched": matched,
            "evaluation_context": evaluation_context,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_event", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EventCondition):
            return value
        return EventCondition.validate_invocation_value(value)


class EventConditionCreateViaEventInput(BaseModel):
    event_id: UUID = Field(description="Foreign key for Event.event_conditions")
    condition_id: UUID
    config_id: UUID
    matched: bool = Field(default=True)
    evaluation_context: JsonObject = Field(default_factory=JsonObject)


class EventConditionCreateViaEventOutput(BaseModel):
    value: EventCondition


FUNCTIONS = {
    "EventCondition": {
        "create_via_event": {
            "canonical": {
                "name": "create_via_event",
                "description": "Create canonical condition-match evidence for a raised event.",
                "is_constructor": True,
            },
            "input": EventConditionCreateViaEventInput,
            "output": EventConditionCreateViaEventOutput,
        },
    },
}

__all__ = [
    "EventCondition",
    "EventConditionCreateViaEventInput",
    "EventConditionCreateViaEventOutput",
    "FUNCTIONS",
]
