from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.event.event_enums import EventStatus

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.action.action import Action
    from aware_reactivity_ontology_dto.action.action_intent import ActionIntent
    from aware_reactivity_ontology_dto.event.event_condition import EventCondition
    from aware_reactivity_ontology_dto.event.event_config import EventConfig


class Event(BaseModel):
    # Relationships
    actions: list[Action] = Field(default_factory=list)
    action_intents: list[ActionIntent] = Field(default_factory=list)
    config: EventConfig | None = Field(default=None)
    event_conditions: list[EventCondition] = Field(default_factory=list)

    # Attributes
    activation_id: UUID
    event_type: str
    source: str
    status: EventStatus = Field(default=EventStatus.raised)
