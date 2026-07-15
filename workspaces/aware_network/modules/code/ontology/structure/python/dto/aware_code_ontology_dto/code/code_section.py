from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_section_enums import CodeSectionType

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_dto.annotation.code_section_annotation import CodeSectionAnnotation
    from aware_code_ontology_dto.attribute.code_section_attribute import CodeSectionAttribute
    from aware_code_ontology_dto.binding.code_section_binding import CodeSectionBinding
    from aware_code_ontology_dto.class_.code_section_class import CodeSectionClass
    from aware_code_ontology_dto.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_dto.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology_dto.enum.code_section_enum import CodeSectionEnum
    from aware_code_ontology_dto.enum.code_section_enum_value import CodeSectionEnumValue
    from aware_code_ontology_dto.expression.code_section_expression import CodeSectionExpression
    from aware_code_ontology_dto.function.code_section_function import CodeSectionFunction
    from aware_code_ontology_dto.import_.code_section_import import CodeSectionImport
    from aware_code_ontology_dto.mirror.code_section_mirror import CodeSectionMirror
    from aware_code_ontology_dto.projection.code_section_projection import CodeSectionProjection
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSection(BaseModel):
    # Relationships
    content_part_text_segment: ContentPartTextSegment
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None)
    code_section_attribute: CodeSectionAttribute | None = Field(default=None)
    code_section_binding: CodeSectionBinding | None = Field(default=None)
    code_section_class: CodeSectionClass | None = Field(default=None)
    code_section_comment: CodeSectionComment | None = Field(default=None)
    code_section_decorator: CodeSectionDecorator | None = Field(default=None)
    code_section_enum: CodeSectionEnum | None = Field(default=None)
    code_section_enum_value: CodeSectionEnumValue | None = Field(default=None)
    code_section_expression: CodeSectionExpression | None = Field(default=None)
    code_section_function: CodeSectionFunction | None = Field(default=None)
    code_section_import: CodeSectionImport | None = Field(default=None)
    code_section_mirror: CodeSectionMirror | None = Field(default=None)
    code_section_projection: CodeSectionProjection | None = Field(default=None)

    # Attributes
    identity_hash: str
    metadata: JsonObject | None = Field(default=None)
    qualname: str
    section_key: str
    type: CodeSectionType
