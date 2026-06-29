from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.chain.content_chain_content import ContentChainContent
    from aware_content_ontology_orm_models.chain.content_chain_section import ContentChainSection
    from aware_content_ontology_orm_models.content.content import Content


class ContentChain(ORMModel):
    # Relationships
    content_chain_section: ContentChainSection | None = Field(default=None, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Edges
    content_chain_contents_edges: list[ContentChainContent] = Field(
        default_factory=list, exclude=True, description="Edge association helper for content_chain_contents"
    )

    @property
    def content_chain_contents(self) -> list[Content]:
        return [edge.content for edge in self.content_chain_contents_edges if edge.content is not None]
