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

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_reactivity_ontology.event.event_config_condition_config_scope_event import (
        EventConfigConditionConfigScopeEvent,
    )


class EventConfigConditionConfigScope(ORMModel):
    # Relationships
    event_config_condition_config_scope_events: list[EventConfigConditionConfigScopeEvent] = Field(
        default_factory=list, exclude=True
    )
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Foreign Keys
    event_config_condition_config_id: UUID = Field(
        description="Foreign key for EventConfigConditionConfig.event_config_condition_config_scopes"
    )
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for EventConfigConditionConfigScope.object_instance_graph_identity"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for EventConfigConditionConfigScope.object_instance_graph_branch"
    )

    async def add_event(self, event_id: UUID) -> EventConfigConditionConfigScopeEvent:
        """Attach one runtime event evidence record to this scope lane."""

        payload = {"event_id": event_id}
        result = await invoke_instance(orm_model=self, function_name="add_event", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.event.event_config_condition_config_scope_event import (
            EventConfigConditionConfigScopeEvent,
        )

        if isinstance(value, EventConfigConditionConfigScopeEvent):
            return value
        return EventConfigConditionConfigScopeEvent.validate_invocation_value(value)

    @classmethod
    async def create_via_event_config_condition_config(
        cls,
        event_config_condition_config_id: UUID,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_branch_id: UUID | None = None,
    ) -> EventConfigConditionConfigScope:
        """
        Create a canonical lane scope for one EventConfigConditionConfig binding.

        Contract:
        - Event-first scope rail for condition activation matching.
        - Deterministic id derived from binding id + OIGI + optional OIGB.
        """

        payload = {
            "event_config_condition_config_id": event_config_condition_config_id,
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_event_config_condition_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EventConfigConditionConfigScope):
            return value
        return EventConfigConditionConfigScope.validate_invocation_value(value)


class EventConfigConditionConfigScopeAddEventInput(BaseModel):
    event_id: UUID


class EventConfigConditionConfigScopeAddEventOutput(BaseModel):
    value: EventConfigConditionConfigScopeEvent


class EventConfigConditionConfigScopeCreateViaEventConfigConditionConfigInput(BaseModel):
    event_config_condition_config_id: UUID = Field(
        description="Foreign key for EventConfigConditionConfig.event_config_condition_config_scopes"
    )
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID | None = Field(default=None)


class EventConfigConditionConfigScopeCreateViaEventConfigConditionConfigOutput(BaseModel):
    value: EventConfigConditionConfigScope


FUNCTIONS = {
    "EventConfigConditionConfigScope": {
        "add_event": {
            "canonical": {
                "name": "add_event",
                "description": "Attach one runtime event evidence record to this scope lane.",
                "is_constructor": False,
            },
            "input": EventConfigConditionConfigScopeAddEventInput,
            "output": EventConfigConditionConfigScopeAddEventOutput,
        },
        "create_via_event_config_condition_config": {
            "canonical": {
                "name": "create_via_event_config_condition_config",
                "description": "Create a canonical lane scope for one EventConfigConditionConfig binding.\n\nContract:\n- Event-first scope rail for condition activation matching.\n- Deterministic id derived from binding id + OIGI + optional OIGB.",
                "is_constructor": True,
            },
            "input": EventConfigConditionConfigScopeCreateViaEventConfigConditionConfigInput,
            "output": EventConfigConditionConfigScopeCreateViaEventConfigConditionConfigOutput,
        },
    },
}

__all__ = [
    "EventConfigConditionConfigScope",
    "EventConfigConditionConfigScopeAddEventInput",
    "EventConfigConditionConfigScopeAddEventOutput",
    "EventConfigConditionConfigScopeCreateViaEventConfigConditionConfigInput",
    "EventConfigConditionConfigScopeCreateViaEventConfigConditionConfigOutput",
    "FUNCTIONS",
]
