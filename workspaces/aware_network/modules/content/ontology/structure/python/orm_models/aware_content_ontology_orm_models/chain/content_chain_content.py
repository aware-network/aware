from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.content.content import Content


class ContentChainContent(ORMModel):
    # Relationships
    content: Content | None = Field(default=None, exclude=True, description="Association target reference to Content")

    # Attributes
    position: int

    # Foreign Keys
    content_id: UUID = Field(description="Join FK to Content")
    content_chain_id: UUID = Field(description="Join FK to ContentChain")
