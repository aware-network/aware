from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.event.event import Event


class EventConfigConditionConfigScopeEvent(BaseModel):
    # Relationships
    event: Event | None = Field(default=None)
