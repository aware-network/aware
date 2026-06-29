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


class CodeSectionProjectionEdge(ORMModel):
    # Relationships
    type_segment: ContentPartTextSegment
    member_segment: ContentPartTextSegment
    target_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    type_ref: str
    member: str
    target_projection_ref: str | None = Field(
        default=None,
        description="Optional portal target projection reference.\nForms:\n- unqualified: `Focus`\n- qualified: `aware_identity.Identity` (recommended for cross-package)",
    )

    # Foreign Keys
    code_section_projection_id: UUID = Field(description="Foreign key for CodeSectionProjection.projection_edges")
    type_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionEdge.type_segment"
    )
    member_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionEdge.member_segment"
    )
    target_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionEdge.target_segment"
    )
