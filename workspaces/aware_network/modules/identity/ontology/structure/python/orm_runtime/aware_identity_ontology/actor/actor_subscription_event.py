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
from aware_identity_ontology.actor.actor_subscription_enums import SubscriptionActivationStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_reactivity_ontology.event.event_config_condition_config_scope_event import (
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

    async def set_status(
        self, status: SubscriptionActivationStatus, reason: str | None = None
    ) -> ActorSubscriptionEvent:
        """Update activation lifecycle state on an existing ActorSubscriptionEvent record."""

        payload = {"status": status, "reason": reason}
        result = await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorSubscriptionEvent):
            return value
        return ActorSubscriptionEvent.validate_invocation_value(value)

    @classmethod
    async def build_via_actor_subscription(
        cls,
        actor_subscription_id: UUID,
        event_config_condition_config_scope_event_id: UUID,
        status: SubscriptionActivationStatus = SubscriptionActivationStatus.ready,
        reason: str | None = None,
    ) -> ActorSubscriptionEvent:
        """
        Record activation lifecycle state for one ActorSubscription against one scope-level event.

        Contract:
        - Parent ActorSubscription identity is propagated by constructor lowering
          via the containment path `ActorSubscription::actor_subscription_events`.
        - The child ClassInstance stable id must resolve from
          `(actor_subscription_id via path, event_config_condition_config_scope_event_id)`.
        """

        payload = {
            "actor_subscription_id": actor_subscription_id,
            "event_config_condition_config_scope_event_id": event_config_condition_config_scope_event_id,
            "status": status,
            "reason": reason,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_actor_subscription", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorSubscriptionEvent):
            return value
        return ActorSubscriptionEvent.validate_invocation_value(value)


class ActorSubscriptionEventSetStatusInput(BaseModel):
    status: SubscriptionActivationStatus
    reason: str | None = Field(default=None)


class ActorSubscriptionEventSetStatusOutput(BaseModel):
    value: ActorSubscriptionEvent


class ActorSubscriptionEventBuildViaActorSubscriptionInput(BaseModel):
    actor_subscription_id: UUID = Field(description="Foreign key for ActorSubscription.actor_subscription_events")
    event_config_condition_config_scope_event_id: UUID
    status: SubscriptionActivationStatus = Field(default=SubscriptionActivationStatus.ready)
    reason: str | None = Field(default=None)


class ActorSubscriptionEventBuildViaActorSubscriptionOutput(BaseModel):
    value: ActorSubscriptionEvent


FUNCTIONS = {
    "ActorSubscriptionEvent": {
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Update activation lifecycle state on an existing ActorSubscriptionEvent record.",
                "is_constructor": False,
            },
            "input": ActorSubscriptionEventSetStatusInput,
            "output": ActorSubscriptionEventSetStatusOutput,
        },
        "build_via_actor_subscription": {
            "canonical": {
                "name": "build_via_actor_subscription",
                "description": "Record activation lifecycle state for one ActorSubscription against one scope-level event.\n\nContract:\n- Parent ActorSubscription identity is propagated by constructor lowering\n  via the containment path `ActorSubscription::actor_subscription_events`.\n- The child ClassInstance stable id must resolve from\n  `(actor_subscription_id via path, event_config_condition_config_scope_event_id)`.",
                "is_constructor": True,
            },
            "input": ActorSubscriptionEventBuildViaActorSubscriptionInput,
            "output": ActorSubscriptionEventBuildViaActorSubscriptionOutput,
        },
    },
}

__all__ = [
    "ActorSubscriptionEvent",
    "ActorSubscriptionEventSetStatusInput",
    "ActorSubscriptionEventSetStatusOutput",
    "ActorSubscriptionEventBuildViaActorSubscriptionInput",
    "ActorSubscriptionEventBuildViaActorSubscriptionOutput",
    "FUNCTIONS",
]
