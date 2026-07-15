from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.actor.actor_event_enums import ActorEventRole

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor import Actor
    from aware_reactivity_ontology_orm_models.event.event import Event


class ActorEvent(ORMModel):
    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)
    event: Event | None = Field(default=None, exclude=True)

    # Attributes
    role: ActorEventRole

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for ActorEvent.actor")
    event_id: UUID = Field(description="Foreign key for ActorEvent.event")
