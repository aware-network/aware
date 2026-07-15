from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.identity.identity import Identity
    from aware_memory_ontology_dto.memory.memory_procedure import MemoryProcedure


class MemoryProcedural(BaseModel):
    # Relationships
    identity: Identity | None = Field(default=None)
    procedures: list[MemoryProcedure] = Field(default_factory=list)

    # Attributes
    key: str = Field(default="default")
