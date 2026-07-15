from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_turn_instruction import ProgramTurnInstruction
    from aware_experience_ontology_orm_models.turn.turn import Turn


class ProgramTurn(ORMModel):
    # Relationships
    turn: Turn | None = Field(default=None, exclude=True)
    instructions: list[ProgramTurnInstruction] = Field(default_factory=list, exclude=True)

    # Attributes
    order: int

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.turns")
    turn_id: UUID = Field(description="Foreign key for ProgramTurn.turn")
