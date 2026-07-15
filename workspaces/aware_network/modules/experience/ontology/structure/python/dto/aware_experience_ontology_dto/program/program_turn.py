from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_turn_instruction import ProgramTurnInstruction
    from aware_experience_ontology_dto.turn.turn import Turn


class ProgramTurn(BaseModel):
    # Relationships
    turn: Turn | None = Field(default=None)
    instructions: list[ProgramTurnInstruction] = Field(default_factory=list)

    # Attributes
    order: int
