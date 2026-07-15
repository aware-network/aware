from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_turn import ProgramTurn
from aware_experience_ontology.program.program_turn_instruction import ProgramTurnInstruction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Environment Ontology
from aware_experience_ontology.stable_ids import stable_program_turn_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_instruction(
    program_turn: ProgramTurn, program_instruction_id: UUID, sequence: int
) -> ProgramTurnInstruction:
    """
    Create one instruction execution receipt under this ProgramTurn.

    Contract:
    - Mutates only ProgramTurn membership (`instructions`).
    - Instruction linkage is typed via `aware_experience.program.impl.ProgramImplInstruction`.
    """

    # --- AWARE: LOGIC START create_instruction
    program_turn_id = program_turn.id
    if program_turn_id is None:
        raise RuntimeError("ProgramTurn.create_instruction requires ProgramTurn.id")

    instruction = await ProgramTurnInstruction.build_via_program_turn(
        program_turn_id=program_turn_id,
        program_instruction_id=program_instruction_id,
        sequence=sequence,
    )

    if not any(existing.id == instruction.id for existing in program_turn.instructions):
        program_turn.instructions.append(instruction)

    return instruction
    # --- AWARE: LOGIC END create_instruction


async def build_via_program(program_id: UUID, turn_id: UUID, order: int = 0) -> ProgramTurn:
    """
    Create a deterministic ProgramTurn.
    """

    # --- AWARE: LOGIC START build_via_program
    assoc_id = stable_program_turn_id(program_id=program_id, turn_id=turn_id)
    session = current_handler_session()
    existing = session.imap_get(ProgramTurn, assoc_id)
    if existing is not None:
        if existing.program_id != program_id or existing.turn_id != turn_id or existing.order != int(order):
            raise RuntimeError(
                "ProgramTurn.build_via_program payload mismatch for existing association: "
                f"program_turn_id={assoc_id}"
            )
        return existing

    return ProgramTurn(
        id=assoc_id,
        program_id=program_id,
        turn_id=turn_id,
        order=int(order),
    )
    # --- AWARE: LOGIC END build_via_program
