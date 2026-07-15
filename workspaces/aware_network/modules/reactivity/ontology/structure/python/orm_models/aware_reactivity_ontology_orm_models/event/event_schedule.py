from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.event.event_enums import EventScheduleStatus

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.content.content import Content
    from aware_reactivity_ontology_orm_models.event.event import Event
    from aware_reactivity_ontology_orm_models.event.event_config import EventConfig


class EventSchedule(ORMModel):
    # Relationships
    content: Content | None = Field(default=None, exclude=True)
    event_config: EventConfig | None = Field(default=None, exclude=True)
    events: list[Event] = Field(default_factory=list, exclude=True)

    # Attributes
    end_time: datetime
    iteration_count: int | None = Field(default=0)
    key: str
    location: str | None = Field(default=None)
    rrule: str | None = Field(default=None)
    start_time: datetime
    status: EventScheduleStatus = Field(default=EventScheduleStatus.active)

    # Foreign Keys
    content_id: UUID | None = Field(default=None, description="Foreign key for EventSchedule.content")
    event_config_id: UUID = Field(description="Foreign key for EventSchedule.event_config")
