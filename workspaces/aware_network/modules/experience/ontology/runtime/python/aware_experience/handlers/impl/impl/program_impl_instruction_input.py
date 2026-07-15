from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_input import ProgramImplInstructionInput

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_program_impl_instruction_input_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_impl_instruction(
    program_impl_instruction_id: UUID, program_config_input_config_id: UUID
) -> ProgramImplInstructionInput:
    """
    Create a deterministic ProgramImplInstructionInput.
    """

    # --- AWARE: LOGIC START build_via_program_impl_instruction
    instruction_input_id = stable_program_impl_instruction_input_id(
        program_impl_instruction_id=program_impl_instruction_id,
        program_config_input_config_id=program_config_input_config_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ProgramImplInstructionInput, instruction_input_id)
    if existing is not None:
        if existing.program_config_input_config_id != program_config_input_config_id:
            raise RuntimeError(
                "ProgramImplInstructionInput.build_via_program_impl_instruction payload mismatch for existing instruction input: "
                f"instruction_input_id={instruction_input_id}"
            )
        return existing

    return ProgramImplInstructionInput(
        id=instruction_input_id,
        program_config_input_config_id=program_config_input_config_id,
    )
    # --- AWARE: LOGIC END build_via_program_impl_instruction
