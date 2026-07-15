from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_let import ProgramImplInstructionLet

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_program_impl_instruction_let_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_impl_instruction(
    program_impl_instruction_id: UUID, name: str, value_expr: JsonObject
) -> ProgramImplInstructionLet:
    """
    Create deterministic let payload for one ProgramImplInstruction.

    Contract:
    - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_program_impl_instruction
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProgramImplInstructionLet.build requires non-empty name")

    instruction_let_id = stable_program_impl_instruction_let_id(
        program_impl_instruction_id=program_impl_instruction_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ProgramImplInstructionLet, instruction_let_id)
    if existing is not None:
        if (existing.name or "").strip() != normalized_name or existing.value_expr != value_expr:
            raise RuntimeError(
                "ProgramImplInstructionLet.build payload mismatch for existing instruction let: "
                f"instruction_let_id={instruction_let_id}"
            )
        return existing

    return ProgramImplInstructionLet(
        id=instruction_let_id,
        name=normalized_name,
        value_expr=value_expr,
    )
    # --- AWARE: LOGIC END build_via_program_impl_instruction
