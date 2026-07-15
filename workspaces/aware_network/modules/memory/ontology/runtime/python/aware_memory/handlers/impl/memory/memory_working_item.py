from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.session.attention_focus_transition import AttentionFocusTransition

# Memory Ontology
from aware_memory_ontology.memory.memory_working_item_enums import MemoryWorkingItemKind
from aware_memory_ontology.memory.memory_working_content_frame import MemoryWorkingContentFrame
from aware_memory_ontology.memory.memory_working_event_frame import MemoryWorkingEventFrame
from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem
from aware_memory_ontology.memory.memory_working_tool_frame import MemoryWorkingToolFrame

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from datetime import timezone

from aware_memory.memory_working_item_frame_support import (
    require_matching_content_frame,
    require_matching_event_frame,
    require_matching_tool_frame,
    require_working_item_kind,
    resolve_content_frame,
    resolve_event_frame,
    resolve_tool_frame,
)
from aware_attention_ontology.session.attention_focus_transition import (
    AttentionFocusTransition,
)
from aware_memory_ontology.stable_ids import stable_memory_working_item_id

# --- AWARE: USER_IMPORTS END


async def create_event_frame(
    memory_working_item: MemoryWorkingItem,
    event_id: UUID,
    event_config_id: UUID | None = None,
    event_activation_id: UUID | None = None,
    event_type: str | None = None,
    event_source: str | None = None,
    event_status: str | None = None,
    commit_branch_id: UUID | None = None,
    commit_projection_hash: str | None = None,
    commit_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    object_instance_graph_commit_id: UUID | None = None,
    action_intent_id: UUID | None = None,
    intent_key: str | None = None,
    action_config_id: UUID | None = None,
    action_execution_id: UUID | None = None,
    action_execution_key: str | None = None,
    api_call_key: UUID | None = None,
    action_binding_id: UUID | None = None,
    action_experience_id: UUID | None = None,
    environment_profile_id: UUID | None = None,
    environment_event_id: UUID | None = None,
    invocation_config_id: UUID | None = None,
    endpoint_id: UUID | None = None,
    actor_subscription_id: UUID | None = None,
) -> MemoryWorkingEventFrame:
    """
    Construct one event frame under this item (kind=event).
    """

    # --- AWARE: LOGIC START create_event_frame
    require_working_item_kind(memory_working_item, MemoryWorkingItemKind.event)
    frame = await MemoryWorkingEventFrame.build_via_memory_working_item(
        memory_working_item_id=memory_working_item.id,
        event_id=event_id,
        event_config_id=event_config_id,
        event_activation_id=event_activation_id,
        event_type=event_type,
        event_source=event_source,
        event_status=event_status,
        commit_branch_id=commit_branch_id,
        commit_projection_hash=commit_projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        action_intent_id=action_intent_id,
        intent_key=intent_key,
        action_config_id=action_config_id,
        action_execution_id=action_execution_id,
        action_execution_key=action_execution_key,
        api_call_key=api_call_key,
        action_binding_id=action_binding_id,
        action_experience_id=action_experience_id,
        environment_profile_id=environment_profile_id,
        environment_event_id=environment_event_id,
        invocation_config_id=invocation_config_id,
        endpoint_id=endpoint_id,
        actor_subscription_id=actor_subscription_id,
    )
    existing = resolve_event_frame(memory_working_item)
    if existing is not None:
        require_matching_event_frame(existing=existing, built=frame)
        memory_working_item.event_frame = existing
        return existing
    memory_working_item.event_frame = frame
    return frame
    # --- AWARE: LOGIC END create_event_frame


async def create_content_frame(memory_working_item: MemoryWorkingItem, content_id: UUID) -> MemoryWorkingContentFrame:
    """
    Construct one content frame under this item (kind=content).
    """

    # --- AWARE: LOGIC START create_content_frame
    require_working_item_kind(memory_working_item, MemoryWorkingItemKind.content)
    frame = await MemoryWorkingContentFrame.build_via_memory_working_item(
        memory_working_item_id=memory_working_item.id,
        content_id=content_id,
    )
    existing = resolve_content_frame(memory_working_item)
    if existing is not None:
        require_matching_content_frame(existing=existing, built=frame)
        memory_working_item.content_frame = existing
        return existing
    memory_working_item.content_frame = frame
    return frame
    # --- AWARE: LOGIC END create_content_frame


async def create_tool_frame(
    memory_working_item: MemoryWorkingItem,
    tool_call_id: UUID,
    tool_response_id: UUID | None = None,
    object_instance_graph_branch_id: UUID | None = None,
    projection_hash: str | None = None,
) -> MemoryWorkingToolFrame:
    """
    Construct one tool frame under this item (kind=tool).
    """

    # --- AWARE: LOGIC START create_tool_frame
    require_working_item_kind(memory_working_item, MemoryWorkingItemKind.tool)
    frame = await MemoryWorkingToolFrame.build_via_memory_working_item(
        memory_working_item_id=memory_working_item.id,
        tool_call_id=tool_call_id,
        tool_response_id=tool_response_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        projection_hash=projection_hash,
    )
    existing = resolve_tool_frame(memory_working_item)
    if existing is not None:
        require_matching_tool_frame(existing=existing, built=frame)
        memory_working_item.tool_frame = existing
        return existing
    memory_working_item.tool_frame = frame
    return frame
    # --- AWARE: LOGIC END create_tool_frame


async def link_attention_transition(
    memory_working_item: MemoryWorkingItem, attention_focus_transition_id: UUID
) -> AttentionFocusTransition:
    """
    Link this memory item to one Attention-owned focus transition.

    Memory records retention of the transition; it does not copy the
    transition's focus/layout/view envelope.
    """

    # --- AWARE: LOGIC START link_attention_transition
    require_working_item_kind(memory_working_item, MemoryWorkingItemKind.attention)
    transition = AttentionFocusTransition.by_id_cached(attention_focus_transition_id)
    if transition is None:
        raise RuntimeError(
            "MemoryWorkingItem.link_attention_transition requires transition to exist in-lane: "
            f"attention_focus_transition_id={attention_focus_transition_id}"
        )
    memory_working_item.attention_transition_id = attention_focus_transition_id
    memory_working_item.attention_transition = transition
    return transition
    # --- AWARE: LOGIC END link_attention_transition


async def build_via_memory_working(
    memory_working_id: UUID,
    kind: MemoryWorkingItemKind,
    position: int,
    created_at: datetime | None = None,
    event_frame_id: UUID | None = None,
    content_frame_id: UUID | None = None,
    tool_frame_id: UUID | None = None,
    attention_transition_id: UUID | None = None,
    rationale: str | None = None,
    summary: str | None = None,
) -> MemoryWorkingItem:
    """
    Builds a deterministic MemoryWorkingItem envelope.
    """

    # --- AWARE: LOGIC START build_via_memory_working
    position_norm = int(position)
    if position_norm < 0:
        raise ValueError("MemoryWorkingItem.build_via_memory_working requires position >= 0")

    kind_value = kind.value if isinstance(kind, MemoryWorkingItemKind) else str(kind)
    if not kind_value:
        raise ValueError("MemoryWorkingItem.build_via_memory_working requires kind")

    item_id = stable_memory_working_item_id(
        memory_working_id=memory_working_id,
        position=position_norm,
        kind=kind_value,
    )
    created_at_norm = created_at or datetime.now(timezone.utc)
    item = MemoryWorkingItem(
        id=item_id,
        memory_working_id=memory_working_id,
        kind=MemoryWorkingItemKind(kind_value),
        position=position_norm,
        created_at=created_at_norm,
        attention_transition_id=attention_transition_id,
        rationale=rationale,
        summary=summary,
    )
    if event_frame_id is not None:
        event_frame = MemoryWorkingEventFrame.by_id_cached(event_frame_id)
        if event_frame is not None:
            item.event_frame = event_frame
    if content_frame_id is not None:
        content_frame = MemoryWorkingContentFrame.by_id_cached(content_frame_id)
        if content_frame is not None:
            item.content_frame = content_frame
    if tool_frame_id is not None:
        tool_frame = MemoryWorkingToolFrame.by_id_cached(tool_frame_id)
        if tool_frame is not None:
            item.tool_frame = tool_frame
    if attention_transition_id is not None:
        attention_transition = AttentionFocusTransition.by_id_cached(attention_transition_id)
        if attention_transition is not None:
            item.attention_transition = attention_transition
    return item
    # --- AWARE: LOGIC END build_via_memory_working
