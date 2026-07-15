from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_expect import ProgramImplInstructionExpect

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_program_impl_instruction_expect_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_impl_instruction(
    program_impl_instruction_id: UUID, event_config_id: UUID, required: bool = True
) -> ProgramImplInstructionExpect:
    """
    Create deterministic expect payload for one ProgramImplInstruction.

    Contract:
    - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_program_impl_instruction

    instruction_expect_id = stable_program_impl_instruction_expect_id(
        program_impl_instruction_id=program_impl_instruction_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ProgramImplInstructionExpect, instruction_expect_id)
    if existing is not None:
        if existing.event_config_id != event_config_id or existing.required != required:
            raise RuntimeError(
                "ProgramImplInstructionExpect.build payload mismatch for existing instruction expect: "
                f"instruction_expect_id={instruction_expect_id}"
            )
        return existing

    return ProgramImplInstructionExpect(
        id=instruction_expect_id,
        event_config_id=event_config_id,
        required=required,
    )
    # --- AWARE: LOGIC END build_via_program_impl_instruction
