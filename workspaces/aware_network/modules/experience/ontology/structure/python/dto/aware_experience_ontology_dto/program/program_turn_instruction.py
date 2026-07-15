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
    from aware_experience_ontology_dto.program.program_turn_decision import ProgramTurnInstructionDecision
    from aware_experience_ontology_dto.program.program_turn_instruction_action import ProgramTurnInstructionAction
    from aware_experience_ontology_dto.program.program_turn_instruction_bind import ProgramTurnInstructionBind
    from aware_experience_ontology_dto.program.program_turn_instruction_invoke import ProgramTurnInstructionInvoke


class ProgramTurnInstruction(BaseModel):
    """
    Canonical per-turn executed instruction receipt.
    Contract:
    - Anchors one executed `ProgramImplInstruction` under one `ProgramTurn`.
    - Owns decision receipts as child membership (`decisions`).
    """

    # Relationships
    program_instruction: ProgramImplInstruction | None = Field(default=None)
    bind_receipt: ProgramTurnInstructionBind | None = Field(default=None)
    invoke_receipt: ProgramTurnInstructionInvoke | None = Field(default=None)
    action_receipt: ProgramTurnInstructionAction | None = Field(default=None)
    decisions: list[ProgramTurnInstructionDecision] = Field(default_factory=list)

    # Attributes
    sequence: int
