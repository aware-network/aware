from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.event.event import Event


class EventConfigConditionConfigScopeEvent(ORMModel):
    # Relationships
    event: Event | None = Field(default=None, exclude=True)

    # Foreign Keys
    event_config_condition_config_scope_id: UUID = Field(
        description="Foreign key for EventConfigConditionConfigScope.event_config_condition_config_scope_events"
    )
    event_id: UUID = Field(description="Foreign key for EventConfigConditionConfigScopeEvent.event")
