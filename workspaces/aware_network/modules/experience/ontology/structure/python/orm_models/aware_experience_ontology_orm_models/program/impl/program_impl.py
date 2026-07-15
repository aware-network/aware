from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction import ProgramImplInstruction
    from aware_experience_ontology_orm_models.program.program_config import ProgramConfig


class ProgramImpl(ORMModel):
    # Relationships
    program_config: ProgramConfig | None = Field(default=None, exclude=True)
    instructions: list[ProgramImplInstruction] = Field(default_factory=list)

    # Attributes
    key: str

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramImpl.program_config")
