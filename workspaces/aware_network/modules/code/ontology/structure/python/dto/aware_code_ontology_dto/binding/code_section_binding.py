from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.binding.code_section_binding_map import CodeSectionBindingMap
    from aware_code_ontology_dto.code.code_section import CodeSection
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionBinding(BaseModel):
    # Relationships
    source_graph_segment: ContentPartTextSegment
    target_graph_segment: ContentPartTextSegment
    code_section_binding_maps: list[CodeSectionBindingMap] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_binding")

    # Attributes
    source_graph_ref: str
    target_graph_ref: str
