from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.action.action_enums import (
    ActionExecutionStatus,
    ActionIntentStatus,
)
from aware_reactivity_ontology.action.action_execution import ActionExecution
from aware_reactivity_ontology.action.action_intent import ActionIntent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id
from aware_reactivity.stable_ids import stable_action_intent_id

# --- AWARE: USER_IMPORTS END


async def start_execution(
    action_intent: ActionIntent,
    execution_key: str = "primary",
    status: ActionExecutionStatus = ActionExecutionStatus.created,
    execution_context: JsonObject = JsonObject(),
) -> ActionExecution:
    """
    Create one service-fulfillment execution promise for this intent.
    """

    # --- AWARE: LOGIC START start_execution
    created = await ActionExecution.create_via_action_intent(
        action_intent_id=action_intent.id,
        execution_key=execution_key,
        status=status,
        execution_context=dict(execution_context),
    )

    for existing in action_intent.action_executions:
        if existing.id == created.id:
            return existing

    action_intent.action_executions.append(created)
    return created
    # --- AWARE: LOGIC END start_execution


async def set_status(action_intent: ActionIntent, status: ActionIntentStatus) -> None:
    """
    Update intent status without mutating execution lifecycle truth.
    """

    # --- AWARE: LOGIC START set_status
    action_intent.status = status
    # --- AWARE: LOGIC END set_status


async def create_via_event(
    event_id: UUID,
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
    Create commit-backed Reactivity action intent evidence for a raised event.

    Contract:
    - This is the canonical "should react" record.
    - Stable-id migration B1: deterministic id is derived from event,
      action config, and caller-supplied `intent_key`; actor subscription no
      longer participates in identity.
    - `payload_model` is typed request payload evidence. Its ClassConfig is
      supplied by the Experience/API resolver; Reactivity remains API-agnostic.
    - `action_payload` is deprecated compatibility metadata only.
    - Actor/subscription fields are deprecated provenance mirrors; caller
      provenance lives in the bridge/Experience receipt rails.
    """

    # --- AWARE: LOGIC START create_via_event
    normalized_intent_key = str(intent_key or "").strip()
    if not normalized_intent_key:
        raise RuntimeError("ActionIntent.create_via_event requires non-empty intent_key")

    action_intent_id = stable_action_intent_id(
        event_id=event_id,
        config_id=config_id,
        intent_key=normalized_intent_key,
    )
    payload_model = None
    if payload_class_config_id is not None:
        payload_model = InlineValueInstance(
            id=stable_inline_value_instance_id(
                class_config_id=payload_class_config_id,
                owner_key=action_intent_id,
            ),
            class_config_id=payload_class_config_id,
            owner_key=action_intent_id,
            attributes=[],
        )
    return ActionIntent(
        id=action_intent_id,
        event_id=event_id,
        config_id=config_id,
        intent_key=normalized_intent_key,
        actor_subscription_id=actor_subscription_id,
        action_type=action_type,
        actor_id=actor_id,
        target_actor_id=target_actor_id,
        action_payload=dict(action_payload),
        payload_model_id=(payload_model.id if payload_model is not None else None),
        payload_model=payload_model,
        subscription_filter_config=dict(subscription_filter_config),
        priority=priority,
        status=status,
    )
    # --- AWARE: LOGIC END create_via_event
