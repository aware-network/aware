from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.actor.actor_subscription_enums import SubscriptionActivationStatus

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.event.event_config_condition_config_scope_event import (
        EventConfigConditionConfigScopeEvent,
    )


class ActorSubscriptionEvent(BaseModel):
    # Relationships
    event_config_condition_config_scope_event: EventConfigConditionConfigScopeEvent | None = Field(default=None)

    # Attributes
    reason: str | None = Field(default=None)
    status: SubscriptionActivationStatus = Field(default=SubscriptionActivationStatus.ready)
