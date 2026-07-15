from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Memory Ontology
from aware_memory_ontology.memory.memory_working_tool_frame import MemoryWorkingToolFrame

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_memory_ontology.stable_ids import stable_memory_working_tool_frame_id

# --- AWARE: USER_IMPORTS END


async def build_via_memory_working_item(
    memory_working_item_id: UUID,
    tool_call_id: UUID,
    tool_response_id: UUID | None = None,
    object_instance_graph_branch_id: UUID | None = None,
    projection_hash: str | None = None,
) -> MemoryWorkingToolFrame:
    """
    Builds deterministic tool frame payload for a memory item.
    """

    # --- AWARE: LOGIC START build_via_memory_working_item
    return MemoryWorkingToolFrame(
        id=stable_memory_working_tool_frame_id(
            memory_working_item_id=memory_working_item_id,
            tool_call_id=tool_call_id,
        ),
        tool_call_id=tool_call_id,
        tool_response_id=tool_response_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        projection_hash=projection_hash,
    )
    # --- AWARE: LOGIC END build_via_memory_working_item
