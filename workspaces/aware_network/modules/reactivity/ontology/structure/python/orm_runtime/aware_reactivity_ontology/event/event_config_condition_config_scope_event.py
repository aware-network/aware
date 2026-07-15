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
    from aware_reactivity_ontology.event.event import Event


class EventConfigConditionConfigScopeEvent(ORMModel):
    # Relationships
    event: Event | None = Field(default=None, exclude=True)

    # Foreign Keys
    event_config_condition_config_scope_id: UUID = Field(
        description="Foreign key for EventConfigConditionConfigScope.event_config_condition_config_scope_events"
    )
    event_id: UUID = Field(description="Foreign key for EventConfigConditionConfigScopeEvent.event")

    @classmethod
    async def create_via_event_config_condition_config_scope(
        cls, event_config_condition_config_scope_id: UUID, event_id: UUID
    ) -> EventConfigConditionConfigScopeEvent:
        """
        Record canonical scope-level event activation evidence.

        Contract:
        - Event-first evidence rail: one raised Event can be linked to one or more scopes.
        - Deterministic id derived from (scope_id, event_id).
        """

        payload = {
            "event_config_condition_config_scope_id": event_config_condition_config_scope_id,
            "event_id": event_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_event_config_condition_config_scope", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EventConfigConditionConfigScopeEvent):
            return value
        return EventConfigConditionConfigScopeEvent.validate_invocation_value(value)


class EventConfigConditionConfigScopeEventCreateViaEventConfigConditionConfigScopeInput(BaseModel):
    event_config_condition_config_scope_id: UUID = Field(
        description="Foreign key for EventConfigConditionConfigScope.event_config_condition_config_scope_events"
    )
    event_id: UUID


class EventConfigConditionConfigScopeEventCreateViaEventConfigConditionConfigScopeOutput(BaseModel):
    value: EventConfigConditionConfigScopeEvent


FUNCTIONS = {
    "EventConfigConditionConfigScopeEvent": {
        "create_via_event_config_condition_config_scope": {
            "canonical": {
                "name": "create_via_event_config_condition_config_scope",
                "description": "Record canonical scope-level event activation evidence.\n\nContract:\n- Event-first evidence rail: one raised Event can be linked to one or more scopes.\n- Deterministic id derived from (scope_id, event_id).",
                "is_constructor": True,
            },
            "input": EventConfigConditionConfigScopeEventCreateViaEventConfigConditionConfigScopeInput,
            "output": EventConfigConditionConfigScopeEventCreateViaEventConfigConditionConfigScopeOutput,
        },
    },
}

__all__ = [
    "EventConfigConditionConfigScopeEvent",
    "EventConfigConditionConfigScopeEventCreateViaEventConfigConditionConfigScopeInput",
    "EventConfigConditionConfigScopeEventCreateViaEventConfigConditionConfigScopeOutput",
    "FUNCTIONS",
]
