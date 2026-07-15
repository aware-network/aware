from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.event.event_config_meaning_resolver_config import EventConfigMeaningResolverConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity_ontology.stable_ids import (
    stable_event_config_meaning_resolver_config_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_event_config(
    event_config_id: UUID,
    action_config_id: UUID,
    resolver_key: str = "default",
    priority: int = 0,
    is_enabled: bool = True,
) -> EventConfigMeaningResolverConfig:
    """
    Create one typed event-to-meaning-provider action binding.
    """

    # --- AWARE: LOGIC START create_via_event_config
    normalized_resolver_key = resolver_key.casefold().strip() or "default"
    return EventConfigMeaningResolverConfig(
        id=stable_event_config_meaning_resolver_config_id(
            event_config_id=event_config_id,
            action_config_id=action_config_id,
            resolver_key=normalized_resolver_key,
        ),
        event_config_id=event_config_id,
        action_config_id=action_config_id,
        resolver_key=normalized_resolver_key,
        priority=priority,
        is_enabled=is_enabled,
    )
    # --- AWARE: LOGIC END create_via_event_config
