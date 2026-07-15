from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Memory Ontology
from aware_memory_ontology.memory.memory_episodic import MemoryEpisodic

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(actor_id: UUID, key: str = "default") -> MemoryEpisodic:
    """
    Create one deterministic MemoryEpisodic lane for an Identity Actor.

    Policy:
    - Memory owns the lane object and references Identity Actor relationally.
    - Identity is deterministic from actor plus `key`.
    - ContentChain must be created via ContentChain.build (no direct instantiation).
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build


async def create_root(memory_episodic: MemoryEpisodic, p_chain_config_memory_episodic_id: UUID) -> UUID:
    """
    Creates a new root memory episodic with its own content chain and main thread.
    This is used to create the initial memory episodic for an actor lane.
    Parameters: p_chain_config_memory_episodic_id: The UUID of the memory episodic chain config to use
    Returns: The UUID of the newly created memory episodic
    """

    # --- AWARE: LOGIC START create_root
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_root


async def create_thread(memory_episodic: MemoryEpisodic, p_parent_memory_episodic_id: UUID) -> UUID:
    """
    Creates a new memory episodic by creating a thread from a parent memory episodic.
    The new thread diverges from the parent thread at the oldest_content point.
    This is used to create memory threads at different actor-owned layers.
    Parameters: p_parent_memory_episodic_id: The UUID of the parent memory episodic to create thread
    from
    Returns: The UUID of the newly created memory episodic
    """

    # --- AWARE: LOGIC START create_thread
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_thread
