from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.chain.content_chain_content import ContentChainContent
    from aware_content_ontology_orm_models.chain.content_chain_section import ContentChainSection


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
