from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.content.content import Content


class MemoryWorkingContentFrame(BaseModel):
    """
    Content payload for a MemoryWorkingItem.
    Contract:
    - Must be linked to a `MemoryWorkingItem` whose `kind=content`.
    - Content remains multimodal-ready via aware_content.
    """

    # Relationships
    content: Content | None = Field(default=None)
