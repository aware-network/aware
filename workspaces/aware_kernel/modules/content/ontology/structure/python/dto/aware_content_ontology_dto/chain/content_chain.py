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
    from aware_content_ontology_dto.chain.content_chain_section import ContentChainSection
    from aware_content_ontology_dto.content.content import Content


class ContentChain(BaseModel):
    # Relationships
    content_chain_section: ContentChainSection | None = Field(default=None)

    # Attributes
    key: str = Field(default="default")
