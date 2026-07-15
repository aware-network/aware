from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.condition.condition import Condition
    from aware_reactivity_ontology_dto.event.event_config_condition_config import EventConfigConditionConfig


class EventCondition(BaseModel):
    # Relationships
    condition: Condition | None = Field(default=None)
    config: EventConfigConditionConfig | None = Field(default=None)

    # Attributes
    evaluation_context: JsonObject = Field(default_factory=JsonObject)
    matched: bool = Field(default=True)
