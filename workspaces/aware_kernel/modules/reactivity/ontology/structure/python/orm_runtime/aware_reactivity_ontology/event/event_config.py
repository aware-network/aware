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
from aware_reactivity_ontology.event.event_enums import (
    EventDeliveryMode,
    EventPriority,
    EventType,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology.event.event_config_action_config import EventConfigActionConfig
    from aware_reactivity_ontology.event.event_config_condition_config import EventConfigConditionConfig


class EventConfig(ORMModel):
    # Relationships
    event_config_action_configs: list[EventConfigActionConfig] = Field(default_factory=list, exclude=True)
    event_config_condition_configs: list[EventConfigConditionConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    allowed_roles: list[str] = Field(default_factory=list)
    batch_window_ms: int | None = Field(default=None)
    delivery_mode: EventDeliveryMode = Field(default=EventDeliveryMode.immediate)
    description: str
    event_schema: JsonObject = Field(default_factory=JsonObject)
    event_type: EventType = Field(default=EventType.condition)
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    name: str
    priority: EventPriority = Field(default=EventPriority.normal)
    require_authentication: bool = Field(default=True)
    valid_sources: list[str] = Field(default_factory=list)

    @classmethod
    async def create(
        cls,
        name: str,
        description: str,
        event_type: EventType = EventType.condition,
        delivery_mode: EventDeliveryMode = EventDeliveryMode.immediate,
        priority: EventPriority = EventPriority.normal,
        is_enabled: bool = True,
        is_system: bool = False,
        require_authentication: bool = True,
        valid_sources: list[str] = [],
        allowed_roles: list[str] = [],
        event_schema: JsonObject = {},
        batch_window_ms: int | None = None,
    ) -> EventConfig:
        """Create a canonical event policy root."""

        payload = {
            "name": name,
            "description": description,
            "event_type": event_type,
            "delivery_mode": delivery_mode,
            "priority": priority,
            "is_enabled": is_enabled,
            "is_system": is_system,
            "require_authentication": require_authentication,
            "valid_sources": valid_sources,
            "allowed_roles": allowed_roles,
            "event_schema": event_schema,
            "batch_window_ms": batch_window_ms,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EventConfig):
            return value
        return EventConfig.validate_invocation_value(value)

    async def add_condition_config(
        self,
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
        """Link this EventConfig to a ConditionConfig via a canonical binding edge."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="add_condition_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.event.event_config_condition_config import EventConfigConditionConfig

        if isinstance(value, EventConfigConditionConfig):
            return value
        return EventConfigConditionConfig.validate_invocation_value(value)

    async def add_action_config(
        self,
        action_config_id: UUID,
        execution_order: int = 0,
        priority: int = 0,
        is_enabled: bool = True,
        is_required: bool = False,
        continue_on_fail: bool = True,
    ) -> EventConfigActionConfig:
        """Link this EventConfig to an ActionConfig via a canonical binding edge."""

        payload = {
            "action_config_id": action_config_id,
            "execution_order": execution_order,
            "priority": priority,
            "is_enabled": is_enabled,
            "is_required": is_required,
            "continue_on_fail": continue_on_fail,
        }
        result = await invoke_instance(orm_model=self, function_name="add_action_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.event.event_config_action_config import EventConfigActionConfig

        if isinstance(value, EventConfigActionConfig):
            return value
        return EventConfigActionConfig.validate_invocation_value(value)

    async def update_sources(self, p_event_config_id: UUID, p_valid_sources: list[str]) -> None:
        """
        Updates the valid sources for an event config, ensuring uniqueness and order.
        Parameters: p_event_config_id: The UUID of the event config to update.
        p_valid_sources: Array of valid source identifiers.
        Returns: void
        """

        payload = {"p_event_config_id": p_event_config_id, "p_valid_sources": p_valid_sources}
        await invoke_instance(orm_model=self, function_name="update_sources", payload=payload)
        return None


class EventConfigCreateInput(BaseModel):
    name: str
    description: str
    event_type: EventType = Field(default=EventType.condition)
    delivery_mode: EventDeliveryMode = Field(default=EventDeliveryMode.immediate)
    priority: EventPriority = Field(default=EventPriority.normal)
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    require_authentication: bool = Field(default=True)
    valid_sources: list[str] = Field(default_factory=list)
    allowed_roles: list[str] = Field(default_factory=list)
    event_schema: JsonObject = Field(default_factory=JsonObject)
    batch_window_ms: int | None = Field(default=None)


class EventConfigCreateOutput(BaseModel):
    value: EventConfig


class EventConfigAddConditionConfigInput(BaseModel):
    condition_config_id: UUID
    execution_order: int = Field(default=0)
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    continue_on_fail: bool = Field(default=True)
    stop_on_match: bool = Field(default=False)
    cache_result: bool = Field(default=False)
    cache_ttl_seconds: int | None = Field(default=None)


class EventConfigAddConditionConfigOutput(BaseModel):
    value: EventConfigConditionConfig


class EventConfigAddActionConfigInput(BaseModel):
    action_config_id: UUID
    execution_order: int = Field(default=0)
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    continue_on_fail: bool = Field(default=True)


class EventConfigAddActionConfigOutput(BaseModel):
    value: EventConfigActionConfig


class EventConfigUpdateSourcesInput(BaseModel):
    p_event_config_id: UUID
    p_valid_sources: list[str] = Field(default_factory=list)


class EventConfigUpdateSourcesOutput(BaseModel):
    pass


FUNCTIONS = {
    "EventConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create a canonical event policy root.",
                "is_constructor": True,
            },
            "input": EventConfigCreateInput,
            "output": EventConfigCreateOutput,
        },
        "add_condition_config": {
            "canonical": {
                "name": "add_condition_config",
                "description": "Link this EventConfig to a ConditionConfig via a canonical binding edge.",
                "is_constructor": False,
            },
            "input": EventConfigAddConditionConfigInput,
            "output": EventConfigAddConditionConfigOutput,
        },
        "add_action_config": {
            "canonical": {
                "name": "add_action_config",
                "description": "Link this EventConfig to an ActionConfig via a canonical binding edge.",
                "is_constructor": False,
            },
            "input": EventConfigAddActionConfigInput,
            "output": EventConfigAddActionConfigOutput,
        },
        "update_sources": {
            "canonical": {
                "name": "update_sources",
                "description": "Updates the valid sources for an event config, ensuring uniqueness and order.\nParameters: p_event_config_id: The UUID of the event config to update.\np_valid_sources: Array of valid source identifiers.\nReturns: void",
                "is_constructor": False,
            },
            "input": EventConfigUpdateSourcesInput,
            "output": EventConfigUpdateSourcesOutput,
        },
    },
}

__all__ = [
    "EventConfig",
    "EventConfigCreateInput",
    "EventConfigCreateOutput",
    "EventConfigAddConditionConfigInput",
    "EventConfigAddConditionConfigOutput",
    "EventConfigAddActionConfigInput",
    "EventConfigAddActionConfigOutput",
    "EventConfigUpdateSourcesInput",
    "EventConfigUpdateSourcesOutput",
    "FUNCTIONS",
]
