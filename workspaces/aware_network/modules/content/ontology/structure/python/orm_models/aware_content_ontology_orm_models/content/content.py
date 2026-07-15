from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Content Ontology Orm Models
from aware_content_ontology_orm_models.content.content_enums import ContentSource

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.content.content_index import ContentIndex
    from aware_content_ontology_orm_models.content.content_layout import ContentLayout
    from aware_content_ontology_orm_models.part.content_part_content import ContentPartContent


class Content(ORMModel):
    # Relationships
    content_index: ContentIndex | None = Field(default=None, exclude=True)
    content_layouts: list[ContentLayout] = Field(default_factory=list, exclude=True)
    content_part_contents: list[ContentPartContent] = Field(default_factory=list)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    source: ContentSource
    token_count: int | None = Field(default=None)
