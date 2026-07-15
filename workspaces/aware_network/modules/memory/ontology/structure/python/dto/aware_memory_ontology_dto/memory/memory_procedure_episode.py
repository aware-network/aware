from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_memory_ontology_dto.memory.memory_episode import MemoryEpisode
    from aware_memory_ontology_dto.memory.memory_procedure import MemoryProcedure


class MemoryProcedureEpisode(BaseModel):
    # Relationships
    memory_episode: MemoryEpisode | None = Field(default=None)
    memory_procedure: MemoryProcedure | None = Field(default=None)
