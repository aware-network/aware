from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.impl.program_impl_instruction import ProgramImplInstruction
    from aware_experience_ontology_dto.program.program_config import ProgramConfig


class ProgramImpl(BaseModel):
    # Relationships
    program_config: ProgramConfig | None = Field(default=None)
    instructions: list[ProgramImplInstruction] = Field(default_factory=list)

    # Attributes
    key: str
