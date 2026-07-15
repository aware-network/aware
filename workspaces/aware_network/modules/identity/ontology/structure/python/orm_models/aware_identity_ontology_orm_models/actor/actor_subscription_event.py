from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.actor.actor_subscription_enums import SubscriptionActivationStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.event.event_config_condition_config_scope_event import (
        EventConfigConditionConfigScopeEvent,
    )


class ActorSubscriptionEvent(ORMModel):
    # Relationships
    event_config_condition_config_scope_event: EventConfigConditionConfigScopeEvent | None = Field(
        default=None, exclude=True
    )

    # Attributes
    reason: str | None = Field(default=None)
    status: SubscriptionActivationStatus = Field(default=SubscriptionActivationStatus.ready)

    # Foreign Keys
    actor_subscription_id: UUID = Field(description="Foreign key for ActorSubscription.actor_subscription_events")
    event_config_condition_config_scope_event_id: UUID = Field(
        description="Foreign key for ActorSubscriptionEvent.event_config_condition_config_scope_event"
    )
