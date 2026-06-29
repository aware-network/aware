from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.event.event_enums import EventScheduleStatus

if TYPE_CHECKING:
    from aware_content_ontology_dto.content.content import Content
    from aware_reactivity_ontology_dto.event.event import Event
    from aware_reactivity_ontology_dto.event.event_config import EventConfig


class EventSchedule(BaseModel):
    # Relationships
    content: Content | None = Field(default=None)
    event_config: EventConfig | None = Field(default=None)
    events: list[Event] = Field(default_factory=list)

    # Attributes
    end_time: datetime
    iteration_count: int | None = Field(default=0)
    key: str
    location: str | None = Field(default=None)
    rrule: str | None = Field(default=None)
    start_time: datetime
    status: EventScheduleStatus = Field(default=EventScheduleStatus.active)
