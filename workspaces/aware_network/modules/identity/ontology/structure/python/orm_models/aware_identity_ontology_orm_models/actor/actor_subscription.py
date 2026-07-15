from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.actor.actor_subscription_enums import (
    SubscriptionAddressingPolicy,
    SubscriptionFilterMode,
    SubscriptionStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor_subscription_event import ActorSubscriptionEvent
    from aware_reactivity_ontology_orm_models.event.event_config_action_config import EventConfigActionConfig
    from aware_reactivity_ontology_orm_models.event.event_config_condition_config_scope import (
        EventConfigConditionConfigScope,
    )


class ActorSubscription(ORMModel):
    # Relationships
    event_config_condition_config_scope: EventConfigConditionConfigScope | None = Field(default=None, exclude=True)
    event_config_action_configs: list[EventConfigActionConfig] = Field(default_factory=list)
    actor_subscription_events: list[ActorSubscriptionEvent] = Field(
        default_factory=list,
        exclude=True,
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

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for Actor.actor_subscriptions")
    event_config_condition_config_scope_id: UUID = Field(
        description="Foreign key for ActorSubscription.event_config_condition_config_scope"
    )
