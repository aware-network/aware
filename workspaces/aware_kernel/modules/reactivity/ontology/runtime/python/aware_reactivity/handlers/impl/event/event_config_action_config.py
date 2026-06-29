from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.event.event_config_action_config import EventConfigActionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_event_config_action_config_id

# --- AWARE: USER_IMPORTS END


async def create_via_event_config(
    event_config_id: UUID,
    action_config_id: UUID,
    execution_order: int = 0,
    priority: int = 0,
    is_enabled: bool = True,
    is_required: bool = False,
    continue_on_fail: bool = True,
) -> EventConfigActionConfig:
    """
    Create a canonical event-to-action binding policy node.
    """

    # --- AWARE: LOGIC START create_via_event_config
    return EventConfigActionConfig(
        id=stable_event_config_action_config_id(
            event_config_id=event_config_id,
            action_config_id=action_config_id,
        ),
        event_config_id=event_config_id,
        action_config_id=action_config_id,
        execution_order=execution_order,
        priority=priority,
        is_enabled=is_enabled,
        is_required=is_required,
        continue_on_fail=continue_on_fail,
    )
    # --- AWARE: LOGIC END create_via_event_config
