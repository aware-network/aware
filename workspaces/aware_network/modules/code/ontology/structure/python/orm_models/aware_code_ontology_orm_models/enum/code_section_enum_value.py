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
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionEnumValue(ORMModel):
    # Relationships
    value_segment: ContentPartTextSegment
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_enum_value")

    # Attributes
    value: str
    description: str | None = Field(default=None)
    position: int = Field(default=0)

    # Foreign Keys
    code_section_enum_id: UUID = Field(description="Foreign key for CodeSectionEnum.code_section_enum_values")
    code_section_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.code_section_enum_value"
    )
    value_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionEnumValue.value_segment"
    )
