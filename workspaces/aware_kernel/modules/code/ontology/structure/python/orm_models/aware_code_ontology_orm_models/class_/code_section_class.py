from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.attribute.code_section_attribute import CodeSectionAttribute
    from aware_code_ontology_orm_models.class_.code_section_class_attribute import CodeSectionClassAttribute
    from aware_code_ontology_orm_models.class_.code_section_class_base import CodeSectionClassBase
    from aware_code_ontology_orm_models.class_.code_section_class_function import CodeSectionClassFunction
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_orm_models.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology_orm_models.function.code_section_function import CodeSectionFunction
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionClass(ORMModel):
    # Relationships
    code_section_class_bases: list[CodeSectionClassBase] = Field(default_factory=list)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    code_section_decorators: list[CodeSectionDecorator] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    keyword_segment: ContentPartTextSegment | None = Field(default=None)
    modifiers_segment: ContentPartTextSegment | None = Field(default=None)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_class")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    verb_target: str | None = Field(default=None)
    is_edge: bool = Field(default=False)
    is_inline_value: bool = Field(default=False)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_class")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionClass.name_segment")
    keyword_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionClass.keyword_segment"
    )
    modifiers_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionClass.modifiers_segment"
    )

    # Edges
    code_section_class_attributes: list[CodeSectionClassAttribute] = Field(
        default_factory=list, exclude=True, description="Edge association helper for code_section_attributes"
    )
    code_section_class_functions: list[CodeSectionClassFunction] = Field(
        default_factory=list, exclude=True, description="Edge association helper for code_section_functions"
    )

    @property
    def code_section_attributes(self) -> list[CodeSectionAttribute]:
        return [
            edge.code_section_attribute
            for edge in self.code_section_class_attributes
            if edge.code_section_attribute is not None
        ]

    @property
    def code_section_functions(self) -> list[CodeSectionFunction]:
        return [
            edge.code_section_function
            for edge in self.code_section_class_functions
            if edge.code_section_function is not None
        ]
