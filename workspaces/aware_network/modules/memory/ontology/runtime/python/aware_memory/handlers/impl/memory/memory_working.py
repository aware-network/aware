from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Memory Ontology
from aware_memory_ontology.memory.memory_working_item_enums import MemoryWorkingItemKind
from aware_memory_ontology.memory.memory_working import MemoryWorking
from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_content_ontology.chain.content_chain import ContentChain
from aware_memory_ontology.memory.memory_working_content_frame import (
    MemoryWorkingContentFrame,
)
from aware_memory_ontology.memory.memory_working_event_frame import (
    MemoryWorkingEventFrame,
)
from aware_memory_ontology.memory.memory_working_tool_frame import (
    MemoryWorkingToolFrame,
)
from aware_memory_ontology.stable_ids import (
    stable_memory_working_id,
    stable_memory_working_item_id,
)


def _next_item_position(memory_working: MemoryWorking) -> int:
    if not memory_working.items:
        return 0
    positions = [int(item.position) for item in memory_working.items]
    if not positions:
        return 0
    return max(positions) + 1


# --- AWARE: USER_IMPORTS END


async def build(actor_id: UUID, key: str = "default") -> MemoryWorking:
    """
    Create one deterministic standalone MemoryWorking lane for an Identity Actor.

    Policy:
    - Memory owns the lane object and references Identity Actor relationally.
    - Stable identity is actor plus `key`.
    - The lane may be branched/forked without collapsing into non-branchable Actor identity.
    - ContentChain must be created via ContentChain.build (no direct instantiation).
    """

    # --- AWARE: LOGIC START build
    key_norm = (key or "").strip().casefold() or "default"
    memory_working_id = stable_memory_working_id(actor_id=actor_id, key=key_norm)
    content_chain = await ContentChain.build()
    return MemoryWorking(
        id=memory_working_id,
        actor_id=actor_id,
        key=key_norm,
        content_chain_id=content_chain.id,
        content_chain=content_chain,
    )
    # --- AWARE: LOGIC END build


async def create_item(
    memory_working: MemoryWorking,
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
    Construct one item under this MemoryWorking lane.

    Contract:
    - Parent->child containment is explicit (`items.build`) so propagation
      can mark `memory_working_id` as child identity rail.
    """

    # --- AWARE: LOGIC START create_item
    item = await MemoryWorkingItem.build_via_memory_working(
        memory_working_id=memory_working.id,
        kind=kind,
        position=position,
        created_at=created_at,
        event_frame_id=event_frame_id,
        content_frame_id=content_frame_id,
        tool_frame_id=tool_frame_id,
        attention_transition_id=attention_transition_id,
        rationale=rationale,
        summary=summary,
    )
    if all(existing.id != item.id for existing in memory_working.items):
        memory_working.items.append(item)
    return item
    # --- AWARE: LOGIC END create_item


async def add_event_item(
    memory_working: MemoryWorking,
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
    rationale: str | None = None,
    summary: str | None = None,
) -> MemoryWorkingItem:
    """
    Appends an `event` memory item.
    """

    # --- AWARE: LOGIC START add_event_item
    position = _next_item_position(memory_working)
    item_id = stable_memory_working_item_id(
        memory_working_id=memory_working.id,
        position=position,
        kind=MemoryWorkingItemKind.event.value,
    )
    frame = await MemoryWorkingEventFrame.build_via_memory_working_item(
        memory_working_item_id=item_id,
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
    return await create_item(
        memory_working,
        kind=MemoryWorkingItemKind.event,
        position=position,
        event_frame_id=frame.id,
        rationale=rationale,
        summary=summary,
    )
    # --- AWARE: LOGIC END add_event_item


async def add_content_item(
    memory_working: MemoryWorking, content_id: UUID, rationale: str | None = None, summary: str | None = None
) -> MemoryWorkingItem:
    """
    Appends a `content` memory item.
    """

    # --- AWARE: LOGIC START add_content_item
    position = _next_item_position(memory_working)
    item_id = stable_memory_working_item_id(
        memory_working_id=memory_working.id,
        position=position,
        kind=MemoryWorkingItemKind.content.value,
    )
    frame = await MemoryWorkingContentFrame.build_via_memory_working_item(
        memory_working_item_id=item_id,
        content_id=content_id,
    )
    return await create_item(
        memory_working,
        kind=MemoryWorkingItemKind.content,
        position=position,
        content_frame_id=frame.id,
        rationale=rationale,
        summary=summary,
    )
    # --- AWARE: LOGIC END add_content_item


async def add_tool_item(
    memory_working: MemoryWorking,
    tool_call_id: UUID,
    tool_response_id: UUID | None = None,
    object_instance_graph_branch_id: UUID | None = None,
    projection_hash: str | None = None,
    rationale: str | None = None,
    summary: str | None = None,
) -> MemoryWorkingItem:
    """
    Appends a `tool` memory item.
    """

    # --- AWARE: LOGIC START add_tool_item
    position = _next_item_position(memory_working)
    item_id = stable_memory_working_item_id(
        memory_working_id=memory_working.id,
        position=position,
        kind=MemoryWorkingItemKind.tool.value,
    )
    frame = await MemoryWorkingToolFrame.build_via_memory_working_item(
        memory_working_item_id=item_id,
        tool_call_id=tool_call_id,
        tool_response_id=tool_response_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        projection_hash=projection_hash,
    )
    return await create_item(
        memory_working,
        kind=MemoryWorkingItemKind.tool,
        position=position,
        tool_frame_id=frame.id,
        rationale=rationale,
        summary=summary,
    )
    # --- AWARE: LOGIC END add_tool_item


async def add_attention_item(
    memory_working: MemoryWorking,
    attention_focus_transition_id: UUID,
    rationale: str | None = None,
    summary: str | None = None,
) -> MemoryWorkingItem:
    """
    Appends an `attention` memory item by retaining an Attention-owned
    focus transition.
    """

    # --- AWARE: LOGIC START add_attention_item
    position = _next_item_position(memory_working)
    return await create_item(
        memory_working,
        kind=MemoryWorkingItemKind.attention,
        position=position,
        attention_transition_id=attention_focus_transition_id,
        rationale=rationale,
        summary=summary,
    )
    # --- AWARE: LOGIC END add_attention_item
