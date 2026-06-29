from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_text import ContentPartText
    from aware_content_ontology_orm_models.part.content_part_text_segment_translation import (
        ContentPartTextSegmentTranslation,
    )
    from aware_content_ontology_orm_models.part.content_part_text_style import ContentPartTextStyle


class ContentPartTextSegment(ORMModel):
    # Relationships
    content_part_text_segment_translations: list[ContentPartTextSegmentTranslation] = Field(
        default_factory=list, exclude=True
    )
    parent: ContentPartTextSegment | None = Field(default=None, exclude=True)
    style: ContentPartTextStyle | None = Field(default=None, exclude=True)
    content_part_text: ContentPartText = Field(description="Reverse view for ContentPartText.segments")

    # Attributes
    key: str = Field(default="default")
    byte_end: int | None = Field(default=None)
    byte_start: int | None = Field(default=None)

    # Foreign Keys
    content_part_text_id: UUID | None = Field(default=None, description="Foreign key for ContentPartText.segments")
    parent_id: UUID | None = Field(default=None, description="Foreign key for ContentPartTextSegment.parent")
