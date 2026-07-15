from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_instance

# Types
from aware_types import Vector

if TYPE_CHECKING:
    from aware_content_ontology.chain.content_chain_content import ContentChainContent
    from aware_content_ontology.chain.content_chain_section import ContentChainSection


class MemoryEpisode(ORMModel):
    # Relationships
    content_chain_content: ContentChainContent | None = Field(default=None, exclude=True)
    content_chain_section: ContentChainSection | None = Field(default=None, exclude=True)

    # Attributes
    end_time: datetime
    start_time: datetime

    # Foreign Keys
    memory_episodic_id: UUID = Field(description="Foreign key for MemoryEpisodic.episodes")
    content_chain_content_id: UUID = Field(description="Foreign key for MemoryEpisode.content_chain_content")
    content_chain_section_id: UUID = Field(description="Foreign key for MemoryEpisode.content_chain_section")

    async def find_similar_multimodal(
        self,
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

        payload = {
            "p_memory_episodic_id": p_memory_episodic_id,
            "p_query_vector": p_query_vector,
            "p_result_count": p_result_count,
            "p_min_similarity": p_min_similarity,
            "p_start_time": p_start_time,
            "p_end_time": p_end_time,
        }
        await invoke_instance(orm_model=self, function_name="find_similar_multimodal", payload=payload)
        return None

    async def find_similar_text(
        self,
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

        payload = {
            "p_memory_episodic_id": p_memory_episodic_id,
            "p_query_vector": p_query_vector,
            "p_result_count": p_result_count,
            "p_min_similarity": p_min_similarity,
            "p_start_time": p_start_time,
            "p_end_time": p_end_time,
        }
        await invoke_instance(orm_model=self, function_name="find_similar_text", payload=payload)
        return None


class MemoryEpisodeFindSimilarMultimodalInput(BaseModel):
    p_memory_episodic_id: UUID
    p_query_vector: Vector
    p_result_count: int
    p_min_similarity: float
    p_start_time: datetime | None = Field(default=None)
    p_end_time: datetime | None = Field(default=None)


class MemoryEpisodeFindSimilarMultimodalOutput(BaseModel):
    pass


class MemoryEpisodeFindSimilarTextInput(BaseModel):
    p_memory_episodic_id: UUID
    p_query_vector: Vector
    p_result_count: int
    p_min_similarity: float
    p_start_time: datetime | None = Field(default=None)
    p_end_time: datetime | None = Field(default=None)


class MemoryEpisodeFindSimilarTextOutput(BaseModel):
    pass


FUNCTIONS = {
    "MemoryEpisode": {
        "find_similar_multimodal": {
            "canonical": {
                "name": "find_similar_multimodal",
                "description": "Finds similar multimodal content parts within a specific episodic memory with optional time constraints.\nParameters: p_memory_episodic_id: The UUID of the episodic memory to search in.\np_query_vector: The vector to query.\np_result_count: The number of results to return.\np_min_similarity: The minimum similarity to return.\np_start_time: Optional start time for temporal filtering.\np_end_time: Optional end time for temporal filtering.\nReturns: Table containing episode information and similarity scores.\nType: episode_id: The UUID of the episode.\nstart_time: When the episode started.\nend_time: When the episode ended.\nsimilarity: The similarity score (adjusted for temporal proximity when time range is provided).",
                "is_constructor": False,
            },
            "input": MemoryEpisodeFindSimilarMultimodalInput,
            "output": MemoryEpisodeFindSimilarMultimodalOutput,
        },
        "find_similar_text": {
            "canonical": {
                "name": "find_similar_text",
                "description": "Finds similar text content parts within a specific episodic memory with optional time constraints.\nParameters: p_memory_episodic_id: The UUID of the episodic memory to search in.\np_query_vector: The vector to query.\np_result_count: The number of results to return.\np_min_similarity: The minimum similarity to return.\np_start_time: Optional start time for temporal filtering.\np_end_time: Optional end time for temporal filtering.\nReturns: Table containing episode information and similarity scores.\nType: episode_id: The UUID of the episode.\nstart_time: When the episode started.\nend_time: When the episode ended.\nsimilarity: The similarity score (adjusted for temporal proximity when time range is provided).",
                "is_constructor": False,
            },
            "input": MemoryEpisodeFindSimilarTextInput,
            "output": MemoryEpisodeFindSimilarTextOutput,
        },
    },
}

__all__ = [
    "MemoryEpisode",
    "MemoryEpisodeFindSimilarMultimodalInput",
    "MemoryEpisodeFindSimilarMultimodalOutput",
    "MemoryEpisodeFindSimilarTextInput",
    "MemoryEpisodeFindSimilarTextOutput",
    "FUNCTIONS",
]
