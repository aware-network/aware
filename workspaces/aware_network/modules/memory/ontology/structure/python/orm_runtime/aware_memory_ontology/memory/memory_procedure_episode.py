from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_memory_ontology.memory.memory_episode import MemoryEpisode
    from aware_memory_ontology.memory.memory_procedure import MemoryProcedure


class MemoryProcedureEpisode(ORMModel):
    # Relationships
    memory_episode: MemoryEpisode | None = Field(default=None, exclude=True)
    memory_procedure: MemoryProcedure | None = Field(default=None, exclude=True)

    # Foreign Keys
    memory_episode_id: UUID = Field(description="Foreign key for MemoryProcedureEpisode.memory_episode")
    memory_procedure_id: UUID = Field(description="Foreign key for MemoryProcedureEpisode.memory_procedure")


FUNCTIONS = {
    "MemoryProcedureEpisode": {},
}

__all__ = [
    "MemoryProcedureEpisode",
    "FUNCTIONS",
]
