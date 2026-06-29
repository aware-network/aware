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


class CodeSectionAttribute(ORMModel):
    # Relationships
    name_segment: ContentPartTextSegment | None = Field(default=None)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    default_value_segment: ContentPartTextSegment | None = Field(default=None)
    type_segment: ContentPartTextSegment | None = Field(default=None)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_attribute")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    type_text: str | None = Field(default=None)
    default_value_text: str | None = Field(default=None)
    is_required: bool
    is_public: bool
    is_unique: bool
    is_primary: bool
    is_many_to_many: bool = Field(default=False)
    edge_spec_name: str | None = Field(default=None)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_attribute")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionAttribute.name_segment")
    default_value_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAttribute.default_value_segment"
    )
    type_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionAttribute.type_segment")
