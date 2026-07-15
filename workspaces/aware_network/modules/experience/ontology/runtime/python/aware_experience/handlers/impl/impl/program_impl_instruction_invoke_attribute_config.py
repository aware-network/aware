from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# Experience Runtime
from aware_experience.stable_ids import (
    stable_program_impl_instruction_invoke_attribute_config_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_impl_instruction_invoke(
    program_impl_instruction_invoke_id: UUID,
    attribute_config_id: UUID,
    value_expr: JsonObject,
    position: int | None = None,
) -> ProgramImplInstructionInvokeAttributeConfig:
    """
    Create deterministic invoke argument association for one ProgramImplInstructionInvoke.
    """

    # --- AWARE: LOGIC START build_via_program_impl_instruction_invoke
    if position is not None and position < 0:
        raise RuntimeError(
            "ProgramImplInstructionInvokeAttributeConfig.build_via_program_impl_instruction_invoke requires position >= 0"
        )

    assoc_id = stable_program_impl_instruction_invoke_attribute_config_id(
        program_impl_instruction_invoke_id=program_impl_instruction_invoke_id,
        attribute_config_id=attribute_config_id,
    )

    session = current_handler_session()
    attribute_config = session.imap_get(AttributeConfig, attribute_config_id)
    if attribute_config is None:
        raise RuntimeError(
            "ProgramImplInstructionInvokeAttributeConfig.build requires AttributeConfig to exist. "
            "Create it first via AttributeConfig.create(...)."
        )

    existing = session.imap_get(ProgramImplInstructionInvokeAttributeConfig, assoc_id)
    if existing is not None:
        if (
            existing.program_impl_instruction_invoke_id != program_impl_instruction_invoke_id
            or existing.attribute_config_id != attribute_config_id
            or existing.value_expr != value_expr
            or existing.position != position
        ):
            raise RuntimeError(
                "ProgramImplInstructionInvokeAttributeConfig.build_via_program_impl_instruction_invoke payload mismatch for existing association: "
                f"association_id={assoc_id}"
            )
        return existing

    return ProgramImplInstructionInvokeAttributeConfig(
        id=assoc_id,
        program_impl_instruction_invoke_id=program_impl_instruction_invoke_id,
        attribute_config_id=attribute_config_id,
        value_expr=value_expr,
        position=position,
    )
    # --- AWARE: LOGIC END build_via_program_impl_instruction_invoke
