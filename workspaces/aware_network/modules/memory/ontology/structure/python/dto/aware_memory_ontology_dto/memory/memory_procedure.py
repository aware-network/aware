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
    from aware_memory_ontology_dto.memory.memory_procedure_config import MemoryProcedureConfig


class MemoryProcedure(BaseModel):
    # Relationships
    content: Content | None = Field(default=None)
    procedure_config: MemoryProcedureConfig | None = Field(default=None)

    # Attributes
    reward_score: float = Field(default=0)
