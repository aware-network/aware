from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_orm_models.enum.code_section_enum_value import CodeSectionEnumValue
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionEnum(ORMModel):
    # Relationships
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    code_section_enum_values: list[CodeSectionEnumValue] = Field(default_factory=list)
    content_part_text_segments: list[ContentPartTextSegment] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_enum")

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_enum")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionEnum.name_segment")
