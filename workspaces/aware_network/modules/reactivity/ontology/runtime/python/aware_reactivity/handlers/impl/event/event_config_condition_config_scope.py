from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.event.event_config_condition_config_scope import EventConfigConditionConfigScope
from aware_reactivity_ontology.event.event_config_condition_config_scope_event import (
    EventConfigConditionConfigScopeEvent,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import (
    stable_event_config_condition_config_scope_id,
)

# --- AWARE: USER_IMPORTS END


async def add_event(
    event_config_condition_config_scope: EventConfigConditionConfigScope, event_id: UUID
) -> EventConfigConditionConfigScopeEvent:
    """
    Attach one runtime event evidence record to this scope lane.
    """

    # --- AWARE: LOGIC START add_event
    event_config_condition_config_scope_id = event_config_condition_config_scope.id
    if event_config_condition_config_scope_id is None:
        raise RuntimeError("EventConfigConditionConfigScope.add_event requires EventConfigConditionConfigScope.id")

    created = await EventConfigConditionConfigScopeEvent.create_via_event_config_condition_config_scope(
        event_config_condition_config_scope_id=event_config_condition_config_scope_id,
        event_id=event_id,
    )
    for existing in event_config_condition_config_scope.event_config_condition_config_scope_events:
        if existing.id == created.id:
            return existing

    event_config_condition_config_scope.event_config_condition_config_scope_events.append(created)
    return created
    # --- AWARE: LOGIC END add_event


async def create_via_event_config_condition_config(
    event_config_condition_config_id: UUID,
    object_instance_graph_identity_id: UUID,
    scope_key: str = "lane",
    object_instance_graph_branch_id: UUID | None = None,
    class_instance_identity_id: UUID | None = None,
) -> EventConfigConditionConfigScope:
    """
    Create a canonical lane scope for one EventConfigConditionConfig binding.

    Contract:
    - Event-first scope rail for condition activation matching.
    - Deterministic id derived from binding id + OIGI + non-null
      scope_key. The key is a materializable discriminator for the typed
      optional branch/ClassInstanceIdentity relationships; those
      relationships remain the semantic authority.
    - When class_instance_identity is present, the condition only matches
      commit candidates for that exact instance.
    - Reactivity owns only Meta scope truth here. Experience may lower
      graph-binding node aliases into this scope, but Reactivity never
      imports Experience or projection-node ontology.
    """

    # --- AWARE: LOGIC START create_via_event_config_condition_config
    if class_instance_identity_id is not None:
        branch_part = (
            f"branch:{object_instance_graph_branch_id}" if object_instance_graph_branch_id is not None else "branch:all"
        )
        normalized_scope_key = f"{branch_part}|class_instance:{class_instance_identity_id}"
    elif object_instance_graph_branch_id is not None:
        normalized_scope_key = f"branch:{object_instance_graph_branch_id}"
    else:
        normalized_scope_key = (scope_key or "").strip() or "lane"
    return EventConfigConditionConfigScope(
        id=stable_event_config_condition_config_scope_id(
            event_config_condition_config_id=event_config_condition_config_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            scope_key=normalized_scope_key,
        ),
        event_config_condition_config_id=event_config_condition_config_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        scope_key=normalized_scope_key,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        class_instance_identity_id=class_instance_identity_id,
    )
    # --- AWARE: LOGIC END create_via_event_config_condition_config
