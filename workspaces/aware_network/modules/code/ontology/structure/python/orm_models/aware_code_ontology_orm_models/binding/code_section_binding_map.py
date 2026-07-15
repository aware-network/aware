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


class CodeSectionBindingMap(ORMModel):
    # Relationships
    name_segment: ContentPartTextSegment
    source_segment: ContentPartTextSegment
    target_segment: ContentPartTextSegment
    body_segment: ContentPartTextSegment | None = Field(default=None)
    template_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    name: str
    source_ref: str
    target_ref: str
    description: str | None = Field(default=None)
    template_text: str | None = Field(default=None)

    # Foreign Keys
    code_section_binding_id: UUID = Field(description="Foreign key for CodeSectionBinding.code_section_binding_maps")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionBindingMap.name_segment")
    source_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBindingMap.source_segment"
    )
    target_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBindingMap.target_segment"
    )
    body_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionBindingMap.body_segment")
    template_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBindingMap.template_segment"
    )
