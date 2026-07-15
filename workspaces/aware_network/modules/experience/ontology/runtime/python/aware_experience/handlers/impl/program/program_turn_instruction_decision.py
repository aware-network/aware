from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_experience_ontology.program.program_enums import (
    ProgramTurnDecisionReason,
    ProgramTurnTransition,
)
from aware_experience_ontology.program.program_turn_decision import ProgramTurnInstructionDecision

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from uuid import NAMESPACE_URL, uuid5

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

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
    if step_index < 0:
        raise RuntimeError("ProgramTurnInstructionDecision.build_via_program_turn_instruction requires step_index >= 0")
    if total_steps < 0:
        raise RuntimeError(
            "ProgramTurnInstructionDecision.build_via_program_turn_instruction requires total_steps >= 0"
        )
    if invokes_in_turn < 0:
        raise RuntimeError(
            "ProgramTurnInstructionDecision.build_via_program_turn_instruction requires invokes_in_turn >= 0"
        )
    if elapsed_ms_in_turn < 0:
        raise RuntimeError(
            "ProgramTurnInstructionDecision.build_via_program_turn_instruction requires elapsed_ms_in_turn >= 0"
        )

    decision_id = uuid5(
        NAMESPACE_URL,
        "aware:program_turn_instruction_decision:" f"{program_turn_instruction_id}:{int(step_index)}",
    )

    session = current_handler_session()
    existing = session.imap_get(ProgramTurnInstructionDecision, decision_id)
    if existing is not None:
        if (
            existing.program_turn_instruction_id != program_turn_instruction_id
            or existing.transition != transition
            or existing.reason != reason
            or existing.step_index != int(step_index)
            or existing.total_steps != int(total_steps)
            or existing.invokes_in_turn != int(invokes_in_turn)
            or existing.elapsed_ms_in_turn != int(elapsed_ms_in_turn)
            or bool(existing.awaiting_external_signal) != bool(awaiting_external_signal)
            or bool(existing.instruction_failed) != bool(instruction_failed)
        ):
            raise RuntimeError(
                "ProgramTurnInstructionDecision.build_via_program_turn_instruction payload mismatch "
                f"for existing decision: program_turn_instruction_decision_id={decision_id}"
            )
        return existing

    return ProgramTurnInstructionDecision(
        id=decision_id,
        program_turn_instruction_id=program_turn_instruction_id,
        transition=transition,
        reason=reason,
        step_index=int(step_index),
        total_steps=int(total_steps),
        invokes_in_turn=int(invokes_in_turn),
        elapsed_ms_in_turn=int(elapsed_ms_in_turn),
        awaiting_external_signal=bool(awaiting_external_signal),
        instruction_failed=bool(instruction_failed),
    )
    # --- AWARE: LOGIC END build_via_program_turn_instruction
