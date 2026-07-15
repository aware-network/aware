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


class MemoryProcedureConfig(BaseModel):
    # Relationships
    content: Content | None = Field(default=None)

    # Attributes
    title: str
    description: str
