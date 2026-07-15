from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.chain.content_chain_content import ContentChainContent


class ContentChainSection(BaseModel):
    # Relationships
    newest_content_chain_content: ContentChainContent | None = Field(default=None)
    oldest_content_chain_content: ContentChainContent | None = Field(default=None)

    # Attributes
    key: str = Field(default="default")
