from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.action.action_enums import ActionIntentStatus
from aware_reactivity_ontology.event.event_enums import EventStatus
from aware_reactivity_ontology.action.action import Action
from aware_reactivity_ontology.action.action_intent import ActionIntent
from aware_reactivity_ontology.event.event import Event
from aware_reactivity_ontology.event.event_condition import EventCondition

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_event_id

# --- AWARE: USER_IMPORTS END


async def create(
    config_id: UUID, activation_id: UUID, event_type: str, source: str, status: EventStatus = EventStatus.raised
) -> Event:
    """
    Create runtime event evidence anchored to one activation.
    """

    # --- AWARE: LOGIC START create
    return Event(
        id=stable_event_id(config_id=config_id, activation_id=activation_id),
        config_id=config_id,
        activation_id=activation_id,
        event_type=event_type,
        source=source,
        status=status,
    )
    # --- AWARE: LOGIC END create


async def add_event_condition(
    event: Event,
    condition_id: UUID,
    config_id: UUID,
    matched: bool = True,
    evaluation_context: JsonObject = JsonObject(),
) -> EventCondition:
    """
    Link one evaluated condition evidence record to this event.
    """

    # --- AWARE: LOGIC START add_event_condition
    created = await EventCondition.create_via_event(
        event_id=event.id,
        condition_id=condition_id,
        config_id=config_id,
        matched=matched,
        evaluation_context=dict(evaluation_context),
    )

    for existing in event.event_conditions:
        if existing.id == created.id:
            return existing

    event.event_conditions.append(created)
    return created
    # --- AWARE: LOGIC END add_event_condition


async def add_action(event: Event, config_id: UUID, execution_context: JsonObject = JsonObject()) -> Action:
    """
    Link one action evidence record to this event.
    """

    # --- AWARE: LOGIC START add_action
    created = await Action.create_via_event(
        event_id=event.id,
        config_id=config_id,
        execution_context=dict(execution_context),
    )
    for existing in event.actions:
        if existing.id == created.id:
            return existing

    event.actions.append(created)
    return created
    # --- AWARE: LOGIC END add_action


async def add_action_intent(
    event: Event,
    config_id: UUID,
    intent_key: str,
    action_type: str | None = None,
    actor_id: UUID | None = None,
    target_actor_id: UUID | None = None,
    actor_subscription_id: UUID | None = None,
    action_payload: JsonObject = JsonObject(),
    payload_class_config_id: UUID | None = None,
    subscription_filter_config: JsonObject = JsonObject(),
    priority: int = 0,
    status: ActionIntentStatus = ActionIntentStatus.requested,
) -> ActionIntent:
    """
    Link one commit-backed action intent evidence record to this event.

    Contract:
    - `intent_key` is caller-supplied and opaque to Reactivity.
    - Actor/subscription args are deprecated provenance mirrors retained for
      bridge compatibility during the C2 cleanup window.
    """

    # --- AWARE: LOGIC START add_action_intent
    created = await ActionIntent.create_via_event(
        event_id=event.id,
        config_id=config_id,
        intent_key=intent_key,
        action_type=action_type,
        actor_id=actor_id,
        target_actor_id=target_actor_id,
        actor_subscription_id=actor_subscription_id,
        action_payload=dict(action_payload),
        payload_class_config_id=payload_class_config_id,
        subscription_filter_config=dict(subscription_filter_config),
        priority=priority,
        status=status,
    )
    for existing in event.action_intents:
        if existing.id == created.id:
            return existing

    event.action_intents.append(created)
    return created
    # --- AWARE: LOGIC END add_action_intent
