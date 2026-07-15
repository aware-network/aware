from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.event.event_config_condition_config_scope_event import (
    EventConfigConditionConfigScopeEvent,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import (
    stable_event_config_condition_config_scope_event_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_event_config_condition_config_scope(
    event_config_condition_config_scope_id: UUID, event_id: UUID
) -> EventConfigConditionConfigScopeEvent:
    """
    Record canonical scope-level event activation evidence.

    Contract:
    - Event-first evidence rail: one raised Event can be linked to one or more scopes.
    - Deterministic id derived from (scope_id, event_id).
    """

    # --- AWARE: LOGIC START create_via_event_config_condition_config_scope
    return EventConfigConditionConfigScopeEvent(
        id=stable_event_config_condition_config_scope_event_id(
            event_config_condition_config_scope_id=event_config_condition_config_scope_id,
            event_id=event_id,
        ),
        event_config_condition_config_scope_id=event_config_condition_config_scope_id,
        event_id=event_id,
    )
    # --- AWARE: LOGIC END create_via_event_config_condition_config_scope
