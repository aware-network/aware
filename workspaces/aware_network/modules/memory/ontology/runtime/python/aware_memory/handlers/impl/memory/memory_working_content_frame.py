from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Memory Ontology
from aware_memory_ontology.memory.memory_working_content_frame import MemoryWorkingContentFrame

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_memory_ontology.stable_ids import stable_memory_working_content_frame_id

# --- AWARE: USER_IMPORTS END


async def build_via_memory_working_item(memory_working_item_id: UUID, content_id: UUID) -> MemoryWorkingContentFrame:
    """
    Builds deterministic content frame payload for a memory item.
    """

    # --- AWARE: LOGIC START build_via_memory_working_item
    return MemoryWorkingContentFrame(
        id=stable_memory_working_content_frame_id(
            memory_working_item_id=memory_working_item_id,
            content_id=content_id,
        ),
        content_id=content_id,
    )
    # --- AWARE: LOGIC END build_via_memory_working_item
