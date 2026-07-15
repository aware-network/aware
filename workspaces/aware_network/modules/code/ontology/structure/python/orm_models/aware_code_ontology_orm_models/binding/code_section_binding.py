from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.binding.code_section_binding_map import CodeSectionBindingMap
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionBinding(ORMModel):
    # Relationships
    source_graph_segment: ContentPartTextSegment
    target_graph_segment: ContentPartTextSegment
    code_section_binding_maps: list[CodeSectionBindingMap] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_binding")

    # Attributes
    source_graph_ref: str
    target_graph_ref: str

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_binding")
    source_graph_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBinding.source_graph_segment"
    )
    target_graph_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBinding.target_graph_segment"
    )
