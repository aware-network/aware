from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.action.action_enums import ActionStatus
from aware_reactivity_ontology.action.action import Action

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_action_id

# --- AWARE: USER_IMPORTS END


async def set_status(action: Action, status: ActionStatus, result_info: str | None = None) -> None:
    """
    Update runtime action status after execution handling.
    """

    # --- AWARE: LOGIC START set_status
    action.status = status
    action.result_info = result_info
    # --- AWARE: LOGIC END set_status


async def create_via_event(
    event_id: UUID,
    config_id: UUID,
    status: ActionStatus = ActionStatus.requested,
    execution_context: JsonObject = JsonObject(),
) -> Action:
    """
    Create runtime action evidence for a raised event.
    """

    # --- AWARE: LOGIC START create_via_event
    return Action(
        id=stable_action_id(event_id=event_id, config_id=config_id),
        event_id=event_id,
        config_id=config_id,
        status=status,
        execution_context=JsonObject(execution_context),
    )
    # --- AWARE: LOGIC END create_via_event
