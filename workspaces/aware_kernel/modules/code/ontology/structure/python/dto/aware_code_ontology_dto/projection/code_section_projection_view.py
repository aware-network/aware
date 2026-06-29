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


class CodeSectionProjectionView(BaseModel):
    # Relationships
    key_segment: ContentPartTextSegment
    body_segment: ContentPartTextSegment

    # Attributes
    key: str = Field(description="Fully qualified view key within the projection (e.g. `onboarding.welcome`).")
    kind: str = Field(description="One of: `construct`, `instance`.")
    is_default: bool = Field(default=False)
    description: str | None = Field(default=None)
