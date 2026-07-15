from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.actor.actor_subscription_enums import (
    SubscriptionAddressingPolicy,
    SubscriptionFilterMode,
    SubscriptionStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor_subscription_event import ActorSubscriptionEvent
    from aware_reactivity_ontology_dto.event.event_config_action_config import EventConfigActionConfig
    from aware_reactivity_ontology_dto.event.event_config_condition_config_scope import EventConfigConditionConfigScope


class ActorSubscription(BaseModel):
    # Relationships
    event_config_condition_config_scope: EventConfigConditionConfigScope | None = Field(default=None)
    event_config_action_configs: list[EventConfigActionConfig] = Field(default_factory=list)
    actor_subscription_events: list[ActorSubscriptionEvent] = Field(
        default_factory=list,
        description="Activation lifecycle ledger \u2014 contained under this subscription.\nContainment rail: ActorSubscriptionEvent identity propagates parent\ncontext through this member path per\n`languages/aware/grammar/docs/STABLE_IDS.md`.",
    )

    # Attributes
    addressing_policy: SubscriptionAddressingPolicy = Field(default=SubscriptionAddressingPolicy.any)
    batch_mode: bool = Field(default=False)
    batch_window_ms: int = Field(default=1000)
    check_ownership: bool = Field(default=True)
    description: str | None = Field(default=None)
    action_type: str | None = Field(default=None)
    filter_config: JsonObject | None = Field(default=None)
    filter_mode: SubscriptionFilterMode = Field(default=SubscriptionFilterMode.all_instances)
    is_enabled: bool = Field(default=True)
    max_batch_size: int = Field(default=100)
    name: str
    priority: int = Field(default=0)
    rate_limit_per_hour: int | None = Field(default=None)
    rate_limit_per_minute: int | None = Field(default=None)
    require_read_access: bool = Field(default=True)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.active)
