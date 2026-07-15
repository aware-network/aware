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


class EventConfigMeaningResolverConfig(ORMModel):
    # Relationships
    action_config: ActionConfig | None = Field(default=None, exclude=True)

    # Attributes
    resolver_key: str = Field(default="default")
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)

    # Foreign Keys
    event_config_id: UUID = Field(description="Foreign key for EventConfig.event_config_meaning_resolver_configs")
    action_config_id: UUID = Field(description="Foreign key for EventConfigMeaningResolverConfig.action_config")

    @classmethod
    async def create_via_event_config(
        cls,
        event_config_id: UUID,
        action_config_id: UUID,
        resolver_key: str = "default",
        priority: int = 0,
        is_enabled: bool = True,
    ) -> EventConfigMeaningResolverConfig:
        """Create one typed event-to-meaning-provider action binding."""

        payload = {
            "event_config_id": event_config_id,
            "action_config_id": action_config_id,
            "resolver_key": resolver_key,
            "priority": priority,
            "is_enabled": is_enabled,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_event_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EventConfigMeaningResolverConfig):
            return value
        return EventConfigMeaningResolverConfig.validate_invocation_value(value)


class EventConfigMeaningResolverConfigCreateViaEventConfigInput(BaseModel):
    event_config_id: UUID = Field(description="Foreign key for EventConfig.event_config_meaning_resolver_configs")
    action_config_id: UUID
    resolver_key: str = Field(default="default")
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)


class EventConfigMeaningResolverConfigCreateViaEventConfigOutput(BaseModel):
    value: EventConfigMeaningResolverConfig


FUNCTIONS = {
    "EventConfigMeaningResolverConfig": {
        "create_via_event_config": {
            "canonical": {
                "name": "create_via_event_config",
                "description": "Create one typed event-to-meaning-provider action binding.",
                "is_constructor": True,
            },
            "input": EventConfigMeaningResolverConfigCreateViaEventConfigInput,
            "output": EventConfigMeaningResolverConfigCreateViaEventConfigOutput,
        },
    },
}

__all__ = [
    "EventConfigMeaningResolverConfig",
    "EventConfigMeaningResolverConfigCreateViaEventConfigInput",
    "EventConfigMeaningResolverConfigCreateViaEventConfigOutput",
    "FUNCTIONS",
]
