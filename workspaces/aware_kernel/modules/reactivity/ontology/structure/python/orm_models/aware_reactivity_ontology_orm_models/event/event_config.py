from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.event.event_enums import (
    EventDeliveryMode,
    EventPriority,
    EventType,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.event.event_config_action_config import EventConfigActionConfig
    from aware_reactivity_ontology_orm_models.event.event_config_condition_config import EventConfigConditionConfig


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
