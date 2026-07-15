from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.event.event_config_condition_config import EventConfigConditionConfig
from aware_reactivity_ontology.event.event_config_condition_config_scope import EventConfigConditionConfigScope

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_event_config_condition_config_id

# --- AWARE: USER_IMPORTS END


async def create_scope(
    event_config_condition_config: EventConfigConditionConfig,
    object_instance_graph_identity_id: UUID,
    scope_key: str = "lane",
    object_instance_graph_branch_id: UUID | None = None,
    class_instance_identity_id: UUID | None = None,
) -> EventConfigConditionConfigScope:
    """
    Create one scope rail under this event-condition policy binding.

    Contract:
    - Optional class_instance_identity_id creates an instance-scoped lane.
    - Multiple instance scopes may coexist under the same event-condition
      binding when their non-null scope_key differs. The optional typed
      relationships remain the semantic authority for branch/instance scope.
    """

    # --- AWARE: LOGIC START create_scope
    event_config_condition_config_id = event_config_condition_config.id
    if event_config_condition_config_id is None:
        raise RuntimeError("EventConfigConditionConfig.create_scope requires EventConfigConditionConfig.id")

    created = await EventConfigConditionConfigScope.create_via_event_config_condition_config(
        event_config_condition_config_id=event_config_condition_config_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        scope_key=scope_key,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        class_instance_identity_id=class_instance_identity_id,
    )
    for existing in event_config_condition_config.event_config_condition_config_scopes:
        if existing.id == created.id:
            return existing

    event_config_condition_config.event_config_condition_config_scopes.append(created)
    return created
    # --- AWARE: LOGIC END create_scope


async def create_via_event_config(
    event_config_id: UUID,
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
    Create a canonical event-to-condition binding policy node.

    Contract:
    - Constructor-owned creation path for event-condition links.
    - Binding references are explicit via event_config_id and condition_config_id.
    """

    # --- AWARE: LOGIC START create_via_event_config
    return EventConfigConditionConfig(
        id=stable_event_config_condition_config_id(
            event_config_id=event_config_id,
            condition_config_id=condition_config_id,
        ),
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
    # --- AWARE: LOGIC END create_via_event_config
