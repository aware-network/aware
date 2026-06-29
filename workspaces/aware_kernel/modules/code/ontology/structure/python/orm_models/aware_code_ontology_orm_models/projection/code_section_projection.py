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
    from aware_code_ontology_orm_models.projection.code_section_projection_edge import CodeSectionProjectionEdge
    from aware_code_ontology_orm_models.projection.code_section_projection_view import CodeSectionProjectionView
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionProjection(ORMModel):
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

    # Foreign Keys
    code_section_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.code_section_projection"
    )
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionProjection.name_segment")
    root_type_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjection.root_type_segment"
    )
