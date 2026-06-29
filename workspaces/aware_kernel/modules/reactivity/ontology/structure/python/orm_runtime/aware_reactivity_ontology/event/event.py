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
from aware_reactivity_ontology.action.action_enums import ActionIntentStatus
from aware_reactivity_ontology.event.event_enums import EventStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology.action.action import Action
    from aware_reactivity_ontology.action.action_intent import ActionIntent
    from aware_reactivity_ontology.event.event_condition import EventCondition
    from aware_reactivity_ontology.event.event_config import EventConfig


class Event(ORMModel):
    # Relationships
    actions: list[Action] = Field(default_factory=list, exclude=True)
    action_intents: list[ActionIntent] = Field(default_factory=list, exclude=True)
    config: EventConfig | None = Field(default=None, exclude=True)
    event_conditions: list[EventCondition] = Field(default_factory=list, exclude=True)

    # Attributes
    activation_id: UUID
    event_type: str
    source: str
    status: EventStatus = Field(default=EventStatus.raised)

    # Foreign Keys
    config_id: UUID = Field(description="Foreign key for Event.config")

    @classmethod
    async def create(
        cls,
        config_id: UUID,
        activation_id: UUID,
        event_type: str,
        source: str,
        status: EventStatus = EventStatus.raised,
    ) -> Event:
        """Create runtime event evidence anchored to one activation."""

        payload = {
            "config_id": config_id,
            "activation_id": activation_id,
            "event_type": event_type,
            "source": source,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Event):
            return value
        return Event.validate_invocation_value(value)

    async def add_event_condition(
        self, condition_id: UUID, config_id: UUID, matched: bool = True, evaluation_context: JsonObject = {}
    ) -> EventCondition:
        """Link one evaluated condition evidence record to this event."""

        payload = {
            "condition_id": condition_id,
            "config_id": config_id,
            "matched": matched,
            "evaluation_context": evaluation_context,
        }
        result = await invoke_instance(orm_model=self, function_name="add_event_condition", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.event.event_condition import EventCondition

        if isinstance(value, EventCondition):
            return value
        return EventCondition.validate_invocation_value(value)

    async def add_action(self, config_id: UUID, execution_context: JsonObject = {}) -> Action:
        """Link one action evidence record to this event."""

        payload = {"config_id": config_id, "execution_context": execution_context}
        result = await invoke_instance(orm_model=self, function_name="add_action", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.action.action import Action

        if isinstance(value, Action):
            return value
        return Action.validate_invocation_value(value)

    async def add_action_intent(
        self,
        config_id: UUID,
        intent_key: str,
        action_type: str | None = None,
        actor_id: UUID | None = None,
        target_actor_id: UUID | None = None,
        actor_subscription_id: UUID | None = None,
        action_payload: JsonObject = {},
        payload_class_config_id: UUID | None = None,
        subscription_filter_config: JsonObject = {},
        priority: int = 0,
        status: ActionIntentStatus = ActionIntentStatus.requested,
    ) -> ActionIntent:
        """
        Link one commit-backed action intent evidence record to this event.

        Contract:
        - `intent_key` is caller-supplied and opaque to Reactivity.
        - Actor/subscription args are deprecated provenance mirrors retained for
          bridge compatibility during the C2 cleanup window.
        """

        payload = {
            "config_id": config_id,
            "intent_key": intent_key,
            "action_type": action_type,
            "actor_id": actor_id,
            "target_actor_id": target_actor_id,
            "actor_subscription_id": actor_subscription_id,
            "action_payload": action_payload,
            "payload_class_config_id": payload_class_config_id,
            "subscription_filter_config": subscription_filter_config,
            "priority": priority,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="add_action_intent", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.action.action_intent import ActionIntent

        if isinstance(value, ActionIntent):
            return value
        return ActionIntent.validate_invocation_value(value)


class EventCreateInput(BaseModel):
    config_id: UUID
    activation_id: UUID
    event_type: str
    source: str
    status: EventStatus = Field(default=EventStatus.raised)


class EventCreateOutput(BaseModel):
    value: Event


class EventAddEventConditionInput(BaseModel):
    condition_id: UUID
    config_id: UUID
    matched: bool = Field(default=True)
    evaluation_context: JsonObject = Field(default_factory=JsonObject)


class EventAddEventConditionOutput(BaseModel):
    value: EventCondition


class EventAddActionInput(BaseModel):
    config_id: UUID
    execution_context: JsonObject = Field(default_factory=JsonObject)


class EventAddActionOutput(BaseModel):
    value: Action


class EventAddActionIntentInput(BaseModel):
    config_id: UUID
    intent_key: str
    action_type: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    target_actor_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    action_payload: JsonObject = Field(default_factory=JsonObject)
    payload_class_config_id: UUID | None = Field(default=None)
    subscription_filter_config: JsonObject = Field(default_factory=JsonObject)
    priority: int = Field(default=0)
    status: ActionIntentStatus = Field(default=ActionIntentStatus.requested)


class EventAddActionIntentOutput(BaseModel):
    value: ActionIntent


FUNCTIONS = {
    "Event": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create runtime event evidence anchored to one activation.",
                "is_constructor": True,
            },
            "input": EventCreateInput,
            "output": EventCreateOutput,
        },
        "add_event_condition": {
            "canonical": {
                "name": "add_event_condition",
                "description": "Link one evaluated condition evidence record to this event.",
                "is_constructor": False,
            },
            "input": EventAddEventConditionInput,
            "output": EventAddEventConditionOutput,
        },
        "add_action": {
            "canonical": {
                "name": "add_action",
                "description": "Link one action evidence record to this event.",
                "is_constructor": False,
            },
            "input": EventAddActionInput,
            "output": EventAddActionOutput,
        },
        "add_action_intent": {
            "canonical": {
                "name": "add_action_intent",
                "description": "Link one commit-backed action intent evidence record to this event.\n\nContract:\n- `intent_key` is caller-supplied and opaque to Reactivity.\n- Actor/subscription args are deprecated provenance mirrors retained for\n  bridge compatibility during the C2 cleanup window.",
                "is_constructor": False,
            },
            "input": EventAddActionIntentInput,
            "output": EventAddActionIntentOutput,
        },
    },
}

__all__ = [
    "Event",
    "EventCreateInput",
    "EventCreateOutput",
    "EventAddEventConditionInput",
    "EventAddEventConditionOutput",
    "EventAddActionInput",
    "EventAddActionOutput",
    "EventAddActionIntentInput",
    "EventAddActionIntentOutput",
    "FUNCTIONS",
]
