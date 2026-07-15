from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.content.content import Content


class MemoryWorkingContentFrame(ORMModel):
    """
    Content payload for a MemoryWorkingItem.
    Contract:
    - Must be linked to a `MemoryWorkingItem` whose `kind=content`.
    - Content remains multimodal-ready via aware_content.
    """

    # Relationships
    content: Content | None = Field(default=None, exclude=True)

    # Foreign Keys
    memory_working_item_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingItem.content_frame"
    )
    content_id: UUID = Field(description="Foreign key for MemoryWorkingContentFrame.content")
