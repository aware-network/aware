from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Code
from aware_code.types import Vector

# Memory Ontology
from aware_memory_ontology.memory.memory_episode import MemoryEpisode

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def find_similar_multimodal(
    memory_episode: MemoryEpisode,
    p_memory_episodic_id: UUID,
    p_query_vector: Vector,
    p_result_count: int,
    p_min_similarity: float,
    p_start_time: datetime | None = None,
    p_end_time: datetime | None = None,
) -> None:
    """
    Finds similar multimodal content parts within a specific episodic memory with optional time
    constraints.
    Parameters: p_memory_episodic_id: The UUID of the episodic memory to search in.
    p_query_vector: The vector to query.
    p_result_count: The number of results to return.
    p_min_similarity: The minimum similarity to return.
    p_start_time: Optional start time for temporal filtering.
    p_end_time: Optional end time for temporal filtering.
    Returns: Table containing episode information and similarity scores.
    Type: episode_id: The UUID of the episode.
    start_time: When the episode started.
    end_time: When the episode ended.
    similarity: The similarity score (adjusted for temporal proximity when time range is provided).
    """

    # --- AWARE: LOGIC START find_similar_multimodal
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END find_similar_multimodal


async def find_similar_text(
    memory_episode: MemoryEpisode,
    p_memory_episodic_id: UUID,
    p_query_vector: Vector,
    p_result_count: int,
    p_min_similarity: float,
    p_start_time: datetime | None = None,
    p_end_time: datetime | None = None,
) -> None:
    """
    Finds similar text content parts within a specific episodic memory with optional time constraints.
    Parameters: p_memory_episodic_id: The UUID of the episodic memory to search in.
    p_query_vector: The vector to query.
    p_result_count: The number of results to return.
    p_min_similarity: The minimum similarity to return.
    p_start_time: Optional start time for temporal filtering.
    p_end_time: Optional end time for temporal filtering.
    Returns: Table containing episode information and similarity scores.
    Type: episode_id: The UUID of the episode.
    start_time: When the episode started.
    end_time: When the episode ended.
    similarity: The similarity score (adjusted for temporal proximity when time range is provided).
    """

    # --- AWARE: LOGIC START find_similar_text
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END find_similar_text
