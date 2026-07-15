from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.chain.content_chain_content import ContentChainContent
    from aware_content_ontology_dto.chain.content_chain_section import ContentChainSection


class MemoryEpisode(BaseModel):
    # Relationships
    content_chain_content: ContentChainContent | None = Field(default=None)
    content_chain_section: ContentChainSection | None = Field(default=None)

    # Attributes
    end_time: datetime
    start_time: datetime
