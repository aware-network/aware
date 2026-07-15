from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.event.event_enums import EventStatus

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.action.action import Action
    from aware_reactivity_ontology_orm_models.action.action_intent import ActionIntent
    from aware_reactivity_ontology_orm_models.event.event_condition import EventCondition
    from aware_reactivity_ontology_orm_models.event.event_config import EventConfig


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
