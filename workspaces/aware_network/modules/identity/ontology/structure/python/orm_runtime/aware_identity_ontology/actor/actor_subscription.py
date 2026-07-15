from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.actor.actor_subscription_enums import (
    SubscriptionActivationStatus,
    SubscriptionAddressingPolicy,
    SubscriptionFilterMode,
    SubscriptionStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor_subscription_event import ActorSubscriptionEvent
    from aware_reactivity_ontology.event.event_config_action_config import EventConfigActionConfig
    from aware_reactivity_ontology.event.event_config_condition_config_scope import EventConfigConditionConfigScope


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

    async def record_event(
        self,
        event_config_condition_config_scope_event_id: UUID,
        status: SubscriptionActivationStatus = SubscriptionActivationStatus.ready,
        reason: str | None = None,
    ) -> ActorSubscriptionEvent:
        """
        Record an activation lifecycle entry for this subscription against
        a scope-level event. Containment-rail constructor: identity flows
        through the `actor_subscription_events` member path.
        """

        payload = {
            "event_config_condition_config_scope_event_id": event_config_condition_config_scope_event_id,
            "status": status,
            "reason": reason,
        }
        result = await invoke_instance(orm_model=self, function_name="record_event", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.actor.actor_subscription_event import ActorSubscriptionEvent

        if isinstance(value, ActorSubscriptionEvent):
            return value
        return ActorSubscriptionEvent.validate_invocation_value(value)

    @classmethod
    async def create_via_actor(
        cls,
        actor_id: UUID,
        event_config_condition_config_scope_id: UUID,
        name: str,
        description: str | None = None,
        action_type: str | None = None,
        event_config_action_config_ids: list[UUID] = [],
        addressing_policy: SubscriptionAddressingPolicy = SubscriptionAddressingPolicy.any,
        is_enabled: bool = True,
        status: SubscriptionStatus = SubscriptionStatus.active,
        filter_mode: SubscriptionFilterMode = SubscriptionFilterMode.all_instances,
        filter_config: JsonObject | None = None,
        priority: int = 0,
        batch_mode: bool = False,
        batch_window_ms: int = 1000,
        max_batch_size: int = 100,
        require_read_access: bool = True,
        check_ownership: bool = True,
        rate_limit_per_minute: int | None = None,
        rate_limit_per_hour: int | None = None,
    ) -> ActorSubscription:
        """
        Create an Actor subscription policy binding.

        Contract:
        - Canonical constructor-owned mutation path for subscription policy.
        - Deterministic id derived from (actor_id, event_config_condition_config_scope_id, name).
        - `event_config_action_config_ids` seeds optional `event_config_action_configs` scope.
          If empty, runtime treats all enabled event actions as eligible.
        """

        payload = {
            "actor_id": actor_id,
            "event_config_condition_config_scope_id": event_config_condition_config_scope_id,
            "name": name,
            "description": description,
            "action_type": action_type,
            "event_config_action_config_ids": event_config_action_config_ids,
            "addressing_policy": addressing_policy,
            "is_enabled": is_enabled,
            "status": status,
            "filter_mode": filter_mode,
            "filter_config": filter_config,
            "priority": priority,
            "batch_mode": batch_mode,
            "batch_window_ms": batch_window_ms,
            "max_batch_size": max_batch_size,
            "require_read_access": require_read_access,
            "check_ownership": check_ownership,
            "rate_limit_per_minute": rate_limit_per_minute,
            "rate_limit_per_hour": rate_limit_per_hour,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_actor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorSubscription):
            return value
        return ActorSubscription.validate_invocation_value(value)


class ActorSubscriptionRecordEventInput(BaseModel):
    event_config_condition_config_scope_event_id: UUID
    status: SubscriptionActivationStatus = Field(default=SubscriptionActivationStatus.ready)
    reason: str | None = Field(default=None)


class ActorSubscriptionRecordEventOutput(BaseModel):
    value: ActorSubscriptionEvent


class ActorSubscriptionCreateViaActorInput(BaseModel):
    actor_id: UUID = Field(description="Foreign key for Actor.actor_subscriptions")
    event_config_condition_config_scope_id: UUID
    name: str
    description: str | None = Field(default=None)
    action_type: str | None = Field(default=None)
    event_config_action_config_ids: list[UUID] = Field(default_factory=list)
    addressing_policy: SubscriptionAddressingPolicy = Field(default=SubscriptionAddressingPolicy.any)
    is_enabled: bool = Field(default=True)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.active)
    filter_mode: SubscriptionFilterMode = Field(default=SubscriptionFilterMode.all_instances)
    filter_config: JsonObject | None = Field(default=None)
    priority: int = Field(default=0)
    batch_mode: bool = Field(default=False)
    batch_window_ms: int = Field(default=1000)
    max_batch_size: int = Field(default=100)
    require_read_access: bool = Field(default=True)
    check_ownership: bool = Field(default=True)
    rate_limit_per_minute: int | None = Field(default=None)
    rate_limit_per_hour: int | None = Field(default=None)


class ActorSubscriptionCreateViaActorOutput(BaseModel):
    value: ActorSubscription


FUNCTIONS = {
    "ActorSubscription": {
        "record_event": {
            "canonical": {
                "name": "record_event",
                "description": "Record an activation lifecycle entry for this subscription against\na scope-level event. Containment-rail constructor: identity flows\nthrough the `actor_subscription_events` member path.",
                "is_constructor": False,
            },
            "input": ActorSubscriptionRecordEventInput,
            "output": ActorSubscriptionRecordEventOutput,
        },
        "create_via_actor": {
            "canonical": {
                "name": "create_via_actor",
                "description": "Create an Actor subscription policy binding.\n\nContract:\n- Canonical constructor-owned mutation path for subscription policy.\n- Deterministic id derived from (actor_id, event_config_condition_config_scope_id, name).\n- `event_config_action_config_ids` seeds optional `event_config_action_configs` scope.\n  If empty, runtime treats all enabled event actions as eligible.",
                "is_constructor": True,
            },
            "input": ActorSubscriptionCreateViaActorInput,
            "output": ActorSubscriptionCreateViaActorOutput,
        },
    },
}

__all__ = [
    "ActorSubscription",
    "ActorSubscriptionRecordEventInput",
    "ActorSubscriptionRecordEventOutput",
    "ActorSubscriptionCreateViaActorInput",
    "ActorSubscriptionCreateViaActorOutput",
    "FUNCTIONS",
]
