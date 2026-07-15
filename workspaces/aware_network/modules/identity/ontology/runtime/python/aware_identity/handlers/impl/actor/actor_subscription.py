from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.actor.actor_subscription_enums import (
    SubscriptionActivationStatus,
    SubscriptionAddressingPolicy,
    SubscriptionFilterMode,
    SubscriptionStatus,
)
from aware_identity_ontology.actor.actor_subscription import ActorSubscription
from aware_identity_ontology.actor.actor_subscription_event import ActorSubscriptionEvent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_actor_subscription_id
from aware_reactivity_ontology.event.event_config_action_config import (
    EventConfigActionConfig,
)

# --- AWARE: USER_IMPORTS END


async def record_event(
    actor_subscription: ActorSubscription,
    event_config_condition_config_scope_event_id: UUID,
    status: SubscriptionActivationStatus = SubscriptionActivationStatus.ready,
    reason: str | None = None,
) -> ActorSubscriptionEvent:
    """
    Record an activation lifecycle entry for this subscription against
    a scope-level event. Containment-rail constructor: identity flows
    through the `actor_subscription_events` member path.
    """

    # --- AWARE: LOGIC START record_event
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END record_event


async def create_via_actor(
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

    # --- AWARE: LOGIC START create_via_actor
    selected_action_bindings = [
        EventConfigActionConfig.model_construct(id=action_binding_id)
        for action_binding_id in list(event_config_action_config_ids or [])
        if isinstance(action_binding_id, UUID)
    ]
    return ActorSubscription(
        id=stable_actor_subscription_id(
            actor_id=actor_id,
            event_config_condition_config_scope_id=event_config_condition_config_scope_id,
            name=name,
        ),
        actor_id=actor_id,
        event_config_condition_config_scope_id=event_config_condition_config_scope_id,
        name=name,
        description=description,
        action_type=action_type,
        addressing_policy=addressing_policy,
        event_config_action_configs=selected_action_bindings,
        is_enabled=is_enabled,
        status=status,
        filter_mode=filter_mode,
        filter_config=filter_config,
        priority=priority,
        batch_mode=batch_mode,
        batch_window_ms=batch_window_ms,
        max_batch_size=max_batch_size,
        require_read_access=require_read_access,
        check_ownership=check_ownership,
        rate_limit_per_minute=rate_limit_per_minute,
        rate_limit_per_hour=rate_limit_per_hour,
    )
    # --- AWARE: LOGIC END create_via_actor
