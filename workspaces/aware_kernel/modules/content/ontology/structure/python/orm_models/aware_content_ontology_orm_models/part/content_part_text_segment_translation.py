from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class ContentPartTextSegmentTranslation(ORMModel):
    # Attributes
    language: str
    text: str

    # Foreign Keys
    content_part_text_segment_id: UUID = Field(
        description="Foreign key for ContentPartTextSegment.content_part_text_segment_translations"
    )
