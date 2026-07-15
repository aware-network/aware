from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_section import CodeSection
    from aware_code_ontology_dto.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_dto.projection.code_section_projection_edge import CodeSectionProjectionEdge
    from aware_code_ontology_dto.projection.code_section_projection_view import CodeSectionProjectionView
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionProjection(BaseModel):
    # Relationships
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    root_type_segment: ContentPartTextSegment | None = Field(default=None)
    projection_edges: list[CodeSectionProjectionEdge] = Field(default_factory=list)
    projection_views: list[CodeSectionProjectionView] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_projection")

    # Attributes
    name: str = Field(description="Projection symbol name (e.g. `ActorFocus`).")
    description: str | None = Field(default=None, description="Human-friendly description (derived from doc comments).")
    projection_name: str = Field(
        description='Canonical projection identity name (default: authored projection symbol; overridable via `name "..."` option).'
    )
    label: str | None = Field(default=None)
    is_branchable: bool = Field(default=False)
    root_type_ref: str | None = Field(default=None, description="Root type reference (FQN) for the projection.")
