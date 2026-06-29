from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_content import ContentPartContent
    from aware_content_ontology_orm_models.part.content_part_content_layout import ContentPartContentLayout


class ContentLayout(ORMModel):
    # Attributes
    background_color: str | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str
    viewport_height: float | None = Field(default=None)
    viewport_width: float | None = Field(default=None)

    # Foreign Keys
    content_id: UUID = Field(description="Foreign key for Content.content_layouts")

    # Edges
    content_part_content_layouts: list[ContentPartContentLayout] = Field(
        default_factory=list, exclude=True, description="Edge association helper for content_part_contents"
    )

    @property
    def content_part_contents(self) -> list[ContentPartContent]:
        return [
            edge.content_part_content
            for edge in self.content_part_content_layouts
            if edge.content_part_content is not None
        ]
