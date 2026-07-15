from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_content import ContentPartContent
    from aware_content_ontology_dto.part.content_part_content_layout import ContentPartContentLayout


class ContentLayout(BaseModel):
    # Attributes
    background_color: str | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str
    viewport_height: float | None = Field(default=None)
    viewport_width: float | None = Field(default=None)
