from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.condition.condition import Condition
    from aware_reactivity_ontology_orm_models.event.event_config_condition_config import EventConfigConditionConfig


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
