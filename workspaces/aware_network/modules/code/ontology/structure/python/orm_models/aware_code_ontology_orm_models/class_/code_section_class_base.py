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


class CodeSectionClassBase(ORMModel):
    # Relationships
    segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    base_ref: str
    is_augment: bool = Field(default=False)

    # Foreign Keys
    code_section_class_id: UUID = Field(description="Foreign key for CodeSectionClass.code_section_class_bases")
    segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionClassBase.segment")
