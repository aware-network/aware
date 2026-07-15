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


class CodeSectionProjectionView(ORMModel):
    # Relationships
    key_segment: ContentPartTextSegment
    body_segment: ContentPartTextSegment

    # Attributes
    key: str = Field(description="Fully qualified view key within the projection (e.g. `onboarding.welcome`).")
    kind: str = Field(description="One of: `construct`, `instance`.")
    is_default: bool = Field(default=False)
    description: str | None = Field(default=None)

    # Foreign Keys
    code_section_projection_id: UUID = Field(description="Foreign key for CodeSectionProjection.projection_views")
    key_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionView.key_segment"
    )
    body_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionView.body_segment"
    )
