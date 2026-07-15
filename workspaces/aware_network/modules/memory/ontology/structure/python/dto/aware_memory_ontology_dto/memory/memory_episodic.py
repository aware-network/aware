from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.chain.content_chain import ContentChain
    from aware_identity_ontology_dto.actor.actor import Actor
    from aware_memory_ontology_dto.memory.memory_episode import MemoryEpisode


class MemoryEpisodic(BaseModel):
    # Relationships
    actor: Actor | None = Field(default=None)
    content_chain: ContentChain | None = Field(default=None)
    episodes: list[MemoryEpisode] = Field(default_factory=list)

    # Attributes
    key: str = Field(default="default")
