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
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_orm_models.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology_orm_models.function.code_section_function_attribute import CodeSectionFunctionAttribute
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionFunction(ORMModel):
    # Relationships
    name_segment: ContentPartTextSegment | None = Field(default=None)
    body_segment: ContentPartTextSegment | None = Field(default=None)
    signature_segment: ContentPartTextSegment
    return_type_segment: ContentPartTextSegment | None = Field(default=None)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    code_section_decorators: list[CodeSectionDecorator] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_function")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    is_async: bool
    is_public: bool
    is_static: bool = Field(default=False)
    is_classmethod: bool = Field(default=False)
    verb: str | None = Field(default=None)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_function")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionFunction.name_segment")
    body_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionFunction.body_segment")
    signature_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionFunction.signature_segment"
    )
    return_type_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionFunction.return_type_segment"
    )

    # Edges
    code_section_function_attributes: list[CodeSectionFunctionAttribute] = Field(
        default_factory=list, exclude=True, description="Edge association helper for code_section_attributes"
    )

    @property
    def code_section_attributes(self) -> list[CodeSectionAttribute]:
        return [
            edge.code_section_attribute
            for edge in self.code_section_function_attributes
            if edge.code_section_attribute is not None
        ]
