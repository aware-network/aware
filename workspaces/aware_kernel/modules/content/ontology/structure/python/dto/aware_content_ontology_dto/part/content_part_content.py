from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import BaseModel

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part import ContentPart


class ContentPartContent(BaseModel):
    # Relationships
    content_part: ContentPart

    # Attributes
    position: int
