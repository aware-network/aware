from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_content_ontology.chain.content_chain import ContentChain
    from aware_identity_ontology.actor.actor import Actor
    from aware_memory_ontology.memory.memory_episode import MemoryEpisode


class MemoryEpisodic(ORMModel):
    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)
    content_chain: ContentChain | None = Field(default=None, exclude=True)
    episodes: list[MemoryEpisode] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for MemoryEpisodic.actor")
    content_chain_id: UUID = Field(description="Foreign key for MemoryEpisodic.content_chain")

    @classmethod
    async def build(cls, actor_id: UUID, key: str = "default") -> MemoryEpisodic:
        """
        Create one deterministic MemoryEpisodic lane for an Identity Actor.

        Policy:
        - Memory owns the lane object and references Identity Actor relationally.
        - Identity is deterministic from actor plus `key`.
        - ContentChain must be created via ContentChain.build (no direct instantiation).
        """

        payload = {"actor_id": actor_id, "key": key}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemoryEpisodic):
            return value
        return MemoryEpisodic.validate_invocation_value(value)

    async def create_root(self, p_chain_config_memory_episodic_id: UUID) -> UUID:
        """
        Creates a new root memory episodic with its own content chain and main thread.
        This is used to create the initial memory episodic for an actor lane.
        Parameters: p_chain_config_memory_episodic_id: The UUID of the memory episodic chain config to use
        Returns: The UUID of the newly created memory episodic
        """

        payload = {"p_chain_config_memory_episodic_id": p_chain_config_memory_episodic_id}
        result = await invoke_instance(orm_model=self, function_name="create_root", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def create_thread(self, p_parent_memory_episodic_id: UUID) -> UUID:
        """
        Creates a new memory episodic by creating a thread from a parent memory episodic.
        The new thread diverges from the parent thread at the oldest_content point.
        This is used to create memory threads at different actor-owned layers.
        Parameters: p_parent_memory_episodic_id: The UUID of the parent memory episodic to create thread
        from
        Returns: The UUID of the newly created memory episodic
        """

        payload = {"p_parent_memory_episodic_id": p_parent_memory_episodic_id}
        result = await invoke_instance(orm_model=self, function_name="create_thread", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value


class MemoryEpisodicBuildInput(BaseModel):
    actor_id: UUID
    key: str = Field(default="default")


class MemoryEpisodicBuildOutput(BaseModel):
    value: MemoryEpisodic


class MemoryEpisodicCreateRootInput(BaseModel):
    p_chain_config_memory_episodic_id: UUID


class MemoryEpisodicCreateRootOutput(BaseModel):
    value: UUID


class MemoryEpisodicCreateThreadInput(BaseModel):
    p_parent_memory_episodic_id: UUID


class MemoryEpisodicCreateThreadOutput(BaseModel):
    value: UUID


FUNCTIONS = {
    "MemoryEpisodic": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic MemoryEpisodic lane for an Identity Actor.\n\nPolicy:\n- Memory owns the lane object and references Identity Actor relationally.\n- Identity is deterministic from actor plus `key`.\n- ContentChain must be created via ContentChain.build (no direct instantiation).",
                "is_constructor": True,
            },
            "input": MemoryEpisodicBuildInput,
            "output": MemoryEpisodicBuildOutput,
        },
        "create_root": {
            "canonical": {
                "name": "create_root",
                "description": "Creates a new root memory episodic with its own content chain and main thread.\nThis is used to create the initial memory episodic for an actor lane.\nParameters: p_chain_config_memory_episodic_id: The UUID of the memory episodic chain config to use\nReturns: The UUID of the newly created memory episodic",
                "is_constructor": False,
            },
            "input": MemoryEpisodicCreateRootInput,
            "output": MemoryEpisodicCreateRootOutput,
        },
        "create_thread": {
            "canonical": {
                "name": "create_thread",
                "description": "Creates a new memory episodic by creating a thread from a parent memory episodic.\nThe new thread diverges from the parent thread at the oldest_content point.\nThis is used to create memory threads at different actor-owned layers.\nParameters: p_parent_memory_episodic_id: The UUID of the parent memory episodic to create thread from\nReturns: The UUID of the newly created memory episodic",
                "is_constructor": False,
            },
            "input": MemoryEpisodicCreateThreadInput,
            "output": MemoryEpisodicCreateThreadOutput,
        },
    },
}

__all__ = [
    "MemoryEpisodic",
    "MemoryEpisodicBuildInput",
    "MemoryEpisodicBuildOutput",
    "MemoryEpisodicCreateRootInput",
    "MemoryEpisodicCreateRootOutput",
    "MemoryEpisodicCreateThreadInput",
    "MemoryEpisodicCreateThreadOutput",
    "FUNCTIONS",
]
