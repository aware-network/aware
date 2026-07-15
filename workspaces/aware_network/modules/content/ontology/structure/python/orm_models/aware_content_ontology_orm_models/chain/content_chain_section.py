from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.chain.content_chain_content import ContentChainContent


class ContentChainSection(ORMModel):
    # Relationships
    newest_content_chain_content: ContentChainContent | None = Field(default=None, exclude=True)
    oldest_content_chain_content: ContentChainContent | None = Field(default=None, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Foreign Keys
    content_chain_id: UUID | None = Field(
        default=None, description="Foreign key for ContentChain.content_chain_section"
    )
    newest_content_chain_content_id: UUID | None = Field(
        default=None, description="Foreign key for ContentChainSection.newest_content_chain_content"
    )
    oldest_content_chain_content_id: UUID | None = Field(
        default=None, description="Foreign key for ContentChainSection.oldest_content_chain_content"
    )
