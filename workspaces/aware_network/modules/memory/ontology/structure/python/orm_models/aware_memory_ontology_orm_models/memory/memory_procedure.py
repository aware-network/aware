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
    from aware_memory_ontology_orm_models.memory.memory_procedure_config import MemoryProcedureConfig


class MemoryProcedure(ORMModel):
    # Relationships
    content: Content | None = Field(default=None, exclude=True)
    procedure_config: MemoryProcedureConfig | None = Field(default=None, exclude=True)

    # Attributes
    reward_score: float = Field(default=0)

    # Foreign Keys
    memory_procedural_id: UUID = Field(description="Foreign key for MemoryProcedural.procedures")
    content_id: UUID = Field(description="Foreign key for MemoryProcedure.content")
    procedure_config_id: UUID = Field(description="Foreign key for MemoryProcedure.procedure_config")
