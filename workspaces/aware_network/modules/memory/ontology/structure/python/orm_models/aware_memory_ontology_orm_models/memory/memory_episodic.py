from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.chain.content_chain import ContentChain
    from aware_identity_ontology_orm_models.actor.actor import Actor
    from aware_memory_ontology_orm_models.memory.memory_episode import MemoryEpisode


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
