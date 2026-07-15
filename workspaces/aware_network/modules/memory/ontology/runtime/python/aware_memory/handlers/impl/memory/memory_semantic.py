from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Memory Ontology
from aware_memory_ontology.memory.memory_semantic import MemorySemantic

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(identity_id: UUID, key: str = "default") -> MemorySemantic:
    """
    Create one deterministic semantic-memory lane for an owning Identity.

    Policy:
    - Memory owns the lane object and references Identity relationally.
    - Shared semantic memory is deterministic from Identity plus `key`.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build
