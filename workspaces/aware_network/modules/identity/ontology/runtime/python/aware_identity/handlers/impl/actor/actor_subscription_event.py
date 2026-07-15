from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.actor.actor_subscription_enums import SubscriptionActivationStatus
from aware_identity_ontology.actor.actor_subscription_event import ActorSubscriptionEvent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import (
    stable_actor_subscription_event_id,
)

# --- AWARE: USER_IMPORTS END


async def set_status(
    actor_subscription_event: ActorSubscriptionEvent, status: SubscriptionActivationStatus, reason: str | None = None
) -> ActorSubscriptionEvent:
    """
    Update activation lifecycle state on an existing ActorSubscriptionEvent record.
    """

    # --- AWARE: LOGIC START set_status
    actor_subscription_event.status = status
    actor_subscription_event.reason = reason
    return actor_subscription_event
    # --- AWARE: LOGIC END set_status


async def build_via_actor_subscription(
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

    # --- AWARE: LOGIC START build_via_actor_subscription
    return ActorSubscriptionEvent(
        id=stable_actor_subscription_event_id(
            actor_subscription_id=actor_subscription_id,
            event_config_condition_config_scope_event_id=event_config_condition_config_scope_event_id,
        ),
        actor_subscription_id=actor_subscription_id,
        event_config_condition_config_scope_event_id=event_config_condition_config_scope_event_id,
        status=status,
        reason=reason,
    )
    # --- AWARE: LOGIC END build_via_actor_subscription
