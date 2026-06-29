from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionProjectionEdge(BaseModel):
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
