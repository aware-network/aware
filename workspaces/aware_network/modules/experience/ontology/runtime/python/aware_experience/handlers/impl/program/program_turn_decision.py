from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_enums import (
    ProgramTurnDecisionReason,
    ProgramTurnTransition,
)
from aware_experience_ontology.program.program_turn_decision import ProgramTurnInstructionDecision

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_program_turn_instruction(
    program_turn_instruction_id: UUID,
    transition: ProgramTurnTransition,
    reason: ProgramTurnDecisionReason,
    step_index: int,
    total_steps: int,
    invokes_in_turn: int = 0,
    elapsed_ms_in_turn: int = 0,
    awaiting_external_signal: bool = False,
    instruction_failed: bool = False,
) -> ProgramTurnInstructionDecision:
    """
    Construct a deterministic ProgramTurnInstructionDecision.

    Contract:
    - Constructor is idempotent for repeated calls with the same payload under one
    ProgramTurnInstruction.
    """

    # --- AWARE: LOGIC START build_via_program_turn_instruction
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_program_turn_instruction
