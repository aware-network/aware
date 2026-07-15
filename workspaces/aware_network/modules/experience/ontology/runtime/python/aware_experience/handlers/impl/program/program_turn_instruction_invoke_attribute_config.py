from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_turn_instruction_invoke_attribute_config import (
    ProgramTurnInstructionInvokeAttributeConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)

# Environment Ontology
from aware_experience_ontology.program.program_turn_instruction_invoke import (
    ProgramTurnInstructionInvoke,
)
from aware_experience_ontology.stable_ids import (
    stable_program_turn_instruction_invoke_attribute_config_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_turn_instruction_invoke(
    program_turn_instruction_invoke_id: UUID, program_impl_instruction_invoke_attribute_config_id: UUID
) -> ProgramTurnInstructionInvokeAttributeConfig:
    """
    Create deterministic ProgramTurnInstructionInvokeAttributeConfig under ProgramTurnInstructionInvoke.
    """

    # --- AWARE: LOGIC START build_via_program_turn_instruction_invoke
    receipt_id = stable_program_turn_instruction_invoke_attribute_config_id(
        program_turn_instruction_invoke_id=program_turn_instruction_invoke_id,
        program_impl_instruction_invoke_attribute_config_id=program_impl_instruction_invoke_attribute_config_id,
    )

    session = current_handler_session()
    invoke_receipt = session.imap_get(
        ProgramTurnInstructionInvoke,
        program_turn_instruction_invoke_id,
    )
    if invoke_receipt is None:
        raise RuntimeError(
            "ProgramTurnInstructionInvokeAttributeConfig.build_via_program_turn_instruction_invoke requires "
            + "ProgramTurnInstructionInvoke in session: "
            + f"{program_turn_instruction_invoke_id}"
        )

    invoke_attribute_config = session.imap_get(
        ProgramImplInstructionInvokeAttributeConfig,
        program_impl_instruction_invoke_attribute_config_id,
    )
    if invoke_attribute_config is None:
        raise RuntimeError(
            "ProgramTurnInstructionInvokeAttributeConfig.build_via_program_turn_instruction_invoke requires "
            + "ProgramImplInstructionInvokeAttributeConfig in session: "
            + f"{program_impl_instruction_invoke_attribute_config_id}"
        )

    existing = session.imap_get(ProgramTurnInstructionInvokeAttributeConfig, receipt_id)
    if existing is not None:
        if (
            existing.program_turn_instruction_invoke_id != program_turn_instruction_invoke_id
            or existing.program_impl_instruction_invoke_attribute_config_id
            != program_impl_instruction_invoke_attribute_config_id
        ):
            raise RuntimeError(
                "ProgramTurnInstructionInvokeAttributeConfig.build_via_program_turn_instruction_invoke "
                + "payload mismatch for existing receipt: "
                + f"program_turn_instruction_invoke_attribute_config_id={receipt_id}"
            )
        if existing.program_impl_instruction_invoke_attribute_config is None and invoke_attribute_config is not None:
            existing.program_impl_instruction_invoke_attribute_config = invoke_attribute_config
        return existing

    return ProgramTurnInstructionInvokeAttributeConfig(
        id=receipt_id,
        program_turn_instruction_invoke_id=program_turn_instruction_invoke_id,
        program_impl_instruction_invoke_attribute_config_id=program_impl_instruction_invoke_attribute_config_id,
        program_impl_instruction_invoke_attribute_config=invoke_attribute_config,
    )
    # --- AWARE: LOGIC END build_via_program_turn_instruction_invoke
