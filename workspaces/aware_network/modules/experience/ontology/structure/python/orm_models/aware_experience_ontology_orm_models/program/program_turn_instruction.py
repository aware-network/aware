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
    from aware_experience_ontology_orm_models.program.program_turn_decision import ProgramTurnInstructionDecision
    from aware_experience_ontology_orm_models.program.program_turn_instruction_action import (
        ProgramTurnInstructionAction,
    )
    from aware_experience_ontology_orm_models.program.program_turn_instruction_bind import ProgramTurnInstructionBind
    from aware_experience_ontology_orm_models.program.program_turn_instruction_invoke import (
        ProgramTurnInstructionInvoke,
    )


class ProgramTurnInstruction(ORMModel):
    """
    Canonical per-turn executed instruction receipt.
    Contract:
    - Anchors one executed `ProgramImplInstruction` under one `ProgramTurn`.
    - Owns decision receipts as child membership (`decisions`).
    """

    # Relationships
    program_instruction: ProgramImplInstruction | None = Field(default=None, exclude=True)
    bind_receipt: ProgramTurnInstructionBind | None = Field(default=None, exclude=True)
    invoke_receipt: ProgramTurnInstructionInvoke | None = Field(default=None, exclude=True)
    action_receipt: ProgramTurnInstructionAction | None = Field(default=None, exclude=True)
    decisions: list[ProgramTurnInstructionDecision] = Field(default_factory=list, exclude=True)

    # Attributes
    sequence: int

    # Foreign Keys
    program_turn_id: UUID = Field(description="Foreign key for ProgramTurn.instructions")
    program_instruction_id: UUID = Field(description="Foreign key for ProgramTurnInstruction.program_instruction")
