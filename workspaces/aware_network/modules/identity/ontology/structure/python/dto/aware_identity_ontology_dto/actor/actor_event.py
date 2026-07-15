from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.actor.actor_event_enums import ActorEventRole

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor import Actor
    from aware_reactivity_ontology_dto.event.event import Event


class ActorEvent(BaseModel):
    # Relationships
    actor: Actor | None = Field(default=None)
    event: Event | None = Field(default=None)

    # Attributes
    role: ActorEventRole
