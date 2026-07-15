from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Experience Ontology Orm Models
from aware_experience_ontology_orm_models.program.program_enums import (
    ProgramTurnDecisionReason,
    ProgramTurnTransition,
)

# Orm
from aware_orm.models.orm_model import ORMModel


class ProgramTurnInstructionDecision(ORMModel):
    """
    Canonical per-instruction checkpoint decision receipt.
    Contract:
    - Captures runtime transition semantics as commit-backed facts.
    - Linked through `ProgramTurnInstruction` membership.
    """

    # Attributes
    transition: ProgramTurnTransition
    reason: ProgramTurnDecisionReason
    step_index: int
    total_steps: int
    invokes_in_turn: int = Field(default=0)
    elapsed_ms_in_turn: int = Field(default=0)
    awaiting_external_signal: bool = Field(default=False)
    instruction_failed: bool = Field(default=False)

    # Foreign Keys
    program_turn_instruction_id: UUID = Field(description="Foreign key for ProgramTurnInstruction.decisions")
