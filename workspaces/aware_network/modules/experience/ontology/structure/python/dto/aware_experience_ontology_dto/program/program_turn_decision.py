from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.program.program_enums import (
    ProgramTurnDecisionReason,
    ProgramTurnTransition,
)


class ProgramTurnInstructionDecision(BaseModel):
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
