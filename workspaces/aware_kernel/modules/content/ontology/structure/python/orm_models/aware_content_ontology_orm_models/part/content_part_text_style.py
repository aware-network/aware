from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class ContentPartTextStyle(ORMModel):
    # Attributes
    background_color: str | None = Field(default=None)
    block_semantic_type: str | None = Field(default=None)
    bold: bool | None = Field(default=False)
    color: str | None = Field(default=None)
    font_family: str | None = Field(default=None)
    font_size: int | None = Field(default=0)
    italic: bool | None = Field(default=False)
    underline: bool | None = Field(default=False)

    # Foreign Keys
    content_part_text_segment_id: UUID | None = Field(
        default=None, description="Foreign key for ContentPartTextSegment.style"
    )
