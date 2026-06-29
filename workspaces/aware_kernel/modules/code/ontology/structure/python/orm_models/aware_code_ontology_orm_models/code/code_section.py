from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_section_enums import CodeSectionType

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.annotation.code_section_annotation import CodeSectionAnnotation
    from aware_code_ontology_orm_models.attribute.code_section_attribute import CodeSectionAttribute
    from aware_code_ontology_orm_models.binding.code_section_binding import CodeSectionBinding
    from aware_code_ontology_orm_models.class_.code_section_class import CodeSectionClass
    from aware_code_ontology_orm_models.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_orm_models.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology_orm_models.enum.code_section_enum import CodeSectionEnum
    from aware_code_ontology_orm_models.enum.code_section_enum_value import CodeSectionEnumValue
    from aware_code_ontology_orm_models.expression.code_section_expression import CodeSectionExpression
    from aware_code_ontology_orm_models.function.code_section_function import CodeSectionFunction
    from aware_code_ontology_orm_models.import_.code_section_import import CodeSectionImport
    from aware_code_ontology_orm_models.mirror.code_section_mirror import CodeSectionMirror
    from aware_code_ontology_orm_models.projection.code_section_projection import CodeSectionProjection
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSection(ORMModel):
    # Relationships
    content_part_text_segment: ContentPartTextSegment
    code_section_annotation: CodeSectionAnnotation | None = Field(default=None, exclude=True)
    code_section_attribute: CodeSectionAttribute | None = Field(default=None, exclude=True)
    code_section_binding: CodeSectionBinding | None = Field(default=None, exclude=True)
    code_section_class: CodeSectionClass | None = Field(default=None, exclude=True)
    code_section_comment: CodeSectionComment | None = Field(default=None, exclude=True)
    code_section_decorator: CodeSectionDecorator | None = Field(default=None, exclude=True)
    code_section_enum: CodeSectionEnum | None = Field(default=None, exclude=True)
    code_section_enum_value: CodeSectionEnumValue | None = Field(default=None, exclude=True)
    code_section_expression: CodeSectionExpression | None = Field(default=None, exclude=True)
    code_section_function: CodeSectionFunction | None = Field(default=None, exclude=True)
    code_section_import: CodeSectionImport | None = Field(default=None, exclude=True)
    code_section_mirror: CodeSectionMirror | None = Field(default=None, exclude=True)
    code_section_projection: CodeSectionProjection | None = Field(default=None, exclude=True)

    # Attributes
    identity_hash: str
    metadata: JsonObject | None = Field(default=None)
    qualname: str
    section_key: str
    type: CodeSectionType

    # Foreign Keys
    code_id: UUID = Field(description="Foreign key for Code.code_sections")
    content_part_text_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.content_part_text_segment"
    )
