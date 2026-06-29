from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.event.event_enums import (
    EventDeliveryMode,
    EventPriority,
    EventType,
)
from aware_reactivity_ontology.event.event_config import EventConfig
from aware_reactivity_ontology.event.event_config_action_config import EventConfigActionConfig
from aware_reactivity_ontology.event.event_config_condition_config import EventConfigConditionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import (
    stable_event_config_action_config_id,
    stable_event_config_condition_config_id,
    stable_event_config_id,
)

# --- AWARE: USER_IMPORTS END


async def create(
    name: str,
    description: str,
    event_type: EventType = EventType.condition,
    delivery_mode: EventDeliveryMode = EventDeliveryMode.immediate,
    priority: EventPriority = EventPriority.normal,
    is_enabled: bool = True,
    is_system: bool = False,
    require_authentication: bool = True,
    valid_sources: list[str] = [],
    allowed_roles: list[str] = [],
    event_schema: JsonObject = JsonObject(),
    batch_window_ms: int | None = None,
) -> EventConfig:
    """
    Create a canonical event policy root.
    """

    # --- AWARE: LOGIC START create
    return EventConfig(
        id=stable_event_config_id(name=name),
        name=name,
        description=description,
        event_type=event_type,
        delivery_mode=delivery_mode,
        priority=priority,
        is_enabled=is_enabled,
        is_system=is_system,
        require_authentication=require_authentication,
        valid_sources=list(valid_sources),
        allowed_roles=list(allowed_roles),
        event_schema=dict(event_schema),
        batch_window_ms=batch_window_ms,
    )
    # --- AWARE: LOGIC END create


async def add_condition_config(
    event_config: EventConfig,
    condition_config_id: UUID,
    execution_order: int = 0,
    priority: int = 0,
    is_enabled: bool = True,
    is_required: bool = False,
    continue_on_fail: bool = True,
    stop_on_match: bool = False,
    cache_result: bool = False,
    cache_ttl_seconds: int | None = None,
) -> EventConfigConditionConfig:
    """
    Link this EventConfig to a ConditionConfig via a canonical binding edge.
    """

    # --- AWARE: LOGIC START add_condition_config
    event_config_id = event_config.id
    if event_config_id is None:
        raise RuntimeError("EventConfig.add_condition_config requires EventConfig.id")

    expected_id = stable_event_config_condition_config_id(
        event_config_id=event_config_id,
        condition_config_id=condition_config_id,
    )
    for existing in event_config.event_config_condition_configs:
        if existing.id == expected_id:
            return existing

    created = await EventConfigConditionConfig.create_via_event_config(
        event_config_id=event_config_id,
        condition_config_id=condition_config_id,
        execution_order=execution_order,
        priority=priority,
        is_enabled=is_enabled,
        is_required=is_required,
        continue_on_fail=continue_on_fail,
        stop_on_match=stop_on_match,
        cache_result=cache_result,
        cache_ttl_seconds=cache_ttl_seconds,
    )
    event_config.event_config_condition_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_condition_config


async def add_action_config(
    event_config: EventConfig,
    action_config_id: UUID,
    execution_order: int = 0,
    priority: int = 0,
    is_enabled: bool = True,
    is_required: bool = False,
    continue_on_fail: bool = True,
) -> EventConfigActionConfig:
    """
    Link this EventConfig to an ActionConfig via a canonical binding edge.
    """

    # --- AWARE: LOGIC START add_action_config
    event_config_id = event_config.id
    if event_config_id is None:
        raise RuntimeError("EventConfig.add_action_config requires EventConfig.id")

    expected_id = stable_event_config_action_config_id(
        event_config_id=event_config_id,
        action_config_id=action_config_id,
    )
    for existing in event_config.event_config_action_configs:
        if existing.id == expected_id:
            return existing

    created = await EventConfigActionConfig.create_via_event_config(
        event_config_id=event_config_id,
        action_config_id=action_config_id,
        execution_order=execution_order,
        priority=priority,
        is_enabled=is_enabled,
        is_required=is_required,
        continue_on_fail=continue_on_fail,
    )
    event_config.event_config_action_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_action_config


async def update_sources(event_config: EventConfig, p_event_config_id: UUID, p_valid_sources: list[str]) -> None:
    """
    Updates the valid sources for an event config, ensuring uniqueness and order.
    Parameters: p_event_config_id: The UUID of the event config to update.
    p_valid_sources: Array of valid source identifiers.
    Returns: void
    """

    # --- AWARE: LOGIC START update_sources
    if p_event_config_id != event_config.id:
        raise ValueError(
            "event_config_id mismatch for update_sources: "
            f"event_config.id={event_config.id} p_event_config_id={p_event_config_id}"
        )

    deduped_sources: list[str] = []
    seen: set[str] = set()
    for source in p_valid_sources:
        candidate = source.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        deduped_sources.append(candidate)

    event_config.valid_sources = deduped_sources
    # --- AWARE: LOGIC END update_sources
