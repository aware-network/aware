from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_bind import ProgramImplInstructionBind

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_program_impl_instruction_bind_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_impl_instruction(
    program_impl_instruction_id: UUID, program_config_port_id: UUID, view_key: str, is_active: bool = True
) -> ProgramImplInstructionBind:
    """
    Create deterministic bind payload for one ProgramImplInstruction.

    Contract:
    - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_program_impl_instruction
    normalized_view_key = (view_key or "").strip()
    if not normalized_view_key:
        raise RuntimeError("ProgramImplInstructionBind.build requires non-empty view_key")

    instruction_bind_id = stable_program_impl_instruction_bind_id(
        program_impl_instruction_id=program_impl_instruction_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ProgramImplInstructionBind, instruction_bind_id)
    if existing is not None:
        if (
            existing.program_config_port_id != program_config_port_id
            or (existing.view_key or "").strip() != normalized_view_key
            or existing.is_active != is_active
        ):
            raise RuntimeError(
                "ProgramImplInstructionBind.build payload mismatch for existing instruction bind: "
                f"instruction_bind_id={instruction_bind_id}"
            )
        return existing

    return ProgramImplInstructionBind(
        id=instruction_bind_id,
        program_config_port_id=program_config_port_id,
        view_key=normalized_view_key,
        is_active=is_active,
    )
    # --- AWARE: LOGIC END build_via_program_impl_instruction
