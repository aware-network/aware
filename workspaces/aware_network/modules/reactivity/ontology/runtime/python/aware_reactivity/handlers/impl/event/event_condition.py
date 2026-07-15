from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.event.event_condition import EventCondition

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_event_condition_id

# --- AWARE: USER_IMPORTS END


async def create_via_event(
    event_id: UUID,
    condition_id: UUID,
    config_id: UUID,
    matched: bool = True,
    evaluation_context: JsonObject = JsonObject(),
) -> EventCondition:
    """
    Create canonical condition-match evidence for a raised event.
    """

    # --- AWARE: LOGIC START create_via_event
    return EventCondition(
        id=stable_event_condition_id(
            event_id=event_id,
            condition_id=condition_id,
            config_id=config_id,
        ),
        condition_id=condition_id,
        config_id=config_id,
        event_id=event_id,
        matched=matched,
        evaluation_context=dict(evaluation_context),
    )
    # --- AWARE: LOGIC END create_via_event
