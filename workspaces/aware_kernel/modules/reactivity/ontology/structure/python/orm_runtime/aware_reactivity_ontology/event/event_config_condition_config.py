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
    from aware_reactivity_ontology.condition.condition_config import ConditionConfig
    from aware_reactivity_ontology.event.event_config_condition_config_scope import EventConfigConditionConfigScope


class EventConfigConditionConfig(ORMModel):
    # Relationships
    condition_config: ConditionConfig | None = Field(default=None, exclude=True)
    event_config_condition_config_scopes: list[EventConfigConditionConfigScope] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    cache_result: bool = Field(default=False)
    cache_ttl_seconds: int | None = Field(default=None)
    continue_on_fail: bool = Field(default=True)
    execution_order: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    priority: int = Field(default=0)
    stop_on_match: bool = Field(default=False)

    # Foreign Keys
    event_config_id: UUID = Field(description="Foreign key for EventConfig.event_config_condition_configs")
    condition_config_id: UUID = Field(description="Foreign key for EventConfigConditionConfig.condition_config")

    async def create_scope(
        self, object_instance_graph_identity_id: UUID, object_instance_graph_branch_id: UUID | None = None
    ) -> EventConfigConditionConfigScope:
        """Create one scope rail under this event-condition policy binding."""

        payload = {
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.event.event_config_condition_config_scope import EventConfigConditionConfigScope

        if isinstance(value, EventConfigConditionConfigScope):
            return value
        return EventConfigConditionConfigScope.validate_invocation_value(value)

    @classmethod
    async def create_via_event_config(
        cls,
        event_config_id: UUID,
        condition_config_id: UUID,
        execution_order: int = 0,
        priority: int = 0,
        is_enabled: bool = True,
        is_required: bool = False,
        continue_on_fail: bool = True,
        stop_on_match: bool = False,
        cache_result: bool = False,
        cache_ttl_seconds: int | None = None,
    ) -> EventConfigConditionConfig:
        """
        Create a canonical event-to-condition binding policy node.

        Contract:
        - Constructor-owned creation path for event-condition links.
        - Binding references are explicit via event_config_id and condition_config_id.
        """

        payload = {
            "event_config_id": event_config_id,
            "condition_config_id": condition_config_id,
            "execution_order": execution_order,
            "priority": priority,
            "is_enabled": is_enabled,
            "is_required": is_required,
            "continue_on_fail": continue_on_fail,
            "stop_on_match": stop_on_match,
            "cache_result": cache_result,
            "cache_ttl_seconds": cache_ttl_seconds,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_event_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EventConfigConditionConfig):
            return value
        return EventConfigConditionConfig.validate_invocation_value(value)


class EventConfigConditionConfigCreateScopeInput(BaseModel):
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID | None = Field(default=None)


class EventConfigConditionConfigCreateScopeOutput(BaseModel):
    value: EventConfigConditionConfigScope


class EventConfigConditionConfigCreateViaEventConfigInput(BaseModel):
    event_config_id: UUID = Field(description="Foreign key for EventConfig.event_config_condition_configs")
    condition_config_id: UUID
    execution_order: int = Field(default=0)
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    continue_on_fail: bool = Field(default=True)
    stop_on_match: bool = Field(default=False)
    cache_result: bool = Field(default=False)
    cache_ttl_seconds: int | None = Field(default=None)


class EventConfigConditionConfigCreateViaEventConfigOutput(BaseModel):
    value: EventConfigConditionConfig


FUNCTIONS = {
    "EventConfigConditionConfig": {
        "create_scope": {
            "canonical": {
                "name": "create_scope",
                "description": "Create one scope rail under this event-condition policy binding.",
                "is_constructor": False,
            },
            "input": EventConfigConditionConfigCreateScopeInput,
            "output": EventConfigConditionConfigCreateScopeOutput,
        },
        "create_via_event_config": {
            "canonical": {
                "name": "create_via_event_config",
                "description": "Create a canonical event-to-condition binding policy node.\n\nContract:\n- Constructor-owned creation path for event-condition links.\n- Binding references are explicit via event_config_id and condition_config_id.",
                "is_constructor": True,
            },
            "input": EventConfigConditionConfigCreateViaEventConfigInput,
            "output": EventConfigConditionConfigCreateViaEventConfigOutput,
        },
    },
}

__all__ = [
    "EventConfigConditionConfig",
    "EventConfigConditionConfigCreateScopeInput",
    "EventConfigConditionConfigCreateScopeOutput",
    "EventConfigConditionConfigCreateViaEventConfigInput",
    "EventConfigConditionConfigCreateViaEventConfigOutput",
    "FUNCTIONS",
]
