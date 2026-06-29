from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionCommentContent(ORMModel):
    # Relationships
    content_part_text_segment: ContentPartTextSegment

    # Attributes
    position: int

    # Foreign Keys
    code_section_comment_id: UUID = Field(
        description="Foreign key for CodeSectionComment.code_section_comment_contents"
    )
    content_part_text_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionCommentContent.content_part_text_segment"
    )
